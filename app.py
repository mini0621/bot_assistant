import os
import datetime as dt

import openai
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

conversations = []
prompt_conversation_num = 4
bot_name = "Curie"
conversation_name =  f"conversations_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}"

#commands list
log_activity = "/log"
pomodoro = "/pomodoro"


@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        user_name = request.form["user"]
        new_prompt = request.form["prompt"]
        if new_prompt.startswith(log_activity):
            answer = log_activity(new_prompt)
        else:
            answer = chat(conversation_name, user_name, new_prompt)
        return redirect(url_for("index", answer=answer))
    answer = request.args.get("answer")
    return render_template("index.html", answer=answer)

def log_activity(new_prompt):
    activity_name = new_prompt.split(" ")[1]
    log_time = dt.datetime.now()
    log_date = log_time.strftime('%Y-%m-%d')
    with open(f"activity_log/{log_date}.txt", "a") as fp:
        fp.write(f"{log_time}:{activity_name}\n")
    return f"I logged an activity.\n{log_time}:{activity_name}"

def chat(conversation_name, user_name, new_prompt):
    update_conversations(conversation_name, new_prompt, user_name)
    response = openai.Completion.create(
         engine="text-davinci-002",
         prompt=generate_prompt(),
         temperature=0.8,
         max_tokens=150,
         top_p=1,
         frequency_penalty=0.0,
         presence_penalty=0.6,
    )
    answer = response.choices[0].text
    update_conversations(conversation_name, answer, bot_name)
    return answer       
    

def generate_prompt():
    print("generating prompt")
    setting = f"The following is a conversation with an AI assistant, {bot_name}. The assistant is intelligent, logical, and helpful.\n\n"
    prompt = setting + "\n".join(conversations) + f"\n{bot_name}:" 
    print("----------------------")     
    print(prompt)     
    print("----------------------")     
    return prompt

def update_conversations(conversation_name, reply, user_name):
    with open(f"conversation_log/{conversation_name}.txt", "a") as fp:
        fp.write(f"{user_name}:{reply}\n")
        print("logging")
    conversations.append(f"{user_name}:{reply}")
    while len(conversations) > prompt_conversation_num:
        conversations.pop(0)
