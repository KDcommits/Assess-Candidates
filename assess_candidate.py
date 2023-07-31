import os
import pymongo
import numpy as np
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
load_dotenv()
collection  = pymongo.MongoClient(os.getenv("MONGO_URI") )['Resume']['Resume']
candidate_qna = pymongo.MongoClient(os.getenv("MONGO_URI") )['Resume']['Candidate_QnA']

class AssessCandidate:
    def __init__(self,candidate_email_id):
        self.candidate_email_id = candidate_email_id
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

    def _calculate_semantic_similarity(self,sentence1, sentence2):
        '''
            Calculate Similartity score between GPT answer and candidate answer
        '''
        embeddings = self.model.encode([sentence1, sentence2], convert_to_tensor=True)
        cosine_sim = util.pytorch_cos_sim(embeddings[0], embeddings[1])
        return cosine_sim.item()
    
    def updateCandidateDescriptiveAnswers(self,descriptive_answers:list) -> float:
        '''
        Update answer of each descriptive question from the candidate and score them
        '''
        filter_={"email":self.candidate_email_id}
        gpt_answers = candidate_qna.find(filter_, {'resume_descriptive_qna'}).next()['resume_descriptive_qna']
        scores = []
        for i in range(len(descriptive_answers)):
            if descriptive_answers[i]!="":
                candidate_descriptive_answer = descriptive_answers[i]
                gpt_answer  =  gpt_answers[i]['answer']
                similarity_score = self._calculate_semantic_similarity(candidate_descriptive_answer, gpt_answer)
                scores.append(similarity_score)
                candidate_qna.update_one({"email": self.candidate_email_id},
                                {"$set": {f"resume_descriptive_qna.{i}.candidate_descriptive_answer": candidate_descriptive_answer,
                                        f"resume_descriptive_qna.{i}.score": similarity_score}})
            else:
                scores.append(0)
                candidate_qna.update_one({"email": self.candidate_email_id},
                                {"$set": {f"resume_descriptive_qna.{i}.candidate_descriptive_answer": "No Answer Written",
                                        f"resume_descriptive_qna.{i}.score": 0}})
                
        return np.mean(scores)

    def updateCandidateMCQAnswers(self, mcq_answers:list)->float:
        ''''
            Update answer of each MCQ question from the candidate and store the score 
        '''
        filter_={"email":self.candidate_email_id}
        gpt_answers = candidate_qna.find(filter_, {'resume_mcq'}).next()['resume_mcq']
        scores = []
        for i in range(len(mcq_answers)):
            if mcq_answers[i]!="":
                candidate_mcq_answer = mcq_answers[i]
                gpt_answer  =  gpt_answers[i]['answer']
                if gpt_answer==candidate_mcq_answer:
                    score = 1
                    scores.append(score)
                    candidate_qna.update_one({"email": self.candidate_email_id},
                                    {"$set": {f"resume_mcq.{i}.candidate_mcq_answer": candidate_mcq_answer,
                                            f"resume_mcq.{i}.score": score}})
                else:
                    score = 0
                    scores.append(score)
                    candidate_qna.update_one({"email": self.candidate_email_id},
                                    {"$set": {f"resume_mcq.{i}.candidate_mcq_answer": candidate_mcq_answer,
                                            f"resume_mcq.{i}.score": score}})

            else:
                score = 0
                scores.append(score)
                candidate_qna.update_one({"email": self.candidate_email_id},
                                {"$set": {f"resume_mcq.{i}.candidate_mcq_answer": "No Answer Written",
                                        f"resume_mcq.{i}.score": 0}})
                
        return np.mean(scores)