from flask import Flask, render_template, session, Response, request, redirect, flash
from gevent.pywsgi import WSGIServer
from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI
from os import getenv
import sse

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = getenv("SECRET_KEY")

channel = sse.Channel()

@app.route("/")
def index():
    return redirect("home")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/subscribe")
def subscribe():
    return channel.subscribe()

@app.route("/publish", methods=["POST"])
def publish():
    channel.publish("GPT-4o:chatgpt response") # this will be returned to client
    channel.publish("Sonnet:claude response")
    channel.publish("Opus:claude response")
    # chatgpt = openai("chatgpt:" + request.data.decode())
    # channel.publish(chatgpt)
    return Response(status=200)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "rayan" and password == "pass":
            session["username"] = username
            return redirect("home")
        else:
            flash("Login failed")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("home")

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
    server = WSGIServer(("127.0.0.1", 5000), app)
    print("Server started at 127.0.0.1:5000")
    server.serve_forever()