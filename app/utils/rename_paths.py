import os
import re
from datetime import datetime
import unicodedata

class PathRenamer:
    def __init__(self, base_dir=None, callback=None):
        """
        Inicializa o renomeador de caminhos
        
        Args:
            base_dir (str): Diretório base para os documentos extraídos
            callback (function): Função de callback para reportar progresso
        """
        self.base_dir = base_dir
        self.callback = callback or (lambda msg, tipo='info': None)
        
        # Mapeamento de tipos de documentos
        self.doc_type_mapping = {
            "Escritura Venda": "EscrituraVenda",
            "Escritura de Venda e Compra": "EscrituraVenda",
            "Ecritura de Venda e Compra": "EscrituraVenda",
            "Título Definitivo": "TituloDefinitivo",
            "Título Definitvo": "TituloDefinitivo",
            "Certidão Inteiro Teor": "CertidaoInteiroTeor",
            "Inteiro Teor": "CertidaoInteiroTeor",
            "Certidão de Titulo": "CertidaoTitulo",
            "Certidão Iterpa": "CertidaoIterpa"
        }
    
    def remove_accents(self, text):
        """
        Remove acentos de um texto
        
        Args:
            text (str): Texto com acentos
            
        Returns:
            str: Texto sem acentos
        """
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    
    def extract_folder_components(self, matricula_str):
        """
        Extrai componentes da pasta a partir da string de matrícula
        
        Args:
            matricula_str (str): String da matrícula
            
        Returns:
            tuple: (nome da pasta, identificador da matrícula)
        """
        if not isinstance(matricula_str, str):
            matricula_str = str(matricula_str)
        matricula_str = matricula_str.replace("Ma.", "Mat.").strip()
        match = re.match(r"Livro ([\w-]+)[,\s]+[fF]ls\.?\s*(\d+)[,\s]+Mat\. (\d+)(?:\s*\(Restauração\))?", matricula_str)
        if match:
            livro = match.group(1).replace("-", "")
            folhas = match.group(2)
            matricula = match.group(3)
            return f"Livro{livro}_fls{folhas}_Mat{matricula}", f"Mat{matricula}"
        clean_name = re.sub(r"[^\w\d]", "_", matricula_str)
        return clean_name, clean_name
    
    def extract_mat_number(self, matricula_str):
        """
        Extrai número da matrícula
        
        Args:
            matricula_str (str): String da matrícula
            
        Returns:
            str: Número da matrícula formatado
        """
        if not isinstance(matricula_str, str):
            matricula_str = str(matricula_str)
        match = re.search(r"Mat\. (\d+)", matricula_str)
        return f"Mat.{match.group(1)}" if match else matricula_str
    
    def standardize_doc_type(self, doc_name):
        """
        Padroniza o tipo de documento
        
        Args:
            doc_name (str): Nome do documento
            
        Returns:
            str: Tipo de documento padronizado
        """
        import pandas as pd
        
        if pd.isna(doc_name) or not str(doc_name).strip():
            return "Desconhecido"
        doc_name = str(doc_name)
        doc_name_clean = self.remove_accents(doc_name).lower()
        for key, value in self.doc_type_mapping.items():
            if self.remove_accents(key).lower() in doc_name_clean:
                return value
        # Se não mapeado, remover caracteres não alfanuméricos e limitar ao essencial
        clean_name = doc_name.split(",")[0].split("nº")[0].strip()
        clean_name = self.remove_accents(clean_name)
        return "".join(c for c in clean_name if c.isalnum())
    
    def standardize_date(self, date_str):
        """
        Padroniza a data
        
        Args:
            date_str (str): String da data
            
        Returns:
            str: Data padronizada no formato YYYY-MM-DD
        """
        import pandas as pd
        
        if pd.isna(date_str) or str(date_str).strip() in ["", "-", "nan"]:
            return "SemData"
        try:
            parsed_date = datetime.strptime(str(date_str).strip(), "%d-%m-%Y")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            try:
                parsed_date = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                return "SemData"
    
    def process_dataframe(self, df):
        """
        Processa um DataFrame pandas para renomear os caminhos
        
        Args:
            df (pandas.DataFrame): DataFrame com os dados
            
        Returns:
            pandas.DataFrame: DataFrame atualizado
        """
        import pandas as pd
        
        self.callback("Iniciando processamento de caminhos...", 'info')
        
        # Detectar documentos compartilhados
        shared_docs = {}
        mat_to_shared = {}  # Mapear matrículas mencionadas em Obs
        
        for index, row in df.iterrows():
            pages = str(row["Páginas"]).strip()
            volume = str(row["Volume"]).strip()
            obs = str(row["Obs"]) if pd.notna(row["Obs"]) else ""
            matricula = row["Matrícula"]
            key = (pages, volume)
            mat_number = self.extract_mat_number(matricula)
            if key not in shared_docs:
                shared_docs[key] = {"matriculas": [mat_number], "index": index}
            else:
                shared_docs[key]["matriculas"].append(mat_number)
            # Processar Obs para encontrar matrículas mencionadas
            mat_matches = re.findall(r"Mat\. (\d+)", obs)
            if mat_matches:
                for mat in mat_matches:
                    mat_to_shared[f"Mat.{mat}"] = key
        
        # Lista para novos caminhos e indicador de compartilhamento
        new_file_paths = []
        is_shared = []
        
        # Processar cada linha da planilha
        total_rows = len(df)
        for index, row in df.iterrows():
            self.callback(f"Processando item {index+1}/{total_rows}: Matrícula {row['Matrícula']}", 'info')
            
            matricula = row["Matrícula"]
            doc_name = row["Nome do Documento"]
            date_str = row["Data"]
            pages = str(row["Páginas"]).strip()
            volume = str(row["Volume"]).strip()
            obs = str(row["Obs"]) if pd.notna(row["Obs"]) else ""
            
            # Extrair componentes da pasta e matrícula
            folder_name, matricula_id = self.extract_folder_components(matricula)
            
            # Padronizar tipo de documento e data
            doc_type = self.standardize_doc_type(doc_name)
            date_formatted = self.standardize_date(date_str)
            
            # Adicionar prefixo para documentos incompletos
            prefix = "INCOMPLETO_" if "incompleto" in obs.lower() else ""
            
            # Criar novo caminho do arquivo
            new_file_name = f"{prefix}{date_formatted}_{doc_type}_{matricula_id}.pdf"
            new_file_path = os.path.join(self.base_dir, folder_name, new_file_name).replace("\\", "/")
            
            # Verificar se o documento é compartilhado
            shared_key = (pages, volume)
            mat_number = self.extract_mat_number(matricula)
            shared_info = shared_docs.get(shared_key, {"matriculas": [mat_number]})
            is_shared_doc = len(shared_info["matriculas"]) > 1 or mat_number in mat_to_shared
            
            new_file_paths.append(new_file_path)
            is_shared.append("Sim" if is_shared_doc else "Não")
        
        # Atualizar DataFrame
        df["Arquivo Extraído"] = new_file_paths
        df["Documento Compartilhado"] = is_shared
        
        self.callback(f"Processamento concluído. {total_rows} entradas atualizadas.", 'info')
        
        return df

