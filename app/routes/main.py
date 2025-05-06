import os
import datetime
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from app import db
from app.models import Projeto, Log
from werkzeug.utils import secure_filename
from app.utils import extract_pdfs, rename_paths

main = Blueprint('main', __name__)

# Adicionar a data atual ao contexto de todos os templates
@main.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

@main.route('/')
def index():
    """Página inicial - lista de projetos"""
    projetos = Projeto.query.order_by(Projeto.data_criacao.desc()).all()
    return render_template('index.html', projetos=projetos)

@main.route('/projeto/novo', methods=['GET', 'POST'])
def novo_projeto():
    """Criar novo projeto"""
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        
        if not nome:
            flash('Nome do projeto é obrigatório', 'danger')
            return render_template('novo_projeto.html')
        
        # Criar diretório do projeto
        nome_diretorio = nome.replace(' ', '_').lower()
        caminho_diretorio = os.path.join(current_app.config['PROJETOS_DIR'], nome_diretorio)
        
        # Verificar se já existe
        if os.path.exists(caminho_diretorio):
            flash(f'Já existe um projeto com o nome "{nome}"', 'danger')
            return render_template('novo_projeto.html')
        
        # Criar diretórios
        os.makedirs(caminho_diretorio)
        os.makedirs(os.path.join(caminho_diretorio, 'processos'))
        os.makedirs(os.path.join(caminho_diretorio, 'docs'))
        
        # Criar arquivo Excel vazio
        caminho_excel = os.path.join(caminho_diretorio, 'Índice Documentos Matrículas_Atualizado.xlsx')
        
        # Criar projeto no banco de dados
        projeto = Projeto(
            nome=nome,
            descricao=descricao,
            caminho_diretorio=caminho_diretorio,
            caminho_excel=caminho_excel
        )
        
        db.session.add(projeto)
        
        # Adicionar log
        log = Log(
            projeto=projeto,
            tipo='info',
            mensagem=f'Projeto "{nome}" criado com sucesso'
        )
        
        db.session.add(log)
        db.session.commit()
        
        flash(f'Projeto "{nome}" criado com sucesso', 'success')
        return redirect(url_for('main.projeto', projeto_id=projeto.id))
    
    return render_template('novo_projeto.html')

@main.route('/projeto/<int:projeto_id>')
def projeto(projeto_id):
    """Página de detalhes do projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Listar arquivos na pasta de processos
    arquivos_origem = []
    processos_dir = os.path.join(projeto.caminho_diretorio, 'processos')
    
    if os.path.exists(processos_dir):
        for filename in os.listdir(processos_dir):
            file_path = os.path.join(processos_dir, filename)
            if os.path.isfile(file_path):
                stats = os.stat(file_path)
                arquivos_origem.append({
                    'nome': filename,
                    'caminho': os.path.join('processos', filename),
                    'tamanho': stats.st_size,
                    'data_upload': datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
                })
    
    # Listar arquivos na pasta de docs
    arquivos_extraidos = []
    docs_dir = os.path.join(projeto.caminho_diretorio, 'docs')
    
    if os.path.exists(docs_dir):
        for root, dirs, files in os.walk(docs_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, docs_dir)
                stats = os.stat(file_path)
                arquivos_extraidos.append({
                    'nome': filename,
                    'caminho': os.path.join('docs', rel_path),
                    'tamanho': stats.st_size,
                    'data_extracao': datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
                })
    
    # Carregar matrículas do arquivo Excel
    matriculas = []
    try:
        if os.path.exists(projeto.caminho_excel):
            df = pd.read_excel(projeto.caminho_excel)
            # Converter DataFrame para lista de dicionários
            matriculas = df.to_dict('records')
    except Exception as e:
        flash(f"Erro ao carregar matrículas: {str(e)}", "warning")
    
    return render_template('projeto.html',
                          projeto=projeto,
                          arquivos_origem=arquivos_origem,
                          arquivos_extraidos=arquivos_extraidos,
                          matriculas=matriculas)

@main.route('/projeto/<int:projeto_id>/upload', methods=['POST'])
def upload_arquivo(projeto_id):
    """Upload de arquivo para o projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo selecionado', 'danger')
        return redirect(url_for('main.projeto', projeto_id=projeto_id))
    
    arquivo = request.files['arquivo']
    
    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado', 'danger')
        return redirect(url_for('main.projeto', projeto_id=projeto_id))
    
    if arquivo:
        filename = secure_filename(arquivo.filename)
        caminho_destino = os.path.join(projeto.caminho_processos, filename)
        arquivo.save(caminho_destino)
        
        # Adicionar log
        log = Log(
            projeto=projeto,
            tipo='info',
            mensagem=f'Arquivo "{filename}" enviado com sucesso'
        )
        
        db.session.add(log)
        db.session.commit()
        
        flash(f'Arquivo "{filename}" enviado com sucesso', 'success')
    
    return redirect(url_for('main.projeto', projeto_id=projeto_id))

