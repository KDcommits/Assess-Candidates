import os
import re
import uuid
import bcrypt
import pymongo
import warnings
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
warnings.filterwarnings('ignore')
from assess_candidate import AssessCandidate
from flask import Flask, render_template, request, url_for, redirect, session, jsonify

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MySQL configurations
db_config = {
    "host": os.getenv('DB_HOST'),
    "user": os.getenv('DB_USERNAME'),
    "password": os.getenv('DB_PASSWORD'),
    "database": os.getenv('DB_NAME'),
}

## Connecting to the mysql database to store user 
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# ## getting the mongoDB Collection: DataBase Name : Resume , Collection Name : Resume
collection  = pymongo.MongoClient( os.getenv("MONGO_URI") )['Resume']['Resume']
candidate_qna = pymongo.MongoClient(os.getenv("MONGO_URI") )['Resume']['Candidate_QnA']


@app.route("/")
def home():
    return render_template("login.html")

@app.route('/submit_answers', methods=['POST'])
def submit_answers():
    if "user_id" in session:
        candidate_email_id = session['user_id']
        print(candidate_email_id)
        mcq_answers = list(request.json['mcq_answers'].values())
        descriptive_answers = list(request.json['descriptive_answers'].values())
        assess_object = AssessCandidate(candidate_email_id)
        descriptive_score = assess_object.updateCandidateDescriptiveAnswers(descriptive_answers)
        objective_score = assess_object.updateCandidateMCQAnswers(mcq_answers)
        net_score = round(((descriptive_score+objective_score)/2)*100, 2)
        candidate_qna.update_one({"email": candidate_email_id}, 
                                                {"$set": {"status": "Assessment Completed","test_score":net_score}})
        return {"success": True}
    else:
        return render_template('/')
        
@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]
        cursor.execute(f"SELECT password FROM candidates WHERE email = '{email}';")
        stored_password = cursor.fetchone()[0]
        if stored_password:
            if stored_password == password:
                session["user_id"] = email
                return {"success": True}
            else:
                return {"success": False}
        else:
            return {"success": False}
    else:
        return render_template('login.html')
    
@app.route("/test_instructions")
def test_instructions():
    if "user_id" in session:
        return render_template("test_instructions.html")
    else:
        return redirect("/")

    
@app.route("/home")
def dashboard():
    if "user_id" in session:
        candidate_email_id = session['user_id']
        filter_={"email":candidate_email_id}
        descriptive_questions = candidate_qna.find(filter_, {'resume_descriptive_qna'}).next()['resume_descriptive_qna']
        mcq_questions = candidate_qna.find(filter_, {'resume_mcq'}).next()['resume_mcq']
        return render_template("assess_candidate.html", mcq_questions = mcq_questions,
                               descriptive_questions = descriptive_questions)
    else:
        return redirect("/")
    
@app.route('/say_thanks', methods = ['GET','POST'])
def say_thanks():
    #session.pop('user_id')
    print("Session : ", session)
    return render_template("thank_you_page.html")

        
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id')
    print("Session : ", session)
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True)