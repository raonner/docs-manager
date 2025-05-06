import os
import pandas as pd
import re
from PyPDF2 import PdfReader, PdfWriter

# Configurações
INPUT_EXCEL = "Índice Documentos Matrículas_Atualizado.xlsx"
PROCESSOS_DIR = "processos"

# Função para extrair intervalo de páginas
def parse_page_range(page_str):
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

# Função para formatar o nome do arquivo de origem
def get_input_pdf_name(origem, volume):
    origem_clean = origem
    return f"{origem_clean}_{volume}.pdf"

# Carregar planilha
try:
    df = pd.read_excel(INPUT_EXCEL)
except FileNotFoundError:
    print(f"Erro: Planilha '{INPUT_EXCEL}' não encontrada.")
    exit(1)
except Exception as e:
    print(f"Erro ao carregar a planilha: {e}")
    exit(1)

# Criar diretórios para arquivos extraídos
for file_path in df["Arquivo Extraído"]:
    output_dir = os.path.dirname(file_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Diretório criado: {output_dir}")

# Processar cada linha da planilha
for index, row in df.iterrows():
    origem = str(row["Origem"]).strip()
    volume = str(row["Volume"]).strip()
    pages = row["Páginas"]
    output_path = row["Arquivo Extraído"]
    matricula = row["Matrícula"]
    
    # Determinar arquivo de origem
    input_pdf_name = get_input_pdf_name(origem, volume)
    input_pdf = os.path.join(PROCESSOS_DIR, input_pdf_name)
    
    # Verificar se o arquivo de origem existe
    if not os.path.exists(input_pdf):
        print(f"Erro: Arquivo de origem '{input_pdf}' não encontrado para Matrícula {matricula}.")
        continue
    
    # Extrair intervalo de páginas
    start_page, end_page = parse_page_range(pages)
    if start_page is None or end_page is None:
        print(f"Erro: Intervalo de páginas inválido '{pages}' para Matrícula {matricula}.")
        continue
    
    # Verificar se o intervalo é válido
    if start_page < 1 or end_page < start_page:
        print(f"Erro: Intervalo de páginas inválido ({start_page}-{end_page}) para Matrícula {matricula}.")
        continue
    
    # Aviso para intervalos longos
    num_pages = end_page - start_page + 1
    if num_pages > 10:
        print(f"Aviso: Intervalo longo ({start_page}-{end_page}, {num_pages} páginas) para Matrícula {matricula}. Verificando...")

    try:
        # Abrir PDF de origem
        reader = PdfReader(input_pdf)
        total_pages = len(reader.pages)
        
        # Verificar se o intervalo está dentro do total de páginas
        if end_page > total_pages:
            print(f"Erro: Intervalo ({start_page}-{end_page}) excede o total de páginas ({total_pages}) em '{input_pdf}' para Matrícula {matricula}.")
            continue
        
        # Criar PDF de saída
        writer = PdfWriter()
        for page_num in range(start_page - 1, end_page):
            writer.add_page(reader.pages[page_num])
        
        # Salvar PDF extraído
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        print(f"PDF extraído salvo em: {output_path} ({num_pages} páginas)")
    
    except Exception as e:
        print(f"Erro ao extrair páginas {start_page}-{end_page} de '{input_pdf}' para Matrícula {matricula}: {e}")

print("Extração concluída.")