@main.route('/projeto/<int:projeto_id>/processar')
def processar_projeto(projeto_id):
    """Processar arquivos do projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Obter parâmetros
    renomear = request.args.get('renomear', 'true') == 'true'
    extrair = request.args.get('extrair', 'true') == 'true'
    
    # Verificar se o arquivo Excel existe
    if not os.path.exists(projeto.caminho_excel):
        flash(f"Erro: Arquivo Excel não encontrado em {projeto.caminho_excel}", "danger")
        return redirect(url_for('main.projeto', projeto_id=projeto_id))
    
    # Função de callback para registrar logs
    def log_callback(mensagem, tipo='info'):
        log = Log(
            projeto=projeto,
            tipo=tipo,
            mensagem=mensagem
        )
        db.session.add(log)
        db.session.commit()
    
    # Processar renomeação de caminhos
    if renomear:
        try:
            # Caminho para o diretório docs do projeto
            docs_dir = os.path.join(projeto.caminho_diretorio, 'docs')
            
            # Garantir que o diretório docs existe
            if not os.path.exists(docs_dir):
                os.makedirs(docs_dir)
            
            # Renomear caminhos no Excel
            success = rename_paths.rename_paths_in_excel(
                projeto.caminho_excel,
                projeto.caminho_excel,
                docs_dir,
                log_callback
            )
            
            if success:
                flash("Caminhos renomeados com sucesso no arquivo Excel", "success")
            else:
                flash("Erro ao renomear caminhos no arquivo Excel", "danger")
                return redirect(url_for('main.projeto', projeto_id=projeto_id))
        
        except Exception as e:
            flash(f"Erro ao renomear caminhos: {str(e)}", "danger")
            log_callback(f"Erro ao renomear caminhos: {str(e)}", 'error')
            return redirect(url_for('main.projeto', projeto_id=projeto_id))
    
    # Processar extração de PDFs
    if extrair:
        try:
            # Extrair PDFs
            stats = extract_pdfs.extract_from_excel(
                projeto.caminho_excel,
                projeto.caminho_diretorio,
                log_callback
            )
            
            if stats['success'] > 0:
                flash(f"Extração concluída: {stats['success']} documentos extraídos com sucesso, {stats['error']} erros", "success")
            else:
                flash(f"Nenhum documento extraído com sucesso. {stats['error']} erros encontrados.", "warning")
        
        except Exception as e:
            flash(f"Erro ao extrair PDFs: {str(e)}", "danger")
            log_callback(f"Erro ao extrair PDFs: {str(e)}", 'error')
    
    return redirect(url_for('main.projeto', projeto_id=projeto_id, _anchor='documentos'))

@main.route('/projeto/<int:projeto_id>/editar_matricula/<int:index>', methods=['GET', 'POST'])
def editar_matricula(projeto_id, index):
    """Editar uma matrícula existente"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Carregar o arquivo Excel
    try:
        df = pd.read_excel(projeto.caminho_excel)
        if index >= len(df):
            flash("Matrícula não encontrada", "danger")
            return redirect(url_for('main.projeto', projeto_id=projeto_id))
        
        if request.method == 'POST':
            # Obter dados do formulário
            matricula = request.form.get('matricula')
            nome_documento = request.form.get('nome_documento')
            data = request.form.get('data')
            origem = request.form.get('origem')
            volume = request.form.get('volume')
            paginas = request.form.get('paginas')
            obs = request.form.get('obs')
            
            # Verificar campos obrigatórios
            if not all([matricula, nome_documento, origem, volume, paginas]):
                flash("Todos os campos obrigatórios devem ser preenchidos", "danger")
                return render_template('editar_matricula.html', projeto=projeto, matricula=df.iloc[index])
            
            # Atualizar dados
            df.at[index, 'Matrícula'] = matricula
            df.at[index, 'Nome do Documento'] = nome_documento
            df.at[index, 'Data'] = data if data else None
            df.at[index, 'Origem'] = origem
            df.at[index, 'Volume'] = volume
            df.at[index, 'Páginas'] = paginas
            df.at[index, 'Obs'] = obs if obs else None
            
            # Salvar o arquivo Excel
            df.to_excel(projeto.caminho_excel, index=False)
            
            # Registrar log
            log = Log(
                projeto=projeto,
                tipo='info',
                mensagem=f'Matrícula "{matricula}" atualizada com sucesso'
            )
            db.session.add(log)
            db.session.commit()
            
            flash(f'Matrícula "{matricula}" atualizada com sucesso', 'success')
            return redirect(url_for('main.projeto', projeto_id=projeto_id, _anchor='matriculas'))
        
        # Método GET - exibir formulário de edição
        # Listar arquivos na pasta de processos para o dropdown de origem
        arquivos_origem = []
        processos_dir = os.path.join(projeto.caminho_diretorio, 'processos')
        
        if os.path.exists(processos_dir):
            for filename in os.listdir(processos_dir):
                file_path = os.path.join(processos_dir, filename)
                if os.path.isfile(file_path):
                    stats = os.stat(file_path)
                    arquivos_origem.append({
                        'nome': filename,
                        'caminho': os.path.join('processos', filename),
                        'tamanho': stats.st_size,
                        'data_upload': datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
                    })
        
        return render_template('editar_matricula.html',
                              projeto=projeto,
                              matricula=df.iloc[index].to_dict(),
                              arquivos_origem=arquivos_origem)
    
    except Exception as e:
        flash(f"Erro ao editar matrícula: {str(e)}", "danger")
        return redirect(url_for('main.projeto', projeto_id=projeto_id))

