
import json
import re

def prune(text):
    # deletes non-8-bit-ASCII characters from the text, like emojis or strange fonts
    encoded = text.encode("ascii", "ignore")
    decoded = encoded.decode("ascii")
    return decoded

def main():
    with open ("sample_emails.json", "r") as f:
        emails = json.load(f)

    with open("email_to_add.txt", "r", errors='ignore') as f:
        new_email = f.read()
    
    new_email = new_email.split("\n")
    new_email = {
        "subj": prune(new_email[1]),
        "from": prune(new_email[0]),
        "body": prune("\n".join(new_email[2:]))
    }
    
    emails["Emails"].append(new_email)
    
    print("Total emails: ", len(emails["Emails"]))
    
    with open("sample_emails.json", "w") as f:
        json.dump(emails, f, indent=4)
    

if __name__ == "__main__":
    main()
