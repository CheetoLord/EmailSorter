
import tkinter as tk
import sys
import requests
import json
import webbrowser
import threading
import time
import torch
from google import genai

from transformers import AutoModelForCausalLM, AutoTokenizer

client = None

ready_semaphore = threading.Semaphore(0)

res_sem = threading.Semaphore()
results = {}

def init_llm():
    global client, ready_semaphore
    global res_sem, results

    use_cuda = torch.cuda.is_available()
    
    key = open("C:\\Users\\peter\\OneDrive\\Documents\\GeminiAPI.txt", "r").read() # Replace with your key
    client = genai.Client(api_key=key)
    
    ready_semaphore.release()
        


def compute_rating(email, i, UserPreference=""):    
    global client
    
    input = f"""
        Please give an integer rating of 1, 2, 3, 4, or 5 representing how important the following email would be to the user (5 is the most important). Do not output anything else, no explanation is needed.
        Try to reserve 1 for truly useless emails, and 5 for very high priority emails. Emails that could potentially be useful or important to the user should on average receive a 3.
        The user may also provide some details about them that would influence what is or is not important to them.
        Details about the user: {UserPreference}
        
        Email:
        From: {email['from']}
        Subject: {email['subj']}
        
        {email['body']}"""
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=input,
    )
    
    res = response.text[0]
    try:
        res = int(res)
    except:
        res = 0
        print("Error parsing response. Expected integer, got: ", end="")
        print(res)
        print(f"({response.text})")
    
    res_sem.acquire()
    results[i] = res
    res_sem.release()




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


if __name__ == "__main__":
    print("Starting")
    init_llm()
    print("Model loaded")
    
    emails = {}
    with open("sample_emails.json", "r") as f:
        emails = json.load(f)
    emails, user_pref = emails["Emails"], emails["UserPreferences"]
    
    # run test
    total_diff = 0
    for i, email in enumerate(compute_rating_for_all(emails, user_pref)):
        print(f"Rating {i+1}/{len(emails)}: {results[i]} (real: {email['real_rating']})")
        total_diff += abs(results[i] - email["real_rating"])
    print(f"Average difference: {total_diff/len(emails)}")
    print("Done")