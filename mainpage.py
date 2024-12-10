from doctest import master
from os import uname, close

import dlib
import tkinter as tk
import cv2
import firebase_admin
import requests
from firebase_admin import credentials, db
from numpy.ma.core import filled, masked
from pyparsing import alphas
from uritemplate import expand

cred = credentials.Certificate('girliecam-firebase-adminsdk-no9ee-a4c71905f6.json')
firebase_admin.initialize_app(cred, {"databaseURL": "https://girliecam-default-rtdb.firebaseio.com/"})

ref = db.reference("/")

root = tk.Tk()
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
root.wm_attributes("-alpha", 0)
root.title("Be the best girlie")

# main Frame

main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# pages

camera_page = tk.Frame(main_frame,bg="#FF0000")
editor_page = tk.Frame(main_frame,bg="#FFFF00")
gallery_page = tk.Frame(main_frame,bg="#FF00FF")
profile_page = tk.Frame(main_frame,bg="#00FFFF")
login_page = tk.Frame(main_frame, bg="#090914")

user_image = tk.PhotoImage(file="images/user.png")
user_image_auth = tk.PhotoImage(file="images/user_auth.png")
add24_image = tk.PhotoImage(file="images/add24.png")
add48_image = tk.PhotoImage(file="images/add48.png")
back_image = tk.PhotoImage(file="images/back.png")
camera_image = tk.PhotoImage(file="images/camera.png")
close_image = tk.PhotoImage(file="images/close.png")
gallery_image = tk.PhotoImage(file="images/gallery.png")
more_image = tk.PhotoImage(file="images/more.png")
photo_image = tk.PhotoImage(file="images/photo.png")
photo96_image = tk.PhotoImage(file="images/photo96.png")

current = 0
pages = [login_page, camera_page, editor_page, gallery_page, profile_page]
def next_page():
    global current
    if current < len(pages) -1:
        set_page(current+1)

def previous_page():
    global current
    if current > 0:
        set_page(current -1)

def set_page(index: int):
    global current
    pages[index].pack(fill=tk.BOTH ,expand=True, )
    pages[current].pack_forget()
    current = index

def open_panel_camera():
    panel_btn.pack_forget()
    close_button.pack(side=tk.RIGHT, padx=30, pady=20)
    side_panel.pack(side=tk.RIGHT, fill=tk.Y)

def close_panel_camera():
    side_panel.pack_forget()
    close_button.pack_forget()
    panel_btn.pack(padx=30, pady=20, side=tk.RIGHT)


def login():
    set_page(1)

def switch_login_mode():
    global login_mode
    if login_mode == 'login':
        login_mode = 'signup'
        signup_panel.pack(expand=True)
        login_panel.pack_forget()
    elif login_mode == 'signup':
        login_mode = 'login'
        login_panel.pack(expand=True)
        signup_panel.pack_forget()


# login

login_mode = 'login'

login_page.pack(fill=tk.BOTH, expand=True)


