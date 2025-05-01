
import tkinter as tk
import sys
import requests
import json
import webbrowser
import threading
import time
import torch

from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = None
model = None
token_1 = None
token_2 = None
token_3 = None
token_4 = None
token_5 = None

ready_semaphore = threading.Semaphore(0)

res_sem = threading.Semaphore()
results = {}

def init_llm():
    global tokenizer, model, token_1, token_2, token_3, token_4, token_5, ready_semaphore
    global res_sem, results

    use_cuda = torch.cuda.is_available()
    
    tokenizer = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-360M")
    model = AutoModelForCausalLM.from_pretrained("HuggingFaceTB/SmolLM2-360M").to("cuda" if use_cuda else "cpu")
    
    token_1 = tokenizer("1").to(model.device)['input_ids'][0]
    token_2 = tokenizer("2").to(model.device)['input_ids'][0]
    token_3 = tokenizer("3").to(model.device)['input_ids'][0]
    token_4 = tokenizer("4").to(model.device)['input_ids'][0]
    token_5 = tokenizer("5").to(model.device)['input_ids'][0]
    
    ready_semaphore.release()


def compute_rating(email, i, UserPreference=""):    
    global tokenizer, model, token_1, token_2, token_3, token_4, token_5
    
    input = f"""
        Please give an integer rating from 1 to 5 representing how important the following email would be to the user (5 is the most important).
        Try to reserve 1 for truly useless emails, and 5 for high priority emails. Emails that could potentially be useful or important to the user should on average receive a 3.
        Assume the user values normal things, like bills, job/school obligations, and personal relationships (unless specified otherwise)
        The user may also provide some details about them that would influence what is or is not important to them.
        Details about the user: {UserPreference}
        Again, try to reserve the rating of 1 for the most useless emails, and 5 for high priority emails. Most emails should receive a 3.
        
        Email:
        From: {email['from']}
        Subject: {email['subj']}
        
        {email['body']}
        
        
        Response: """
    
    inputs = tokenizer(input, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model(**inputs, return_dict=True)
        
    logits = output.logits[0][-1]
    probs = logits.softmax(dim=-1)
    prob_1 = probs[token_1]
    prob_2 = probs[token_2]
    prob_3 = probs[token_3]
    prob_4 = probs[token_4]
    prob_5 = probs[token_5]
    
    relevant_probs = torch.tensor([prob_1, prob_2, prob_3, prob_4, prob_5])
    rating = relevant_probs.argmax(dim=-1).item()+1
    results[i] = rating




def compute_rating_for_all(emails, user_pref=""):
    global ready_semaphore, res_sem, results
    
    # basically just checks that the semaphore is in the ready state. I'm using semaphores here because I think a
    # "while true" approach is ugly, and using semaphores will cleanly re-dispatch the thread once the semaphore is released.
    ready_semaphore.acquire()
    ready_semaphore.release()
    
    threads = []
    
    for i, email in enumerate(emails):
        # dispatch a thread to compute the rating for the current email
        thread = threading.Thread(target=compute_rating, args=(email, i, user_pref))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # yield results as they come
    for i, thread in enumerate(threads):
        thread.join()
        res_sem.acquire()
        yield results[i]
        res_sem.release()