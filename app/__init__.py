from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Inicializar extensões
db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensões com o app
    db.init_app(app)
    
    # Configurar o app
    config_class.init_app(app)
    
    # Registrar blueprints
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Criar tabelas do banco de dados
    with app.app_context():
        db.create_all()
    
    return app

from app import models