import os

class Config:
    # Configuração básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao'
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    
    # Configuração do SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASEDIR, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuração de diretórios
    PROJETOS_DIR = os.path.join(BASEDIR, 'projetos')
    
    # Configuração de upload
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB limite para upload
    
    # Configuração de logs
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    
    @staticmethod
    def init_app(app):
        # Criar diretórios necessários se não existirem
        if not os.path.exists(Config.PROJETOS_DIR):
            os.makedirs(Config.PROJETOS_DIR)
        
        # Criar diretório instance se não existir
        instance_dir = os.path.join(Config.BASEDIR, 'instance')
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)