@main.route('/projeto/<int:projeto_id>/excluir_matricula/<int:index>')
def excluir_matricula(projeto_id, index):
    """Excluir uma matrícula existente"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    try:
        # Carregar o arquivo Excel
        df = pd.read_excel(projeto.caminho_excel)
        
        if index >= len(df):
            flash("Matrícula não encontrada", "danger")
            return redirect(url_for('main.projeto', projeto_id=projeto_id))
        
        # Obter informações da matrícula antes de excluí-la
        matricula_info = df.iloc[index]['Matrícula']
        
        # Excluir a linha
        df = df.drop(index)
        
        # Resetar os índices
        df = df.reset_index(drop=True)
        
        # Salvar o arquivo Excel
        df.to_excel(projeto.caminho_excel, index=False)
        
        # Registrar log
        log = Log(
            projeto=projeto,
            tipo='info',
            mensagem=f'Matrícula "{matricula_info}" excluída com sucesso'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Matrícula "{matricula_info}" excluída com sucesso', 'success')
    
    except Exception as e:
        flash(f"Erro ao excluir matrícula: {str(e)}", "danger")
    
    return redirect(url_for('main.projeto', projeto_id=projeto_id, _anchor='matriculas'))

@main.route('/projeto/<int:projeto_id>/adicionar_matricula', methods=['POST'])
def adicionar_matricula(projeto_id):
    """Adicionar uma nova matrícula ao projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Obter dados do formulário
    matricula = request.form.get('matricula')
    nome_documento = request.form.get('nome_documento')
    data = request.form.get('data')
    origem = request.form.get('origem')
    volume = request.form.get('volume')
    paginas = request.form.get('paginas')
    obs = request.form.get('obs')
    
    # Verificar campos obrigatórios
    if not all([matricula, nome_documento, origem, volume, paginas]):
        flash("Todos os campos obrigatórios devem ser preenchidos", "danger")
        return redirect(url_for('main.projeto', projeto_id=projeto_id))
    
    try:
        # Carregar o arquivo Excel existente ou criar um novo
        excel_path = projeto.caminho_excel
        try:
            df = pd.read_excel(excel_path)
        except FileNotFoundError:
            # Criar DataFrame vazio com as colunas necessárias
            df = pd.DataFrame(columns=[
                'Matrícula', 'Nome do Documento', 'Data', 'Origem',
                'Volume', 'Páginas', 'Obs', 'Arquivo Extraído', 'Documento Compartilhado'
            ])
        
        # Adicionar nova linha
        nova_linha = {
            'Matrícula': matricula,
            'Nome do Documento': nome_documento,
            'Data': data if data else None,
            'Origem': origem,
            'Volume': volume,
            'Páginas': paginas,
            'Obs': obs if obs else None,
            'Arquivo Extraído': '',
            'Documento Compartilhado': 'Não'
        }
        
        df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        
        # Salvar o arquivo Excel
        df.to_excel(excel_path, index=False)
        
        # Registrar log
        log = Log(
            projeto=projeto,
            tipo='info',
            mensagem=f'Matrícula "{matricula}" adicionada com sucesso'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Matrícula "{matricula}" adicionada com sucesso', 'success')
    
    except Exception as e:
        flash(f"Erro ao adicionar matrícula: {str(e)}", "danger")
        # Registrar log de erro
        log = Log(
            projeto=projeto,
            tipo='error',
            mensagem=f'Erro ao adicionar matrícula: {str(e)}'
        )
        db.session.add(log)
        db.session.commit()
    
    return redirect(url_for('main.projeto', projeto_id=projeto_id, _anchor='matriculas'))

@main.route('/projeto/<int:projeto_id>/listar_arquivos/<path:subpath>')
def listar_arquivos(projeto_id, subpath):
    """Listar arquivos em um diretório do projeto (para AJAX)"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Determinar o caminho completo
    if subpath == 'processos':
        path = os.path.join(projeto.caminho_diretorio, 'processos')
    elif subpath == 'docs':
        path = os.path.join(projeto.caminho_diretorio, 'docs')
    else:
        return jsonify({'error': 'Caminho inválido'}), 400
    
    # Verificar se o diretório existe
    if not os.path.exists(path):
        return jsonify({'files': [], 'message': 'Diretório não encontrado'})
    
    # Listar arquivos
    files = []
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):
            stats = os.stat(file_path)
            files.append({
                'name': filename,
                'path': os.path.join(subpath, filename),
                'size': stats.st_size,
                'modified': datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
            })
    
    return jsonify({'files': files})