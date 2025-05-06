# Sistema de Gerenciamento de Matrículas

Sistema web para extração e organização de documentos relacionados a matrículas imobiliárias.

## Descrição

Este sistema permite gerenciar múltiplos projetos de extração e organização de documentos de matrículas, com uma interface web intuitiva que facilita a criação, edição e execução dos projetos.

Cada projeto contém:
- Um arquivo Excel de índice com informações sobre as matrículas
- Uma pasta para arquivos de origem (PDFs)
- Uma pasta para documentos extraídos

O sistema automatiza:
1. A renomeação de caminhos no arquivo Excel com base nas informações de matrícula
2. A extração de páginas específicas dos PDFs de origem
3. A organização dos documentos extraídos em uma estrutura padronizada

## Requisitos

- Python 3.8 ou superior
- Bibliotecas Python (instaladas automaticamente via pip):
  - Flask
  - Flask-SQLAlchemy
  - pandas
  - PyPDF2
  - openpyxl

## Instalação

1. Clone o repositório:
```
git clone <url-do-repositorio>
cd sistema-matriculas
```

2. Crie um ambiente virtual (opcional, mas recomendado):
```
python -m venv venv
```

3. Ative o ambiente virtual:
   - Windows:
   ```
   venv\Scripts\activate
   ```
   - Linux/Mac:
   ```
   source venv/bin/activate
   ```

4. Instale as dependências:
```
pip install -r requirements.txt
```

## Configuração

O sistema utiliza SQLite como banco de dados por padrão. Não é necessária nenhuma configuração adicional para começar a usar.

## Execução

1. Inicie o servidor Flask:
```
python run.py
```

2. Acesse o sistema no navegador:
```
http://localhost:5000
```

## Uso

### Criar um novo projeto

1. Na página inicial, clique em "Novo Projeto"
2. Preencha o nome e a descrição do projeto
3. Clique em "Criar Projeto"

### Adicionar arquivos de origem

1. Na página do projeto, vá para a aba "Arquivos de Origem"
2. Use o formulário de upload para enviar os arquivos PDF

### Gerenciar o índice de matrículas

1. Na página do projeto, vá para a aba "Índice de Matrículas"
2. Adicione entradas manualmente ou importe de um arquivo Excel existente

### Processar documentos

1. Na página do projeto, clique no botão "Processar"
2. Selecione as operações desejadas (renomear caminhos, extrair PDFs)
3. Clique em "Iniciar Processamento"
4. Acompanhe o progresso na aba "Logs"

## Estrutura do Projeto

```
sistema-matriculas/
├── app/                      # Código da aplicação Flask
│   ├── static/               # Arquivos estáticos (CSS, JS)
│   ├── templates/            # Templates HTML
│   ├── models/               # Modelos de dados
│   ├── routes/               # Rotas da aplicação
│   └── utils/                # Utilitários (scripts adaptados)
├── projetos/                 # Diretório para armazenar os projetos
├── instance/                 # Banco de dados SQLite
├── config.py                 # Configurações da aplicação
├── requirements.txt          # Dependências
└── run.py                    # Script para iniciar a aplicação
```

## Desenvolvimento Futuro

Funcionalidades planejadas para futuras versões:
- Edição do índice de matrículas diretamente na interface web
- Visualização de PDFs no navegador
- Exportação de relatórios
- Autenticação de usuários
- Backup automático de projetos

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.