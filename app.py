from flask import Flask, render_template, session, Response, request, redirect, make_response
from flask_socketio import SocketIO, emit
from gevent.pywsgi import WSGIServer
from flask_migrate import Migrate
from anthropic import Anthropic
from dotenv import load_dotenv
from datetime import timedelta
# from flask_cors import CORS
from openai import OpenAI
from os import getenv
from db import *

load_dotenv()

app = Flask(__name__)
# CORS(app)
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
        
    # chats = Chat.query.filter(Chat.user_id == session.get("user_id")).all()
    messages = Message.query.filter(Message.chat_id == chat_id).order_by(Message.timestamp.desc()).all()
    return render_template("/partials/chat.html", chat_msgs=messages)

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
        confirm_password = request.form.get("confirm_password")
        if User.query.filter(User.username == username).first():
            print("Username unavailable")
        elif password != confirm_password:
            pass
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
        emit("llm message", {"content": "Please login...","user": {"username": "TLLLM"}})
        return Response(status=401)

    gpt_model_name = "gpt-4o-mini"
    gpt_response = openai(msg.get("content"), gpt_model_name)
    gpt_msg = gpt_response.choices[0].message.content
    
    haiku_model_name = "claude-3-haiku-20240307"
    haiku_response = anthropic_1(msg.get("content"), haiku_model_name)
    haiku_msg = haiku_response.content[0].text

    sonnet_model_name = "claude-3-5-sonnet-20240620"
    sonnet_response = anthropic_2(msg.get("content"), sonnet_model_name, f"<gpt>{gpt_msg}</gpt><claude>{haiku_msg}</claude>")
    sonnet_msg = sonnet_response.content[0].text

    models = [gpt_model_name, haiku_model_name, sonnet_model_name]

    for model in models:
        if User.query.filter(User.username == model).first() is None:
            newModel = User(model, None, True)
            db.session.add(newModel)
            db.session.commit()
            # session["model_id"] = newModel.id

    # if username:
    user = User.query.filter(User.username == username).first()
    gpt_model = User.query.filter(User.username == gpt_model_name).first()
    haiku_model = User.query.filter(User.username == haiku_model_name).first()
    sonnet_model = User.query.filter(User.username == sonnet_model_name).first()
    # TODO: handle fresh chat
    if msg.get("chat_id") == "home":
        chat = Chat(user=user)
    else:
        chat = db.session.get(Chat, int(msg.get("chat_id")))

    add_message(msg.get("content"), chat, user)

    gpt_message_dict = add_message(gpt_msg, chat, gpt_model)
    emit("llm message", gpt_message_dict)
    
    haiku_message_dict = add_message(haiku_msg, chat, haiku_model)
    emit("llm message", haiku_message_dict)
    
    sonnet_message_dict = add_message(sonnet_msg, chat, sonnet_model)
    emit("llm message", sonnet_message_dict)

def add_message(content, chat, user) -> dict[str, any]:
    message = Message(content=content, user=user, chat=chat)
    message_dict = message.__dict__.copy()
    
    message_dict["user"] = message_dict.get("user").__dict__.copy()
    if not user.is_llm:
        del message_dict["user"]["password"]
    del message_dict["user"]["_sa_instance_state"]
    del message_dict["_sa_instance_state"]
    del message_dict["chat"]
    
    # not efficient but i wanna send messages as they come. will fix with concurrency maybe
    db.session.add(message)
    db.session.commit()
    
    return message_dict

def openai(prompt, model):
    chatGPT_client = OpenAI()
    response = chatGPT_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0
    )
    return response

def anthropic_1(prompt, model):
    claude_client = Anthropic()
    response = claude_client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    )
    return response

def anthropic_2(prompt, model, messages):
    system_rule = f'''
                    You're tasked with combining the best points from two messages, the first is wrapped with <gpt></gpt> tags and second in <claude></claude>.
                    You must follow these rules:
                    1- keep it short, less than 500 words.
                    2- don't add a point of your own, only from provided messages.
                    3- don't say that all points are valid, assume there are objectivly better points.

                    {messages}
                  '''
    claude_client = Anthropic()
    response = claude_client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        system=system_rule,
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    )
    return response

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # server = WSGIServer(("127.0.0.1", 5000), app)
    # print("Server started at 127.0.0.1:5000")
    # server.serve_forever()
    socketio.run(app, host="0.0.0.0", port=5000)