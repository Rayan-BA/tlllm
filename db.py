from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class User:
    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(32))

class Chat:
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

class Message:
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.Date, default=datetime.datetime.now(datetime.UTC))