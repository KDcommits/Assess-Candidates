import os
import pymongo
import numpy as np
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
load_dotenv()
collection  = pymongo.MongoClient(os.getenv("MONGO_URI") )['Resume']['Resume']
candidate_qna = pymongo.MongoClient(os.getenv("MONGO_URI") )['Resume']['Candidate_QnA']


def calculate_semantic_similarity(model, sentence1, sentence2):
    '''
        Calculate Similartity score between GPT answer and candidate answer
    '''
    embeddings = model.encode([sentence1, sentence2], convert_to_tensor=True)
    cosine_sim = util.pytorch_cos_sim(embeddings[0], embeddings[1])
    return cosine_sim.item()
    
def updateCandidateDescriptiveAnswers(candidate_email_id, candidate_answers) -> float:
    '''
    Update answer of each question from the candidate 
    '''
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    filter_={"email":candidate_email_id}
    gpt_answers = candidate_qna.find(filter_, {'descriptive_qna'}).next()['descriptive_qna']
    scores = []
    for i in range(len(candidate_answers)):
        if candidate_answers[i]!="":
            candidate_answer = candidate_answers[i]
            gpt_answer  =  gpt_answers[i]['answer']
            similarity_score = calculate_semantic_similarity(model, candidate_answer, gpt_answer)
            scores.append(similarity_score)
            candidate_qna.update_one({"email": candidate_email_id},
                            {"$set": {f"descriptive_qna.{i}.candidate_answer": candidate_answer,
                                      f"descriptive_qna.{i}.score": similarity_score}})
        else:
            scores.append(0)
            candidate_qna.update_one({"email": candidate_email_id},
                            {"$set": {f"descriptive_qna.{i}.candidate_answer": "No Answer Written",
                                      f"descriptive_qna.{i}.score": 0}})
            
    return np.mean(scores)
