import dlib
import tkinter as tk
import cv2
import firebase_admin
import requests
from firebase_admin import credentials, db
from uritemplate import expand

cred = credentials.Certificate('girliecam-firebase-adminsdk-no9ee-a4c71905f6.json')
firebase_admin.initialize_app(cred, {"databaseURL": "https://girliecam-default-rtdb.firebaseio.com/"})

ref = db.reference("/")

root = tk.Tk()
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
root.title("Be the best girlie")




# main Frame

main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# pages

camera_page = tk.Frame(main_frame)
editor_page = tk.Frame(main_frame)
gallery_page = tk.Frame(main_frame)
profile_page = tk.Frame(main_frame)

current = 0
pages = [camera_page, editor_page, gallery_page, profile_page]
def next_page():
    global current
    if current < len(pages) -1:
        pages[current].pack_forget()
        pages[current+1].pack()
        current += 1

def previous_page():
    global current
    if current > 0:
        pages[current].pack_forget()
        pages[current - 1].pack()
        current -=1


lbl1 = tk.Label(camera_page, text="CAMERA", font=('Normal', 30))
lbl1.pack()
camera_page.pack(pady=100)


lbl2 = tk.Label(editor_page, text="EDITOR", font=('Normal', 30))
lbl2.pack()


lbl3 = tk.Label(gallery_page, text="GALLERY", font=('Normal', 30))
lbl3.pack()


lbl4 = tk.Label(profile_page, text="PROFILE DATA", font=('Normal', 30))
lbl4.pack()

bottom_frame = tk.Frame(root)

back_btn = tk.Button(bottom_frame, text='Back', font=('Bold', 15), command=previous_page)
back_btn.pack()
forward_btn = tk.Button(bottom_frame, text='Forward', font=('Bold', 15), command=next_page)
forward_btn.pack()

bottom_frame.pack(side = tk.BOTTOM, pady=20)

root.mainloop()