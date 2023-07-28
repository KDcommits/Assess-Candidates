import os 
import uuid
import openai
import pymongo
import pandas as pd
import mysql.connector
from dotenv import load_dotenv


load_dotenv()
collection  = pymongo.MongoClient(os.getenv("MONGO_URI") )['Resume']['Resume']
candidate_qna = pymongo.MongoClient(os.getenv("MONGO_URI") )['Resume']['Candidate_QnA']

class CandidateCredentials:
    def __init__(self, db_config):
        self.db_config = db_config

    def create_candidate_credentials(self,candidate_email_id):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            id = uuid.uuid4().hex[:16]
            email = candidate_email_id
            password = uuid.uuid4().hex[:16]
            cursor.execute("INSERT INTO candidates (id, email, password) VALUES (%s,%s, %s)", 
                           (id, email, password))
            conn.commit()
            conn.close()
        except Exception as e:
            raise(e)

class DescriptiveQnAGenerator:
    def __init__(self,candidate_email_id):
        self.candidate_email_id = candidate_email_id

    def promptDescriptiveQuestions(self) -> str:
        '''
            Prompt engineeering with fewshots.
        '''
        filter_={"email":self.candidate_email_id}
        projection = {"_id": 0,"phone":0,"job_role":0,"education":0,'name':0,'email':0}
        query_result = collection.find(filter_, projection) 
        d  = pd.DataFrame(query_result)
        candidate_summary = d.to_dict(orient='records')[0]
        del d
        if candidate_summary:
            descriptive_prompt = f'''
                You are an experienced recruiter specialized in technical assessment of the candidates.
                From the given dictionary in the $ delimiter, you need to prepare 2 easy, 2 medium and 1 hard descriptive type question.
                You will also have to write answer for the same. Here is the JSON Schema instance your output must adhere to:
                
                "json
                [{{
                'question': 'Which programming language is often used for data analysis and has libraries like Pandas and NumPy?',
                'answer': 'Python'
                }}]
                "
                Prepare the level of question based on candidates years of experience(yoe). 
                The candidate's summary goes here ${candidate_summary}$. 
                Response shall be in JSON Format.Contain no additional information.
                Your output will be parsed and type-checked according to the provided schema instance inside & delimiter, so make sure all fields in your output match exactly!
                '''.replace("\n","").replace("  ","")
            
            return descriptive_prompt
        else:
            return "Candidate information not found!"

    def generateQAFromDescriptivePrompt(self) -> list:
        '''
            Crtical step : Generating the QnA output as list of dict using GPT 3.5 Turbo
        '''
        try:
            descriptive_prompt = self.promptDescriptiveQuestions()
            completions = openai.Completion.create(
                engine = 'gpt-3.5-turbo',
                prompt = descriptive_prompt,
                temperature = 3
            )
            response = completions.choices[0]['text']
            return eval(response)
        except Exception as e :
            raise(e)
    
    def insertDescriptiveQAforCandidate(candidate_email_id:str):
        '''
            Inserting the questions and answers generated based on the resume of the 
            candidate to the mongoDB database. 
        '''
        try:
            filter_= {"email":candidate_email_id}
            #projection = {"_id": 0,"phone":0,"job_role":0,"education":0,"yoe":0,'name':0,'email':0}
            #query_result = collection.find(filter_, projection) 
            candidate_name = collection.find(filter_, {'name'}).next()['name']
            #d  = pd.DataFrame(query_result)
            #candidate_summary = d.to_dict(orient='records')[0]
            #del d 
            #descriptive_prompt = promptDescriptiveQuestions(candidate_summary)
            # descriptive_qna_dict = self.generateQAFromDescriptivePrompt()
            descriptive_qna_dict = [
                                    {
                                        "question": "What is the purpose of VLOOKUP function in MS Excel, and how is it used?",
                                        "answer": "The VLOOKUP function in MS Excel is used to search for a value in the first column of a table range and return a related value from another specified column. It is often used for performing vertical lookups or searches in a dataset. The syntax of the VLOOKUP function is: VLOOKUP(lookup_value, table_array, col_index_num, [range_lookup])."
                                    },
                                    {
                                        "question": "Explain the concept of Lean Six Sigma - Green Belt and its significance in process improvement.",
                                        "answer": "Lean Six Sigma - Green Belt is a level of certification that indicates a person's understanding and proficiency in process improvement methodologies. It focuses on the DMAIC approach (Define, Measure, Analyze, Improve, and Control) for identifying and resolving problems in a systematic and data-driven manner. A Green Belt holder plays a vital role in process improvement projects, driving efficiency, reducing defects, and improving overall quality."
                                    },
                                    {
                                        "question": "Can you describe the critical components of Salesforce as a customer relationship management (CRM) platform?",
                                        "answer": "Salesforce is a widely used CRM platform that consists of several critical components. Some of the key components include: 1. Leads: Managing potential customers and their information. 2. Accounts: Storing information about individual customers or organizations. 3. Opportunities: Tracking potential sales deals and their progress. 4. Reports and Dashboards: Analyzing data and generating visualizations for insights. 5. Workflows and Automation: Automating repetitive tasks and processes. 6. Email Integration: Integrating emails with the CRM to track communication with customers."
                                    },
                                    {
                                        "question": "How would you approach a complex technical issue as a Technical Support Specialist, and what problem-solving strategies would you employ?",
                                        "answer": "As a Technical Support Specialist, I would start by actively listening to the customer's issue and gathering all relevant information. Then, I would use my critical thinking skills to analyze the problem thoroughly, breaking it down into smaller components. Next, I would apply systematic problem-solving strategies such as root cause analysis and the 5 Whys technique to identify the underlying cause. Once the root cause is determined, I would propose and implement a solution while keeping the customer informed throughout the process. Finally, I would verify that the issue is resolved and provide additional support if needed."
                                    },
                                    {
                                        "question": "Explain the concept of Kaizen and its role in continuous process improvement.",
                                        "answer": "Kaizen is a Japanese term that translates to 'continuous improvement.' In the context of process improvement, Kaizen refers to the philosophy of making incremental, small improvements in processes, products, or services over time. It involves the participation of all employees in identifying areas for improvement and finding innovative solutions. Kaizen aims to create a culture of continuous improvement, where even minor enhancements can lead to significant long-term benefits, such as increased efficiency, reduced waste, and improved quality."
                                    }
                                    ]

            record = {"name":candidate_name, "email":candidate_email_id,"descriptive_qna": descriptive_qna_dict}
            candidate_qna.insert_one(record)

        except Exception as e :
            raise(e)
        
