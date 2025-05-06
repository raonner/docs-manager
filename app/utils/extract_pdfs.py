import os
import re
from PyPDF2 import PdfReader, PdfWriter

class PDFExtractor:
    def __init__(self, projeto_path=None, excel_path=None, callback=None):
        """
        Inicializa o extrator de PDFs
        
        Args:
            projeto_path (str): Caminho para o diretório do projeto
            excel_path (str): Caminho para o arquivo Excel
            callback (function): Função de callback para reportar progresso
        """
        self.projeto_path = projeto_path
        self.excel_path = excel_path
        self.callback = callback or (lambda msg, tipo='info': None)
        self.processos_dir = os.path.join(projeto_path, 'processos') if projeto_path else None
    
    def parse_page_range(self, page_str):
        """
        Extrai intervalo de páginas de uma string
        
        Args:
            page_str (str): String com o intervalo de páginas (ex: "1-5" ou "3")
            
        Returns:
            tuple: (página inicial, página final) ou (None, None) se inválido
        """
        page_str = str(page_str).strip()
        match = re.match(r"(\d+)\s*-\s*(\d+)", page_str)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            if start <= end:
                return start, end
        match_single = re.match(r"(\d+)", page_str)
        if match_single:
            page = int(match_single.group(1))
            return page, page
        return None, None
    
    def get_input_pdf_name(self, origem, volume):
        """
        Formata o nome do arquivo de origem
        
        Args:
            origem (str): Nome da origem
            volume (str): Número do volume
            
        Returns:
            str: Nome do arquivo formatado
        """
        origem_clean = origem
        return f"{origem_clean}_{volume}.pdf"
    
    def extract_pages(self, data_row):
        """
        Extrai páginas de um PDF com base nas informações da linha
        
        Args:
            data_row (dict): Dicionário com os dados da linha
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        origem = str(data_row["Origem"]).strip()
        volume = str(data_row["Volume"]).strip()
        pages = data_row["Páginas"]
        output_path = data_row["Arquivo Extraído"]
        matricula = data_row["Matrícula"]
        
        # Determinar arquivo de origem
        input_pdf_name = self.get_input_pdf_name(origem, volume)
        input_pdf = os.path.join(self.processos_dir, input_pdf_name)
        
        # Verificar se o arquivo de origem existe
        if not os.path.exists(input_pdf):
            msg = f"Erro: Arquivo de origem '{input_pdf}' não encontrado para Matrícula {matricula}."
            self.callback(msg, 'error')
            return False, msg
        
        # Extrair intervalo de páginas
        start_page, end_page = self.parse_page_range(pages)
        if start_page is None or end_page is None:
            msg = f"Erro: Intervalo de páginas inválido '{pages}' para Matrícula {matricula}."
            self.callback(msg, 'error')
            return False, msg
        
        # Verificar se o intervalo é válido
        if start_page < 1 or end_page < start_page:
            msg = f"Erro: Intervalo de páginas inválido ({start_page}-{end_page}) para Matrícula {matricula}."
            self.callback(msg, 'error')
            return False, msg
        
        # Aviso para intervalos longos
        num_pages = end_page - start_page + 1
        if num_pages > 10:
            self.callback(f"Aviso: Intervalo longo ({start_page}-{end_page}, {num_pages} páginas) para Matrícula {matricula}. Verificando...", 'warning')
        
        try:
            # Abrir PDF de origem
            reader = PdfReader(input_pdf)
            total_pages = len(reader.pages)
            
            # Verificar se o intervalo está dentro do total de páginas
            if end_page > total_pages:
                msg = f"Erro: Intervalo ({start_page}-{end_page}) excede o total de páginas ({total_pages}) em '{input_pdf}' para Matrícula {matricula}."
                self.callback(msg, 'error')
                return False, msg
            
            # Criar diretório de saída se não existir
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.callback(f"Diretório criado: {output_dir}", 'info')
            
            # Criar PDF de saída
            writer = PdfWriter()
            for page_num in range(start_page - 1, end_page):
                writer.add_page(reader.pages[page_num])
            
            # Salvar PDF extraído
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            
            msg = f"PDF extraído salvo em: {output_path} ({num_pages} páginas)"
            self.callback(msg, 'info')
            return True, msg
        
        except Exception as e:
            msg = f"Erro ao extrair páginas {start_page}-{end_page} de '{input_pdf}' para Matrícula {matricula}: {e}"
            self.callback(msg, 'error')
            return False, msg
    
    def process_dataframe(self, df):
        """
        Processa um DataFrame pandas com as informações das matrículas
        
        Args:
            df (pandas.DataFrame): DataFrame com os dados
            
        Returns:
            dict: Estatísticas do processamento
        """
        total_rows = len(df)
        success_count = 0
        error_count = 0
        
        self.callback(f"Iniciando extração de {total_rows} documentos...", 'info')
        
        # Criar diretórios para arquivos extraídos
        for file_path in df["Arquivo Extraído"]:
            output_dir = os.path.dirname(file_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.callback(f"Diretório criado: {output_dir}", 'info')
        
        # Processar cada linha
        for index, row in df.iterrows():
            self.callback(f"Processando item {index+1}/{total_rows}: Matrícula {row['Matrícula']}", 'info')
            success, _ = self.extract_pages(row)
            if success:
                success_count += 1
            else:
                error_count += 1
        
        # Resumo final
        self.callback(f"Extração concluída. Total: {total_rows}, Sucesso: {success_count}, Erros: {error_count}", 'info')
        
        return {
            'total': total_rows,
            'success': success_count,
            'error': error_count
        }

def extract_from_excel(excel_path, projeto_path, callback=None):
    """
    Função auxiliar para extrair PDFs a partir de um arquivo Excel
    
    Args:
        excel_path (str): Caminho para o arquivo Excel
        projeto_path (str): Caminho para o diretório do projeto
        callback (function): Função de callback para reportar progresso
        
    Returns:
        dict: Estatísticas do processamento
    """
    try:
        import pandas as pd
        
        # Inicializar extrator
        extractor = PDFExtractor(projeto_path, excel_path, callback)
        
        # Carregar planilha
        df = pd.read_excel(excel_path)
        
        # Processar DataFrame
        return extractor.process_dataframe(df)
    
    except Exception as e:
        if callback:
            callback(f"Erro ao processar arquivo Excel: {e}", 'error')
        return {'total': 0, 'success': 0, 'error': 1, 'exception': str(e)}