
import tkinter as tk
import sys
import requests
import json
import webbrowser
import threading
import time
from PIL import Image, ImageTk

from oauth2_handler import get_token
from oauth2_handler import getPermissionURL

from AI_handler import init_llm
from AI_handler import compute_rating_for_all

BGcolor = "#D8D8FF"

rating_results = {}

rating_icon_images = {}

def gather_results(emails, user_pref=""):
    global rating_results
    curr = 0
    for res in compute_rating_for_all(emails, user_pref):
        rating_results[curr] = res
        curr += 1

old_tokens = {
    'client_id': "627669641558-cefnkbjml4lnl9qc0glgf2j6qm7nvrnh.apps.googleusercontent.com",
    'client_secret': "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",
}

new_tokens = {
    'client_id': "627669641558-55fp69l23tiu3vhu5q533gbph8kcaq08.apps.googleusercontent.com",
    'client_secret': "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",
}

def is_linux():
    return sys.platform.startswith('linux')


def setup(root):
    if is_linux():
        root.attributes('-zoomed', True) # Set the window to full screen
    else: 
        root.state("zoomed") # Same but for not linux
        
    root.title("Email Sorter")
    root.configure(bg=BGcolor) # Set the background color to a light gray
    
    def deselect_input(event):
        if event.widget == root:
            root.focus_set()
    
    root.bind("<Button-1>", deselect_input) # Deselect the input field when clicking outside of it
    
    global rating_icon_images
    rating_icon_images = {
        "InProgress1": ImageTk.PhotoImage(Image.open("rating_icons/InProgress1.png")),
        "InProgress2": ImageTk.PhotoImage(Image.open("rating_icons/InProgress2.png")),
        "InProgress3": ImageTk.PhotoImage(Image.open("rating_icons/InProgress3.png")),
        "1": ImageTk.PhotoImage(Image.open("rating_icons/None.png")),
        "2": ImageTk.PhotoImage(Image.open("rating_icons/Low.png")),
        "3": ImageTk.PhotoImage(Image.open("rating_icons/Normal.png")),
        "4": ImageTk.PhotoImage(Image.open("rating_icons/High.png")),
        "5": ImageTk.PhotoImage(Image.open("rating_icons/Urgent.png")),
    }


def get_emails(token):
    emails = {}
    with open("sample_emails.json", "r") as f:
        emails = json.load(f)
    return emails["Emails"], emails["UserPreferences"]
    
    # TODO: update to google
    return requests.get(
        "https://graph.microsoft.com/v1.0/me/mailfolders/inbox/messages",
        headers={"Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json"}
    ).json()


