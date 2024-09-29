from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class User(db.Model):
    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
    
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    username = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(32), nullable=False)

    chats = db.relationship("Chat", backref = "user", cascade = "all, delete-orphan", lazy = "dynamic")#, primaryjoin="User.id == Chat.user_id")

    def check_password(self, password):
        return self.password == password

class Chat(db.Model):
    def __init__(self) -> None:
        pass
    
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    messages = db.relationship("Message", backref = "chat", cascade = "all, delete-orphan", lazy = "dynamic")#, primaryjoin="Chat.id == Message.chat_id")
    

class Message(db.Model):
    def __init__(self, content) -> None:
        # self.sender_id = sender_id
        self.content = content
    
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(datetime.UTC),nullable=False )
    chat_id = db.Column(db.Integer, db.ForeignKey("chat.id"))
