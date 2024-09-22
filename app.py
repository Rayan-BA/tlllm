from openai import OpenAI
import anthropic
from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
from os import getenv
import json

load_dotenv()

def flask():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = getenv("SECRET_KEY")

    @app.route("/")
    def index():
        return render_template("conversation.html")
    
    @app.route("/prompt", methods=["POST", "GET"])
    def handlePrompt():
        if request.method == "POST":
            prompt_text = request.data.decode()
            print(prompt_text)
        return redirect("/")

    app.run()

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
    flask()
    # response = openai("say one random word")
    # response_message = response.choices[0].message.content