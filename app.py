from openai import OpenAI
import anthropic
from flask import Flask, render_template, request, redirect, session, url_for, Response
from dotenv import load_dotenv
from os import getenv
import sse
from gevent.pywsgi import WSGIServer
import time

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = getenv("SECRET_KEY")

channel = sse.Channel()


@app.route("/", methods=["GET"])
def index():
    return render_template("conversation.html")

@app.route('/subscribe')
def subscribe():
    return channel.subscribe()

@app.route('/publish', methods=["POST"])
def publish():
    # time.sleep(.5)
    channel.publish('message here') # this will be returned to client
    return Response(status=200)

def openai(prompt):
    chatGPT_client = OpenAI()
    response = chatGPT_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    return response

def anthropic(prompt):
    claude_client = anthropic.Anthropic()
    response = claude_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        temperature=0,
        system="You are a world-class poet. Respond only with short poems.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    return response

if __name__ == "__main__":
    server = WSGIServer(("127.0.0.1", 5000), app)
    print("Server started at 127.0.0.1:5000")
    server.serve_forever()
    # response = openai("say one random word")
    # response_message = response.choices[0].message.content