def main_screen(root, token, email="example@gmail.com"):
    global rating_results, rating_icon_images
    
    root.update_idletasks() # Update the window size before placing elements
    
    spacing = 8
    top_spacing = 50
    
    
    main_elements = {}
    label = tk.Label(root, text=f"Signed in as {email}", font=("Helvetica", 16),bg=BGcolor)
    label.pack(pady=10)
    main_elements["label"] = label
    
    emails, user_pref = get_emails(token) # Call the function to get emails
    
    # send off a thread to start running the AI
    threading.Thread(target=gather_results, args=(emails, user_pref)).start()
    
    
    # email display + inner elements
    mail_display_frame = tk.Frame(root, bg="white")
    mail_display_frame.place(
        x=root.winfo_width()*0.4,
        y=top_spacing,
        width=root.winfo_width()*0.6 - spacing,
        height=root.winfo_height() - spacing - top_spacing,
    )
    main_elements["mail_display_frame"] = mail_display_frame
    
    mail_display_scrollbar = tk.Scrollbar(mail_display_frame, orient="vertical")
    mail_display_scrollbar.pack(side="right", fill="y")
    main_elements["mail_display_scrollbar"] = mail_display_frame
    
    mail_display_meta = tk.Frame(mail_display_frame, bg=BGcolor, bd=1, relief="solid")
    mail_display_meta.pack(fill="x", padx=5, pady=5)
    main_elements["mail_display_meta"] = mail_display_meta
    
    mail_display_meta.update()
    
    mail_display_meta_from = tk.Label(mail_display_meta, text="From: ...", font=("Helvetica", 16), bg=BGcolor, anchor="w", justify="left", wraplength=mail_display_meta.winfo_width()-20)
    mail_display_meta_from.pack(side="top", fill="x", padx=5, pady=2)
    main_elements["mail_display_meta_from"] = mail_display_meta_from
    
    mail_display_meta_subj = tk.Label(mail_display_meta, text="Subject: ...", font=("Helvetica", 16), bg=BGcolor, anchor="w", justify="left", wraplength=mail_display_meta.winfo_width()-20)
    mail_display_meta_subj.pack(side="top", fill="x", padx=5, pady=2)
    main_elements["mail_display_meta_subj"] = mail_display_meta_subj
    
    mail_display_body_frame = tk.Frame(mail_display_frame, bg=BGcolor, bd=1, relief="solid")
    mail_display_body_frame.pack(fill="both", expand=True, padx=5, pady=5)
    main_elements["mail_display_body_frame"] = mail_display_body_frame
    
    mail_display_body_frame.update()
    
    mail_display_body = tk.Label(mail_display_body_frame, text="Select an email", font=("Helvetica", 12), bg=BGcolor, justify="left", wraplength=mail_display_body_frame.winfo_width()-20)
    mail_display_body.pack(side="top", fill="both", expand=True, padx=5, pady=5)
    main_elements["mail_display_body"] = mail_display_body
    
    def display_email(email):
        # This function will be called when the email is clicked
        mail_display_meta_from.config(text=f"From: {email['from']}")
        mail_display_meta_subj.config(text=f"Subject: {email['subj']}")
        mail_display_body.config(text=email["body"], anchor="nw")

    
    
    # email scrollable list + inner elements
    mail_list_frame = tk.Frame(root, bg=BGcolor)
    mail_list_frame.place(
        x=spacing,
        y=top_spacing,
        width=root.winfo_width()*0.4 - spacing*2,
        height=root.winfo_height() - spacing - top_spacing,
    )
    main_elements["mail_list_frame"] = mail_list_frame
    
    mail_list_scrollbar = tk.Scrollbar(mail_list_frame, orient="vertical")
    mail_list_scrollbar.pack(side="right", fill="y")
    main_elements["mail_list_scrollbar"] = mail_list_scrollbar
    
    mail_list = tk.Canvas(mail_list_frame, yscrollcommand=mail_list_scrollbar.set)
    mail_list.pack(side="left", fill="both", expand=True)
    main_elements["mail_list"] = mail_list
    
    mail_list_scrollbar.config(command=mail_list.yview)
    
    for i, email in enumerate(emails):
        email_frame = tk.Frame(mail_list, bg=BGcolor, bd=1, relief="solid")
        email_frame.pack(fill="x", padx=5, pady=5)
        main_elements["email_frame" + str(i)] = email_frame
        
        email_frame.update()
        
        email_rating_icon = tk.Label(email_frame, image=rating_icon_images["InProgress3"], anchor="ne", justify="right", borderwidth=0)
        email_rating_icon.pack(side="right", padx=5, pady=2)
        main_elements["email_rating_icon" + str(i)] = email_rating_icon
        
        email_from_label = tk.Label(
            email_frame,
            text=f"From: {email["from"]}",
            font=("Helvetica", 12),
            bg=BGcolor,
            justify="left",
            anchor = "w",
            wraplength=email_frame.winfo_width()-60
        )
        email_from_label.pack(side="top", fill="x", padx=5, pady=2)
        main_elements["email_from_label" + str(i)] = email_from_label
        
        email_subj_label = tk.Label(
            email_frame,
            text=email["subj"],
            font=("Helvetica", 16),
            bg=BGcolor,
            justify="left",
            anchor="w",
            wraplength=email_frame.winfo_width()-60
        )
        email_subj_label.pack(side="top", fill="x", padx=5, pady=2)
        main_elements["email_subj_label" + str(i)] = email_subj_label
    
        # make the frame respons when clicked 
        email_frame.bind("<Button-1>", lambda event, email_literal=email: display_email(email_literal))
    
        # Bind the click event to child widgets and propagate to the parent
        email_from_label.bind("<Button-1>", lambda event: event.widget.master.event_generate("<Button-1>"))
        email_subj_label.bind("<Button-1>", lambda event: event.widget.master.event_generate("<Button-1>"))
    
    
    
    # update ratings as they are computed
    def update_rating_icons():
        global rating_results, rating_icon_images
        emails_updated = 0
        clock = 0
        while emails_updated < len(emails):
            if emails_updated in rating_results:
                rating = rating_results[emails_updated]
                email_rating_icon = main_elements["email_rating_icon" + str(emails_updated)]
                email_rating_icon.config(image=rating_icon_images[str(rating)])
                email_rating_icon.image = rating_icon_images[str(rating)]
                emails_updated += 1
                
            clock += 1
            loading_image = None
            if clock % 3 == 0:
                loading_image = rating_icon_images["InProgress1"]
            elif clock % 3 == 1:
                loading_image = rating_icon_images["InProgress2"]
            elif clock % 3 == 2:
                loading_image = rating_icon_images["InProgress3"]
            for i in range(emails_updated, len(emails)):
                email_rating_icon = main_elements["email_rating_icon" + str(i)]
                email_rating_icon.config(image=loading_image)
                email_rating_icon.image = loading_image
            
            time.sleep(0.2)
                
    threading.Thread(target=update_rating_icons).start()
        

