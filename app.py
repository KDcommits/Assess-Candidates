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
from werkzeug.utils import secure_filename
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
        if request.method =="POST":
            candidate_email_id = session['user_id']
            print(candidate_email_id)
            mcq_answers = list(request.json['mcq_answers'].values())
            descriptive_answers = list(request.json['descriptive_answers'].values())
            assess_object = AssessCandidate(candidate_email_id)
            print(mcq_answers)
            print(descriptive_answers)
            descriptive_answers = ['The VLOOKUP function in MS Excel is used to search for a value in the first column of a table range and return a related value from another specified column',
                     'Lean Six Sigma - Green Belt is a level of certification that indicates a persons understanding and proficiency in process improvement methodologies.',
                     '',
                     '',
                     '',
                     ]
        
            descriptive_score = assess_object.updateCandidateDescriptiveAnswers(descriptive_answers)
            objective_score = assess_object.updateCandidateMCQAnswers(mcq_answers)
            ## return a page to showcase the score/ Thank you message
            return jsonify({'message': 'Answers received successfully'})
        

# row  : 'ec7b963a86914fe4', 'utkarshrastogi101@gmail.com', 'be9cbd4821944d7a'
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
        
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id')
    print("Session : ", session)
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True)