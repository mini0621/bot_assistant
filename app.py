import os
import datetime as dt

import openai
from flask import Flask, redirect, render_template, request, url_for, send_file

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

conversations = []
prompt_conversation_num = 4
bot_name = "Curie"
conversation_name =  f"conversations_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}"

#commands list
log_activity_command = "/log"
pomodoro_command = "/pomodoro"

#pomodoro constants
pomodoro_target = 25
pomodoro_break = 5
pomodoro_long_break = 15


fp=open(f"conversation.html", "w")
fp.close()

@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        user_name = request.form["user"]
        new_prompt = request.form["prompt"]
        if new_prompt.startswith(log_activity_command):
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
    with open(f"conversation.html", "a") as fp:
        fp.write(f"<p>{user_name}:{reply}\n</p>")
    conversations.append(f"{user_name}:{reply}")
    while len(conversations) > prompt_conversation_num:
        conversations.pop(0)

@app.route('/conversation.html')
def show_conversations():
    return send_file('conversation.html')


#test from here
@app.route("/conversation", methods=("GET", "POST"))
def conversation():
    if request.method == "POST":
        user_name = request.form["user"]
        new_prompt = request.form["prompt"]
        if new_prompt.startswith(log_activity_command):
            answer = log_activity(new_prompt)
        else:
            answer = chat(conversation_name, user_name, new_prompt)
        return redirect(url_for("conversation", answer=answer))
    answer = request.args.get("answer")
    return render_template("conversation.html", answer=answer)

@app.route("/pomodoro", methods=("GET", "POST"))
def pomodoro():
    if request.method == "POST":
        target = request.form["target"]
        break_target = request.form["break_target"]
        long_break = request.form["long_break"]
        if target == "":
            target = pomodoro_target
        if break_target == "":
            break_target = pomodoro_break
        if long_break == "":
            long_break = pomodoro_long_break
        return render_template("pomodoro.html", target=target, target_break=break_target, long_break=long_break)    
    return render_template("pomodoro.html", target=pomodoro_target, target_break=pomodoro_break, long_break=pomodoro_long_break)

