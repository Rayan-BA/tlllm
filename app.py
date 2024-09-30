from flask import Flask, render_template, session, Response, request, redirect, flash
from gevent.pywsgi import WSGIServer
from flask_migrate import Migrate
from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI
from os import getenv
from db import *
from flask_socketio import SocketIO, emit

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")
db.init_app(app)

migrate = Migrate(app, db, render_as_batch=True)
socketio = SocketIO(app)

@app.route("/")
def index():
    return redirect("home")

@app.route("/home")
def home():
    if session.get("username"):
        user = User.query.filter(User.username == session.get("username")).first()
        chats = Chat.query.filter(Chat.user_id == user.id).all()
    return render_template("home.html", chats=chats)

@app.route("/home?chat=<chat_id>")
def get_chat(chat_id):
    # chat = Chat.query.get(chat_id)
    print(chat_id)
    messages = Message.query.filter(Message.chat_id == chat_id).order_by(Message.timestamp.desc()).all()
    return render_template("home.html", chat_msgs=messages)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        userMatch = User.query.filter(User.username == username).first()
        if userMatch and userMatch.check_password(password):
            session["username"] = username
            return redirect("home")
        else:
            print("login failed")
            return redirect("login")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("home")

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("username"):
        return redirect("home")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter(User.username == username).first():
            print("Username unavailable")
        else:
            newUser = User(username, password)
            db.session.add(newUser)
            db.session.commit()
            session["username"] = username
            return redirect("home")

    return render_template("register.html")

@socketio.on("user message")
def client(msg):
    username = session.get("username")
    if username:
        gpt_msg = openai(msg.get("content"))
        user = User.query.filter(User.username == username).first()
        if msg.get("chat_id"):
            chat = db.session.get(Chat, int(msg.get("chat_id")))
            user_message = Message(content=msg.get("content"), user=user, chat=chat)
            gpt_message = Message(content=gpt_msg, chat=chat)
        else:
            chat = Chat(user=user)
            user_message = Message(content=msg.get("content"), user=user, chat=chat)
            gpt_message = Message(content=gpt_msg, chat=chat)

        # db.session.add_all([user_message, gpt_message])
        db.session.add(user_message)
        db.session.add(gpt_message)
        db.session.commit()
        emit("llm message", "GPT-4o:" + gpt_msg)

def openai(prompt):
    chatGPT_client = OpenAI()
    response = chatGPT_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0
    )
    return response.choices[0].message.content

def anthropic(prompt):
    claude_client = Anthropic()
    response = claude_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        temperature=0,
        system="You are a world-class poet. Respond only with short poems.",
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    )
    print(response) 
    return response

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # server = WSGIServer(("127.0.0.1", 5000), app)
    # print("Server started at 127.0.0.1:5000")
    # server.serve_forever()
    socketio.run(app)