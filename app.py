import os
import datetime as dt

import openai
from flask import Flask, redirect, render_template, request, url_for, send_file
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

conversations = []
prompt_conversation_num = 4
bot_name = "June"
conversation_name =  f"conversations_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}"
date_id = dt.datetime.now().strftime('%Y%m%d')

#commands list
log_activity_command = "/log"

#pomodoro constants
pomodoro_target = 1
pomodoro_break = 1
pomodoro_long_break = 1

#db
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///store.db'
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)

def __rep__(self):
    return '<Todo %r>' % self.id

@app.route("/", methods=("GET", "POST"))
def index():
    return render_template("index.html")

def log_activity(new_prompt):
    activity_name = new_prompt.split(" ")[1]
    log_time = dt.datetime.now()
    log_date = log_time.strftime('%Y-%m-%d')
    with open(f"log/activity_log/{log_date}.txt", "a") as fp:
        fp.write(f"{log_time}:{activity_name}\n")
    return f"I logged an activity.\n{log_time}:{activity_name}"

def correct(prompt):
    response = openai.Completion.create(
         engine="text-davinci-002",
         prompt=f"Correct this to standard English: {prompt}",
         temperature=0,
         max_tokens=60,
         top_p=1,
         frequency_penalty=0.0,
         presence_penalty=0.0,
    )
    answer = response.choices[0].text 
    return answer

def chat(conversation_name, user_name, new_prompt):
    update_conversations(conversation_name, new_prompt, user_name)
    response = openai.Completion.create(
         engine="text-davinci-002",
         prompt=generate_prompt_for_chat(),
         temperature=0.8,
         max_tokens=150,
         top_p=1,
         frequency_penalty=0.0,
         presence_penalty=0.6,
    )
    answer = response.choices[0].text
    update_conversations(conversation_name, answer, bot_name)
    return answer       
    

def generate_prompt_for_chat():
    print("generating prompt")
    setting = f"The following is a conversation with an AI assistant, {bot_name}. The assistant is intelligent, logical, and helpful.\n\n"
    prompt = setting + "\n".join(conversations[-4:]) + f"\n{bot_name}:" 
    print("----------------------")     
    print(prompt)     
    print("----------------------")     
    return prompt

def update_conversations(conversation_name, reply, user_name):
    with open(f"log/conversation_log/{conversation_name}.txt", "a") as fp:
        fp.write(f"{user_name}:{dt.datetime.now()}:{reply}\n")
        print("logging")
    conversations.append(f"{user_name}:{reply}")

@app.route("/conversation", methods=("GET", "POST"))
def conversation():
    if request.method == "POST":
        user_name = request.form["user"]
        new_prompt = request.form["prompt"]
        if new_prompt.startswith(log_activity_command):
            answer = log_activity(new_prompt)
        else:
            answer = chat(conversation_name, user_name, new_prompt)
            #correction = correct(new_prompt)
        return redirect(url_for("conversation", answer=answer, conversations=conversations))
    answer = request.args.get("answer")
    return render_template("conversation.html", answer=answer, conversations=conversations)

@app.route("/pomodoro", methods=("GET", "POST"))
def pomodoro():
    try:
        with open(f"log/pomodoro_log/{date_id}.txt", "r") as fp:
            log = fp.readlines()
    except:
        log =[]
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
        return render_template("pomodoro.html", target=target, target_break=break_target, long_break=long_break, log=log)    
    return render_template("pomodoro.html", target=pomodoro_target, target_break=pomodoro_break, long_break=pomodoro_long_break, log=log)

@app.route('/pomodoro/getdata/<target>')
def get_javascript_data(target):
    current_datetime = dt.datetime.now()
    with open(f"log/pomodoro_log/{date_id}.txt", "a") as fp:
        fp.write(f"{current_datetime}:{target/60}\n")
        print("logging") 

@app.route("/calendar", methods=("GET", "POST"))
def calendar():
    return render_template("calendar.html")


@app.route("/todo", methods=("GET", "POST"))
def todo():
    if request.method == "POST":
        todo = request.form["todo"]
        new_todo = Todo(content=todo)
        try:
            db.session.add(new_todo)
            db.session.commit()
            return redirect('/todo')
        except:
            return 'There was an error while adding the task'
    todos = Todo.query.all()
    return render_template("todo.html", todos=todos)

@app.route('/todo/delete/<int:id>')
def todo_delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/todo')
    except:
        return 'There was an error while deleting that task'

@app.route('/todo/update/<int:id>', methods=['GET','POST'])
def todo_update(id):
    todo = Todo.query.get_or_404(id)

    if request.method == 'POST':
        todo.content = request.form['todo']

        try:
            db.session.commit()
            return redirect('/todo')
        except:
            return 'There was an issue while updating that task'

    else:
        return render_template('todo_update.html', todo=todo)