login_panel = tk.Frame(login_page, bg="#292a5e", width=root.winfo_screenwidth() // 2, height=root.winfo_screenheight() // 2)
login_panel.pack_propagate(0)
login_panel.pack(expand=True)

button_frame = tk.Frame(login_panel, bg="#292a5e")
button_frame.pack(side=tk.BOTTOM, pady=20)
login_button = tk.Button(button_frame, bg="#292a5e", width=15, height=1, text="Log In", highlightcolor="#292a5e", highlightbackground="#090914",
                         font=("Normal", 20), activebackground="#383a82", bd=2, fg="white", command=login)
login_button.pack(side=tk.LEFT, padx=10)

signup_button_li = tk.Button(button_frame, bg="#292a5e", width=15, height=1, text="Sign Up", highlightcolor="#292a5e", highlightbackground="#292a5e",
                             font=("Normal", 20), activebackground="#292a5e", bd=0, fg="white", command=switch_login_mode)
signup_button_li.pack(side=tk.LEFT, padx=10)

info_label_li = tk.Label(login_panel, text="Log in to your profile", fg="#FFFFFF", font=("Normal", 25), bg="#292a5e")
info_label_li.pack(side=tk.TOP, pady=50)
entry_panel_li = tk.Frame(login_panel, bg="#292a5e")
entry_panel_li.pack(side=tk.BOTTOM, pady=30)
login_entry_li = tk.Entry(entry_panel_li, bg="#d0d1f5", fg="#090914", font=("Normal", 25), width=30)
login_entry_li.pack(side=tk.TOP)
pwd_entry_li = tk.Entry(entry_panel_li, bg="#d0d1f5", fg="#090914", font=("Normal", 25), show="*", width=30)
pwd_entry_li.pack(side=tk.TOP, pady=50)
angry_label_li = tk.Label(entry_panel_li, text="", fg="#fc6d95", font=("Normal", 15), bg="#292a5e")
angry_label_li.pack(side=tk.TOP, anchor=tk.SW)


signup_panel = tk.Frame(login_page, bg="#292a5e", width=root.winfo_screenwidth() // 2, height=root.winfo_screenheight() // 2)
signup_panel.pack_propagate(0)
#signup_panel.pack(expand=True)

button_frame_su = tk.Frame(signup_panel, bg="#292a5e")
button_frame_su.pack(side=tk.BOTTOM, pady=50)
login_button_su = tk.Button(button_frame_su, bg="#292a5e", width=15, height=1, text="Log In", highlightcolor="#292a5e", highlightbackground="#292a5e",
                         font=("Normal", 20), activebackground="#383a82", bd=0, fg="white", command=switch_login_mode)
login_button_su.pack(side=tk.LEFT, padx=10)

signup_button = tk.Button(button_frame_su, bg="#292a5e", width=15, height=1, text="Sign Up", highlightcolor="#292a5e", highlightbackground="#090914",
                             font=("Normal", 20), activebackground="#292a5e", bd=2, fg="white", command=login)
signup_button.pack(side=tk.LEFT, padx=10)

info_label_su = tk.Label(signup_panel, text="Create your profile", fg="#FFFFFF", font=("Normal", 25), bg="#292a5e")
info_label_su.pack(side=tk.TOP, pady=50)
entry_panel_su = tk.Frame(signup_panel, bg="#292a5e")
entry_panel_su.pack(side=tk.BOTTOM, pady=30)
login_entry_su = tk.Entry(entry_panel_su, bg="#d0d1f5", fg="#090914", font=("Normal", 25), width=30, )
login_entry_su.pack(side=tk.TOP)
pwd_entry_su = tk.Entry(entry_panel_su, bg="#d0d1f5", fg="#090914", font=("Normal", 25), show="*", width=30)
pwd_entry_su.pack(side=tk.TOP, pady=10)
pwd_entry2_su = tk.Entry(entry_panel_su, bg="#d0d1f5", fg="#090914", font=("Normal", 25), show="*", width=30)
pwd_entry2_su.pack(side=tk.TOP)
angry_label_su = tk.Label(entry_panel_su, text="", fg="#fc6d95", font=("Normal", 15), bg="#292a5e")
angry_label_su.pack(side=tk.TOP, anchor=tk.SW, pady=10)

# camera


upper_panel = tk.Frame(camera_page, bg="#090914", height=100)
user_btn = tk.Button(upper_panel, width=60, height=60, bg="#090914", activebackground="#090914",
                     highlightbackground="#090914"  , image=user_image,
                     command=lambda: set_page(4), bd=0)
user_btn.pack(padx=30, pady=20, side=tk.LEFT)
user_lbl = tk.Label(upper_panel, bg="#090914", text="unauthenticated", font=("normal", 20), fg="#FFFFFF")
user_lbl.pack(padx=30, side=tk.LEFT, fill=tk.Y)
panel_btn = tk.Button(upper_panel, width=60, height=60, bg="#090914", activebackground="#090914",
                     highlightbackground="#090914"  , image=more_image, bd=0,
                     command=open_panel_camera)
panel_btn.pack(padx=30, pady=20, side=tk.RIGHT)
close_button = tk.Button(upper_panel, width=50, height=50, bg="#090914", activebackground="#090914",
                         highlightbackground="#090914", image=close_image, bd=0,
                         command=close_panel_camera)
upper_panel.pack(padx=0, pady=0, side=tk.TOP, fill=tk.X)

bottom_panel = tk.Frame(camera_page, bg="#090914", height=100)
gallery_btn = tk.Button(bottom_panel, width=60, height=60, bg="#090914", activebackground="#090914",
                     highlightbackground="#090914"  , image=gallery_image,
                     command=lambda: set_page(3), bd=0)
gallery_btn.pack(padx=30, pady=20, side=tk.LEFT)
take_photo_btn = tk.Button(bottom_panel, width=90, height=90, bg="#090914", activebackground="#090914",
                     highlightbackground="#090914"  , image=photo96_image,
                     bd=0)
take_photo_btn.pack(fill=tk.BOTH)
bottom_panel.pack(padx=0, pady=0, side=tk.BOTTOM, fill=tk.X, )

side_panel = tk.Frame(camera_page, bg="#090914", width=400)
side_panel.pack_propagate(0)





'''
bottom_frame = tk.Frame(root)

back_btn = tk.Button(bottom_frame, text='Back', font=('Bold', 15), command=previous_page)
back_btn.pack()
forward_btn = tk.Button(bottom_frame, text='Forward', font=('Bold', 15), command=next_page)
forward_btn.pack()

bottom_frame.pack(side = tk.BOTTOM, pady=20)
'''
root.mainloop()