def token_screen(root, email):
    token_elements = {}
    emaillabel = tk.Label(root, text=f"Signing into {email}", font=("Helvetica", 32), bg=BGcolor)
    emaillabel.pack(pady=20)
    token_elements["emaillabel"] = emaillabel
    
    label = tk.Label(root, text="Please enter the authorization code here: ", font=("Helvetica", 48), bg=BGcolor)
    label.pack(pady=20)
    token_elements["label"] = label

    code_input = tk.Entry(root, font=("Helvetica", 36), )
    code_input.pack(pady=10)
    token_elements["code_input"] = code_input
    
    def finish_signin(root, email):
        code = code_input.get()
        # This function will be called when the button is clicked
        access_token, refresh_token, expires_in = get_token(new_tokens['client_id'], new_tokens['client_secret'], code)
        token = access_token
        if not token:
            print("Failed to retrieve token.")
            exit(-1)
            
        close_menu(token_elements)
        main_screen(root, token, email)
    
    def back_to_login():
        close_menu(token_elements)
        login_screen(root)

    button = tk.Button(root, text="Continue", command=lambda: finish_signin(root, email), font=("Helvetica", 36))
    button.pack(pady=10)
    token_elements["button"] = button
    
    backbutton = tk.Button(root, text="Back", command=back_to_login, font=("Helvetica", 28))
    backbutton.pack(pady=20)
    token_elements["backbutton"] = backbutton


def login_screen(root):
    login_elements = {}
    label = tk.Label(root, text="Welcome to the\nEmail Sorter!", font=("Helvetica", 48), bg=BGcolor)
    label.pack(pady=20)
    login_elements["label"] = label

    def prompt_signin():
        site = getPermissionURL(new_tokens['client_id'])
        webbrowser.open(site, new=1, autoraise=True)
        token_screen(root, email_input.get())
        close_menu(login_elements)
        
    hint_text = "example@gmail.com"
    
    def on_entry_click(event):
        if email_input.get() == hint_text:
            email_input.delete(0, tk.END)
            email_input.config(fg='black')

    def on_focus_out(event):
        if email_input.get() == '':
            email_input.insert(0, hint_text)
            email_input.config(fg='grey')

    email_input = tk.Entry(root, font=("Helvetica", 36), fg="gray")
    email_input.insert(0, hint_text)
    email_input.bind('<FocusIn>', on_entry_click)
    email_input.bind('<FocusOut>', on_focus_out)
    email_input.pack(pady=10)
    login_elements["email_input"] = email_input

    button = tk.Button(root, text="Login with Google", command=prompt_signin, font=("Helvetica", 36))
    button.pack(pady=10)
    login_elements["button"] = button


def close_menu(elements):
    for key, item in elements.items():
        item.destroy()


def main():
    root = tk.Tk()
    setup(root)
    
    threading.Thread(target=init_llm).start() # load the LLM using a separate thread

    # login_screen(root)
    main_screen(root, 1)
    root.mainloop()

if (__name__ == "__main__"):
    main()