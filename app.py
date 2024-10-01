from flask import Flask, render_template, session, Response, request, redirect, make_response
from flask_socketio import SocketIO, emit
from gevent.pywsgi import WSGIServer
from flask_migrate import Migrate
from anthropic import Anthropic
from dotenv import load_dotenv
from datetime import timedelta
from openai import OpenAI
from os import getenv
from db import *
import json

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")
app.permanent_session_lifetime = timedelta(hours=1)
db.init_app(app)

migrate = Migrate(app, db, render_as_batch=True)
socketio = SocketIO(app)

@app.route("/")
def index():
    return redirect("/home")

@app.route("/home")
def home():
    chats = []
    if session.get("username"):
        user = User.query.filter(User.username == session.get("username")).first()
        if session.get("user_id"):
            chats = Chat.query.filter(Chat.user_id == user.id).all()
    return render_template("home.html", chats=chats)

@app.route("/home/<chat_id>")
def get_chat(chat_id):
    if db.session.get(Chat, chat_id).user_id != session.get("user_id"):
        return redirect("/home")
        
    chats = Chat.query.filter(Chat.user_id == session.get("user_id")).all()
    messages = Message.query.filter(Message.chat_id == chat_id).order_by(Message.timestamp.desc()).all()
    return render_template("home.html", chats=chats, chat_msgs=messages)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        userMatch = User.query.filter(User.username == username).first()
        if userMatch and userMatch.check_password(password):
            session["username"] = username
            session["user_id"] = userMatch.id
            res = make_response(redirect("/home"))
            res.set_cookie("username", username)
            return res
        else:
            print("login failed")
            return redirect("login")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("user_id", None)
    return redirect("/home")

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("username"):
        return redirect("/home")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter(User.username == username).first():
            print("Username unavailable")
        else:
            newUser = User(username, password)
            db.session.add(newUser)
            db.session.commit()
            session["username"] = newUser.username
            session["user_id"] = newUser.id
            return redirect("/home")

    return render_template("register.html")

@socketio.on("user prompt")
def client(msg):
    username = session.get("username")

    if username is None:
        print("go back")
        return Response(status=401)

    response = openai(msg.get("content"))
    model = response.model
    gpt_msg = response.choices[0].message.content

    if User.query.filter(User.username == model).first() is None:
        newModel = User(model, None, True)
        db.session.add(newModel)
        db.session.commit()
        session["model_id"] = newModel.id

    # if username:
    user = User.query.filter(User.username == username).first()
    model = User.query.filter(User.is_llm).first()
    # TODO: handle fresh chat
    if msg.get("chat_id") == "home":
        chat = Chat(user=user)
    else:
        chat = db.session.get(Chat, int(msg.get("chat_id")))

    user_message = Message(content=msg.get("content"), user=user, chat=chat)
    gpt_message = Message(content=gpt_msg, chat=chat, user=model)


    user_message_dict = user_message.__dict__.copy()
    user_message_dict["user"] = user_message_dict.get("user").__dict__.copy()
    del user_message_dict["user"]["password"]
    del user_message_dict["user"]["_sa_instance_state"]
    del user_message_dict["_sa_instance_state"]
    del user_message_dict["chat"]

    gpt_message_dict = gpt_message.__dict__.copy()
    gpt_message_dict["user"] = gpt_message_dict.get("user").__dict__.copy()
    del gpt_message_dict["user"]["password"]
    del gpt_message_dict["user"]["_sa_instance_state"]
    del gpt_message_dict["_sa_instance_state"]
    del gpt_message_dict["chat"]

    db.session.add(user_message)
    db.session.add(gpt_message)
    db.session.commit()

    # if msg.get("chat_id") == "home":
    #     return redirect(f"/home/{chat.id}")
    # else:
        # emit("llm message", gpt_message)

    emit("llm message", gpt_message_dict)

def openai(prompt):
    chatGPT_client = OpenAI()
    response = chatGPT_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0
    )
    return response

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