from datetime import datetime
from app import db

class Projeto(db.Model):
    __tablename__ = 'projetos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    caminho_diretorio = db.Column(db.String(255), nullable=False)
    caminho_excel = db.Column(db.String(255), nullable=False)
    
    # Relacionamento com logs
    logs = db.relationship('Log', backref='projeto', lazy='dynamic')
    
    def __repr__(self):
        return f'<Projeto {self.nome}>'
    
    @property
    def caminho_processos(self):
        """Retorna o caminho para a pasta de processos do projeto"""
        import os
        return os.path.join(self.caminho_diretorio, 'processos')
    
    @property
    def caminho_docs(self):
        """Retorna o caminho para a pasta de documentos extraídos do projeto"""
        import os
        return os.path.join(self.caminho_diretorio, 'docs')


class Log(db.Model):
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'))
    tipo = db.Column(db.String(50), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Log {self.id}: {self.tipo}>'