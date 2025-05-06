import os
import pandas as pd
import re
from datetime import datetime
import unicodedata

# Configurações
BASE_DIR = "docs"
INPUT_EXCEL = "Índice Documentos Matrículas_Atualizado.xlsx"
OUTPUT_EXCEL = "Índice Documentos Matrículas_Atualizado.xlsx"

# Mapeamento de tipos de documentos
DOC_TYPE_MAPPING = {
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

# Função para remover acentos
def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

# Função para extrair Livro, Folhas e Matrícula
def extract_folder_components(matricula_str):
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

# Função para extrair número da matrícula
def extract_mat_number(matricula_str):
    if not isinstance(matricula_str, str):
        matricula_str = str(matricula_str)
    match = re.search(r"Mat\. (\d+)", matricula_str)
    return f"Mat.{match.group(1)}" if match else matricula_str

# Função para padronizar tipo de documento
def standardize_doc_type(doc_name):
    if pd.isna(doc_name) or not str(doc_name).strip():
        return "Desconhecido"
    doc_name = str(doc_name)
    doc_name_clean = remove_accents(doc_name).lower()
    for key, value in DOC_TYPE_MAPPING.items():
        if remove_accents(key).lower() in doc_name_clean:
            return value
    # Se não mapeado, remover caracteres não alfanuméricos e limitar ao essencial
    clean_name = doc_name.split(",")[0].split("nº")[0].strip()
    clean_name = remove_accents(clean_name)
    return "".join(c for c in clean_name if c.isalnum())

# Função para padronizar data
def standardize_date(date_str):
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

# Carregar planilha
try:
    df = pd.read_excel(INPUT_EXCEL)
except FileNotFoundError:
    print(f"Erro: Planilha '{INPUT_EXCEL}' não encontrada no diretório atual.")
    exit(1)
except Exception as e:
    print(f"Erro ao carregar a planilha: {e}")
    exit(1)

# Detectar documentos compartilhados
shared_docs = {}
mat_to_shared = {}  # Mapear matrículas mencionadas em Obs
for index, row in df.iterrows():
    pages = str(row["Páginas"]).strip()
    volume = str(row["Volume"]).strip()
    obs = str(row["Obs"]) if pd.notna(row["Obs"]) else ""
    matricula = row["Matrícula"]
    key = (pages, volume)
    mat_number = extract_mat_number(matricula)
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
for index, row in df.iterrows():
    matricula = row["Matrícula"]
    doc_name = row["Nome do Documento"]
    date_str = row["Data"]
    pages = str(row["Páginas"]).strip()
    volume = str(row["Volume"]).strip()
    obs = str(row["Obs"]) if pd.notna(row["Obs"]) else ""

    # Extrair componentes da pasta e matrícula
    folder_name, matricula_id = extract_folder_components(matricula)

    # Padronizar tipo de documento e data
    doc_type = standardize_doc_type(doc_name)
    date_formatted = standardize_date(date_str)

    # Adicionar prefixo para documentos incompletos
    prefix = "INCOMPLETO_" if "incompleto" in obs.lower() else ""

    # Criar novo caminho do arquivo
    new_file_name = f"{prefix}{date_formatted}_{doc_type}_{matricula_id}.pdf"
    new_file_path = os.path.join(BASE_DIR, folder_name, new_file_name).replace("\\", "/")

    # Verificar se o documento é compartilhado
    shared_key = (pages, volume)
    mat_number = extract_mat_number(matricula)
    shared_info = shared_docs.get(shared_key, {"matriculas": [mat_number]})
    is_shared_doc = len(shared_info["matriculas"]) > 1 or mat_number in mat_to_shared

    new_file_paths.append(new_file_path)
    is_shared.append("Sim" if is_shared_doc else "Não")

# Atualizar planilha
df["Arquivo Extraído"] = new_file_paths
df["Documento Compartilhado"] = is_shared
try:
    df.to_excel(OUTPUT_EXCEL, index=False)
    print(f"Planilha atualizada salva em: {OUTPUT_EXCEL}")
except Exception as e:
    print(f"Erro ao salvar a planilha: {e}")
    exit(1)