def rename_paths_in_excel(excel_path, output_excel_path, base_dir, callback=None):
    """
    Função auxiliar para renomear caminhos em um arquivo Excel
    
    Args:
        excel_path (str): Caminho para o arquivo Excel de entrada
        output_excel_path (str): Caminho para o arquivo Excel de saída
        base_dir (str): Diretório base para os documentos extraídos
        callback (function): Função de callback para reportar progresso
        
    Returns:
        bool: True se o processamento foi bem-sucedido, False caso contrário
    """
    try:
        import pandas as pd
        
        # Inicializar renomeador
        renamer = PathRenamer(base_dir, callback)
        
        # Carregar planilha
        if callback:
            callback(f"Carregando planilha: {excel_path}", 'info')
        df = pd.read_excel(excel_path)
        
        # Processar DataFrame
        df_updated = renamer.process_dataframe(df)
        
        # Salvar planilha atualizada
        if callback:
            callback(f"Salvando planilha atualizada: {output_excel_path}", 'info')
        df_updated.to_excel(output_excel_path, index=False)
        
        if callback:
            callback(f"Planilha atualizada salva com sucesso.", 'info')
        
        return True
    
    except Exception as e:
        if callback:
            callback(f"Erro ao processar arquivo Excel: {e}", 'error')
        return False