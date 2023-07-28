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
from assess_candidate import updateCandidateDescriptiveAnswers
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

candidate_email_id = "utkarshrastogi101@gmail.com"

@app.route("/")
def home():
    return render_template("login.html")

@app.route('/submit_answers', methods=['POST'])
def submit_answers():
    if request.method =="POST":
        candidate_answers = list(request.json.values())
        updateCandidateDescriptiveAnswers(candidate_email_id, candidate_answers)
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
                session["user_id"] = stored_password
                return {"success": True}
            else:
                return {"success": False}
        else:
            return {"success": False}
    else:
        return render_template('login.html')
    
@app.route("/home")
def dashboard():
    # Check if the user is logged in
    print(session['user_id'])
    if "user_id" in session:
        filter_={"email":candidate_email_id}
        qna_data = candidate_qna.find(filter_, {'descriptive_qna'}).next()['descriptive_qna']
        print(session['user_id'])
        return render_template("test_descriptive.html", qna_data = qna_data)
        # return render_template("home.html")
    else:
        return redirect("/")
        
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id')
    print("Session : ", session)
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True)