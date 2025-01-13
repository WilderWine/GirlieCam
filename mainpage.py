#from doctest import master
#from logging import exception
#from os import uname, close
import re
import os
import time
import base64
#import dlib
import tkinter as tk
from tkinter import ttk, filedialog
import cv2
import firebase_admin
#import requests
from firebase_admin import credentials, db
#import pyrebase
#from numpy.ma.core import filled, masked
#from pyparsing import alphas
#from uritemplate import expand
from threading import Thread, Lock
from PIL import Image, ImageTk
import numpy as np
from classes import User, Filter, Mask, Sticker

class Gallery:
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(master)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = tk.Scrollbar(self.frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.configure(command=self.canvas.yview)
        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')
        self.images = []
        self.buttons = []
        self.column = 0
        self.row = 0

    def add_image(self, path):
        image = Image.open(path)
        image.thumbnail((400, 300))
        photo = ImageTk.PhotoImage(image)
        button = tk.Button(self.inner_frame, image=photo, command=lambda p=path: self.show_path(p))
        button.image = photo
        pad = 100
        button.grid(column=self.column, row=self.row, padx=pad, pady=10)
        self.images.append(photo)
        self.buttons.append(button)
        self.column += 1
        if self.column == 3:
            self.column = 0
            self.row += 1
        self.inner_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def show_path(self, path):
        global edit_image
        edit_image = path
        set_page(2)

class ScrollablePanel:
    def __init__(self, master, button_command=None):
        self.frame = tk.Frame(master, borderwidth=0,highlightbackground="#090914")
        self.canvas = tk.Canvas(self.frame, height=75, width=350, bg='#090914', borderwidth=0,highlightbackground="#090914")
        self.scrollbar = ttk.Scrollbar(self.frame, orient="horizontal", command=self.canvas.xview,)

        # Используем tk.Frame для scrollable_frame
        self.scrollable_frame = tk.Frame(self.canvas, bg='#090914', borderwidth=0, bd=0, highlightthickness=0, highlightbackground="#090914")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        self.button_command = button_command
        self.canvas.pack(side="top", fill="both", expand=True)
        self.scrollbar.pack(side="bottom", fill="x")
        #self.frame.pack()
        self.frame.pack(padx=0, pady=0)

        self.elements = []

    def add_element(self, image_path, name):
        img = Image.open(image_path)
        img = img.resize((50, 50), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)

        element_frame = tk.Frame(self.scrollable_frame, bg='#090914',  highlightcolor='#090914')
        element_frame.pack(side="left", padx=(0, 20))
        button_command = self.button_command
        button = tk.Button(element_frame, image=photo, command=lambda: button_command(name), bg='#090914', borderwidth=0,  activebackground="#090914",
                     highlightbackground="#090914", bd=0)
        button.image = photo
        button.pack()

        label = tk.Label(element_frame, text=name, bg='#090914', fg='white')
        label.pack()

        self.elements.append((button, label))

    def clear(self):
        i = 0
        for  button, label in self.elements:
            if i > 2:
                button.destroy()
                label.destroy()
            i+=1
        self.elements.clear()

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

class CameraViewer:
    def __init__(self, master):
        self.master = master
        self.cap = None
        self.running = False

        self.middle_frame = tk.Frame(middle_panel, bg="#FF0000")
        self.middle_frame.pack(fill=tk.BOTH, expand=True)

        self.middle_canvas = tk.Canvas(self.middle_frame, width=640, height=480)
        self.middle_canvas.pack(fill=tk.BOTH, expand=True)

        self.lock = None
        self.frame = None
        self.current_img = None
        self.thread = None


    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.lock = Lock()
        self.running = True
        self.thread = Thread(target=self.read_frames)
        self.thread.daemon = True
        self.thread.start()
        self.update_image()

    def stop_camera(self):
        self.running = False
        self.thread = None
        self.lock = None
        self.cap.release()

    def read_frames(self):
        while True:
            ret, frame = self.cap.read()
            with self.lock:
                self.frame = frame

    def update_image(self):
        global current_filter_cam
        global custom_filter
        def apply_filter(fr, index):
            if index == 0:
                return fr
            elif index == 1:
                return cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
            elif index == 2:
                return cv2.convertScaleAbs(fr, beta=-250)
            elif index == -1:
                # custom_filter = {'brightness' : 0, 'contrast': 1, 'gauss_blur': 0, 'saturation': 0, 'sharpness': 0, 'blackwhite': 0}
                brightness = int(custom_filter['brightness'])
                contrast = int(custom_filter['contrast'])
                gauss_blur = int(custom_filter['gauss_blur'])+1
                saturation = float(custom_filter['saturation'])
                sharpness = int(custom_filter['sharpness'])+1
                blackwhite = int(custom_filter['blackwhite'])
                fr = cv2.convertScaleAbs(fr, alpha=contrast, beta=brightness)
                fr = cv2.GaussianBlur(fr, (gauss_blur, gauss_blur), 0)
                hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
                hsv[..., 1] = hsv[..., 1] * saturation
                fr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                kernel1 = np.multiply(kernel, sharpness)
                fr = cv2.filter2D(fr, -1, kernel1)
                if blackwhite == 1:
                    fr = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
                return fr
            else:
                return fr
        with self.lock:
            if self.frame is not None:
                # Convert the image to a format suitable for Tkinter
                frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                frame = apply_filter(frame, current_filter_cam)
                frame_width = self.middle_frame.winfo_width()
                aspect_ratio = frame.shape[1] / frame.shape[0]
                new_width = frame_width
                new_height = int(frame_width / aspect_ratio)

                # Ensure the new width and height are valid
                if new_width > 0 and new_height > 0:

                    # Resize the image
                    frame = cv2.resize(frame, (new_width, new_height))
                    photo = ImageTk.PhotoImage(Image.fromarray(frame))

                    # Display the image on the middle_canvas
                    self.middle_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                    self.middle_canvas.image = photo
                    self.current_img = Image.fromarray(frame)


        self.master.after(33, self.update_image)


cred = credentials.Certificate('girliecam-firebase-adminsdk-no9ee-a4c71905f6.json')
firebase_admin.initialize_app(cred, {"databaseURL": "https://girliecam-default-rtdb.firebaseio.com/"})
#config = {"databaseURL": "https://girliecam-default-rtdb.firebaseio.com/"}

ref = db.reference("/")

def register_user(email: str, password: str):
    def sanitize_email(email):
        return email.replace('.', '_dot_').replace('@', '_at_')
    try:
        email_key = email.lower()
        new_name = email_key.split('@')[0]
        email_key = sanitize_email(email_key)
        user_ref = db.reference(f'users/{email_key}')


        if user_ref.get() is None:
            user_ref.set({
                'name': new_name,
                'password': password,
                'filters': {},
                'stickers': {},
                'masks': {}
            })
            print("Successfully resistered!")
            return True
        else:
            print("User exists!")
            return False
    except Exception as e:
        print(f"Error while register: {e}")
        return False

def login_user(email: str, password: str):
    def sanitize_email(email):
        return email.replace('.', '_dot_').replace('@', '_at_')
    try:
        email_key = email.lower()
        email_key = sanitize_email(email_key)
        user_ref = db.reference(f'users/{email_key}')
        user_data = user_ref.get()
        if user_data is not None:
            if user_data['password'] == password:
                print("Successfully entered!")
                print("Userdata:", user_data)
                return user_data
            else:
                print("Wrong password!")
                return None
        else:
            print("No such user!")
    except Exception as e:
        print(f"Error while login: {e}")
        return None


root = tk.Tk()
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
root.wm_attributes("-alpha", 0)
root.title("Be the best girlie")

# main Frame

main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# pages

camera_page = tk.Frame(main_frame,bg="#FF0000")
editor_page = tk.Frame(main_frame,bg="#FFFF11")
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
no_image = "images/no.png"
negative_image = "images/negative.png"
custom_image = "images/custom.png"
gray_image ="images/gray.png"
red_horror_eye = "images/red_horror.png"
purple_horror_eye = "images/purple_horror.png"
trash_image = "images/trash.png"
smile_image = "images/smile.png"



edit_image = None
current = 0
current_user = None
pages = [login_page, camera_page, editor_page, gallery_page, profile_page]


def base64_to_png(base64_string, output_file_path):
    # Декодирование строки Base64
    image_data = base64.b64decode(base64_string)
    with open(output_file_path, "wb") as image_file:
        # Запись в файл
        image_file.write(image_data)

def png_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        # Чтение изображения в двоичном формате
        image_data = image_file.read()
        # Кодирование в Base64
        base64_string = base64.b64encode(image_data).decode('utf-8')
        return base64_string

def next_page():
    global current
    if current < len(pages) -1:
        set_page(current+1)

def previous_page():
    global current
    if current > 0:
        set_page(current -1)

def on_image_click(event):
    # Получаем координаты клика
    x = event.x
    y = event.y
    print(f"Кликнули на координатах: ({x}, {y})")

def set_page(index: int):
    global current
    global app
    global gallery
    global edit_image

    if  index  ==  4:
        return

    previous = current
    pages[index].pack(fill=tk.BOTH ,expand=True, )
    pages[current].pack_forget()
    current = index

    if index == 1:
        app.start_camera()
    elif previous == 1:
        app.stop_camera()

    if index == 2:
        image = Image.open(edit_image)
        image.thumbnail((1800, 900))
        photo = ImageTk.PhotoImage(image)
        image_label.config(image=photo)
        image_label.image = photo
        image_label.bind("<Button-1>", on_image_click)

    elif previous == 2:
        edit_image = None

    if index == 3:
        gallery_path = os.path.join(os.path.expanduser('~'), 'Gallery')
        if not os.path.exists(gallery_path):
            os.makedirs(gallery_path)

        gallery_files = [os.path.join(os.path.expanduser('~'), 'Gallery') + f"/{f}" for f in os.listdir(gallery_path) if f.endswith('.jpg') or f.endswith('.jpeg')]

        gallery = Gallery(middle_panel_gal)
        for f in gallery_files:
            gallery.add_image(f)
    elif previous == 3:
        if gallery is not  None:
            gallery.frame.pack_forget()
            gallery = None

    if current == 4:
        pass
    elif previous == 4:
        edit_image = None




def open_panel_camera():
    panel_btn.pack_forget()
    close_button.pack(side=tk.RIGHT, padx=30, pady=20)

    side_panel.pack(side=tk.RIGHT, fill=tk.Y)

def close_panel_camera():
    side_panel.pack_forget()
    close_button.pack_forget()
    panel_btn.pack(padx=30, pady=20, side=tk.RIGHT)





def take_photo():
    photo = app.current_img
    gallery_path = os.path.join(os.path.expanduser('~'), 'Gallery')
    if not os.path.exists(gallery_path):
        os.makedirs(gallery_path)

    current_time = int(time.time() * 1000)
    filename = os.path.join(gallery_path, f"img_{current_time}.jpg")
    photo.save(filename, 'JPEG')


def login():
    def is_valid_email(em):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, em) is not None
    global current_user
    email = login_entry_li.get()
    pwd1 = pwd_entry_li.get()
    res = None
    if is_valid_email(email):
        res = login_user(email, pwd1)
        print(res)
    if res is None:
        current_user = None
    else:
        filters = []
        for filter_name, filter_values in res.get('filters', {}).items():
            filters.append(Filter(**filter_values, name=filter_name))

        stickers = []
        for sticker_name, image_code in res.get('stickers', {}).items():
            stickers.append(Sticker(name=sticker_name, img=base64_to_png(image_code)))

        masks = []
        for mask_name, mask_values in res.get('masks', {}).items():
            masks.append(Mask(
                name=mask_name,
                eye_r=base64_to_png(mask_values['eye_r']),
                eye_l=base64_to_png(mask_values['eye_l']),
                nose=base64_to_png(mask_values['nose']),
                mouth=base64_to_png(mask_values['mouth'])
            ))
        current_user = User(name=res['name'], email=email,password=res['password'], filters=filters,
                            stickers=stickers,  masks=masks)
    if current_user is not None:
        user_lbl.config(text=current_user.name)
        user_lbl_gal.config(text=current_user.name)
        save_button_filters.pack(padx=10, side=tk.LEFT)
        save_button_mask.pack(padx=10, side=tk.LEFT)
        save_button_filters_editor.pack(padx=10, side=tk.LEFT)
        save_button_mask_editor.pack(padx=10, side=tk.LEFT)
        save_button_sticker_editor.pack(side=tk.LEFT)
        for f in current_user.filters:
            filters_panel.add_element(custom_image, f.name)

    set_page(1)

def register():
    def is_valid_email(em):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, em) is not None
    email = login_entry_su.get()
    pwd1 = pwd_entry_su.get()
    pwd2 = pwd_entry2_su.get()
    if is_valid_email(email) and pwd1 == pwd2:
        res = register_user(email, pwd1)
        print(res)



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
                             font=("Normal", 20), activebackground="#292a5e", bd=2, fg="white", command=register)
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

def filter_cam_click(filter_name: str):
    global current_filter_cam
    global current_user
    if filter_name == "No filter":
        current_filter_cam = 0
    elif filter_name == "Gray shade":
        current_filter_cam = 1
    elif filter_name == "Negative":
        current_filter_cam = 2
    else:
        if current_user is None:
            return
        for ii,f in enumerate(current_user.filters):
            if f.name == filter_name:
                current_filter_cam = ii+3
                break

current_filter_cam = 0
custom_filter = {'brightness' : 0, 'contrast': 1, 'gauss_blur': 0, 'saturation': 0, 'sharpness': 0, 'blackwhite': 0}

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
                     bd=0, command=take_photo)
take_photo_btn.pack(fill=tk.BOTH)
bottom_panel.pack(padx=0, pady=0, side=tk.BOTTOM, fill=tk.X, )


middle_panel = tk.Frame(camera_page, bg="#00FF00")
middle_panel.pack(padx=0, pady=0, side=tk.LEFT, fill=tk.BOTH, expand=True)

side_panel = tk.Frame(camera_page, bg="#090914", width=400)

filters_label = tk.Label(side_panel, text="Filters:", bg='#090914', fg='white')
filters_label.pack(pady=5)

filters_panel = ScrollablePanel(side_panel, filter_cam_click)
filters_panel.add_element(no_image, "No filter")
filters_panel.add_element(gray_image, "Gray shade")
filters_panel.add_element(negative_image, "Negative")
filters_panel.pack(pady=5)

#custom_filter = {'brightness' : 0, 'contrast': 1, 'gauss_blur': 0, 'saturation': 0, 'sharpness': 0, 'blackwhite': 0}
def update_label(slider_index, value):
    global custom_filter
    if slider_index == 0:
        custom_filter['brightness']=value
    elif slider_index == 1:
        custom_filter['contrast'] = value
    elif slider_index == 2:
        custom_filter['sharpness'] = value
    elif slider_index == 3:
        custom_filter['gauss_blur'] = value
    elif slider_index == 4:
        custom_filter['saturation'] = value
    elif slider_index == 5:
        custom_filter['blackwhite'] = value

def on_button_click():
    values = [slider.get() for slider in sliders]
    print("Значения слайдеров:", values)

def on_checkbutton_change_cam():
    global current_filter_cam
    if use_custom_var_filters.get():
        current_filter_cam = -1
    else:
        current_filter_cam = 0



panel = tk.Frame(side_panel, width=350, bg='#090914')
panel.pack(fill=tk.X, padx=5, pady=10)

checkbox_frame_filters = tk.Frame(panel, bg='#090914')
checkbox_frame_filters.pack(pady=(0, 5))
use_custom_var_filters = tk.IntVar()
checkbox_filters = tk.Checkbutton(checkbox_frame_filters, variable=use_custom_var_filters, bg='#090914', fg='black', bd=0, highlightthickness=0,
                                  command=on_checkbutton_change_cam)
checkbox_filters.pack(side=tk.LEFT)
label_text_filters = tk.Label(checkbox_frame_filters, text="Use Custom", fg='white', bg='#090914')
label_text_filters.pack(padx=10,side=tk.LEFT)
save_button_filters = tk.Button(checkbox_frame_filters, text="Save", command=on_button_click, bg="#090914", fg="white", )

fixed_length = 10

ranges = [
    (-300, 200, 1, 0, 'Brightness'),
    (1, 10, 1, 1, 'Contrast'),
    (-10, 10, 1, 0,'Sharpness'),
    (0, 50, 2, 0, 'Blur'),
    (-5, 5, 0.1, 0,'Saturation'),
    (0, 1, 1, 0, 'B/W'),
]
sliders = []
labels = []

for i, (min_val, max_val, step, val, name) in enumerate(ranges):
    row_frame = tk.Frame(panel, bg='#090914', highlightthickness=0,borderwidth=0, height=350)
    row_frame.pack(fill=tk.X, padx=5, pady=5)
    label1 = tk.Label(row_frame, text=name, width=fixed_length, bg='#090914', fg='white')
    label1.pack(side=tk.LEFT)
    slider = tk.Scale(row_frame, from_=min_val, to=max_val, resolution=step, orient=tk.HORIZONTAL, command=lambda value, index=i: update_label(index, value),
                      bg='#090914', fg='white', bd=0,  highlightthickness=0)
    slider.set(val)
    slider.pack(side=tk.LEFT, padx=5, fill=tk.X)
    sliders.append(slider)



def on_button_click():
    values = [slider.get() for slider in sliders]
    print("Значения слайдеров:", values)

def choose_file(row_index):
    file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    if file_path:
        file_labels_masks[row_index].config(text=file_path)

def clear_file(row_index):
    file_labels_masks[row_index].config(text="")

masks_label = tk.Label(side_panel, text="Masks:", bg='#090914', fg='white')
masks_label.pack(pady=5)  # Отступ 60

masks_panel = ScrollablePanel(side_panel)
masks_panel.add_element(no_image, "No")
masks_panel.add_element(red_horror_eye, "Red Horror")
masks_panel.add_element(purple_horror_eye, "Blue Horror")
masks_panel.add_element(custom_image, "Image 4")
masks_panel.add_element(custom_image, "Image 3")
masks_panel.add_element(custom_image, "Image 4")
masks_panel.pack(pady=5)

# Строка с чекбоксом
use_custom_var_masks = tk.IntVar()
checkbox_frame_masks = tk.Frame(side_panel, bg='#090914')
checkbox_masks = tk.Checkbutton(checkbox_frame_masks, variable=use_custom_var_masks, bg='#090914', fg='black', bd=0, highlightthickness=0)
checkbox_masks.pack(side=tk.LEFT)
checkbox_frame_masks.pack(pady=(0, 10))
label_text = tk.Label(checkbox_frame_masks, text="Use Custom", fg='white', bg='#090914')
label_text.pack(padx=10,side=tk.LEFT)
save_button_mask = tk.Button(checkbox_frame_masks, text="Save", command=on_button_click, bg="#090914", fg="white")

# Фиксированные строки
fixed_names_masks = ['Eye Right', 'Eye Left ', 'Nose      ', 'Mouth    ']
file_labels_masks = []

file_frame_maska = tk.Frame(side_panel, bg='#090914')
file_frame_maska.pack(pady=10)

for name in fixed_names_masks:
    row_frame = tk.Frame(file_frame_maska, bg='#090914')
    row_frame.pack(fill=tk.X, padx=5, pady=2)

    label = tk.Label(row_frame, text=name, width=15, bg='#090914', fg='white')
    label.pack(side=tk.LEFT)

    file_label = tk.Label(row_frame, text="", width=30, bg='#090914', fg='white')
    file_label.pack(side=tk.LEFT)
    file_labels_masks.append(file_label)

    choose_button_mask = tk.Button(row_frame, text="Choose", command=lambda idx=len(file_labels_masks)-1: choose_file(idx), bg="#090914", fg="white")
    choose_button_mask.pack(side=tk.LEFT)

    clear_button_mask = tk.Button(row_frame, text="Clear", command=lambda idx=len(file_labels_masks)-1: clear_file(idx), bg="#090914", fg="white")
    clear_button_mask.pack(side=tk.LEFT)

app = CameraViewer(root)
gallery = None


# gallery

upper_panel_gal = tk.Frame(gallery_page, bg="#090914", height=100)
user_btn_gal = tk.Button(upper_panel_gal, width=60, height=60, bg="#090914", activebackground="#090914",
                     highlightbackground="#090914"  , image=user_image,
                     command=lambda: set_page(4), bd=0)
user_btn_gal.pack(padx=30, pady=20, side=tk.LEFT)
user_lbl_gal = tk.Label(upper_panel_gal, bg="#090914", text="unauthenticated", font=("normal", 20), fg="#FFFFFF")
user_lbl_gal.pack(padx=30, side=tk.LEFT, fill=tk.Y)

upper_panel_gal.pack(padx=0, pady=0, side=tk.TOP, fill=tk.X)

bottom_panel_gal = tk.Frame(gallery_page, bg="#090914", height=100)
camera_btn = tk.Button(bottom_panel_gal, width=60, height=60, bg="#090914", activebackground="#090914",
                     highlightbackground="#090914"  , image=camera_image,
                     command=lambda: set_page(1), bd=0)
camera_btn.pack(padx=30, pady=20, side=tk.LEFT)

bottom_panel_gal.pack(padx=0, pady=0, side=tk.BOTTOM, fill=tk.X, )


middle_panel_gal = tk.Frame(gallery_page, bg="#00FF00")
middle_panel_gal.pack(padx=0, pady=0, side=tk.LEFT, fill=tk.BOTH, expand=True)


# editor

def apply_filter_editor():

    global current_filter_editor
    img = cv2.imread(edit_image)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    if current_filter_editor == 0:
        pass
    elif current_filter_editor == 1:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif current_filter_editor == 2:
        img = cv2.convertScaleAbs(img, beta=-250)
    elif current_filter_editor == -1:
        # custom_filter = {'brightness' : 0, 'contrast': 1, 'gauss_blur': 0, 'saturation': 0, 'sharpness': 0, 'blackwhite': 0}
        brightness = int(custom_filter_editor['brightness'])
        contrast = int(custom_filter_editor['contrast'])
        gauss_blur = int(custom_filter_editor['gauss_blur']) + 1
        saturation = float(custom_filter_editor['saturation'])
        sharpness = int(custom_filter_editor['sharpness']) + 1
        blackwhite = int(custom_filter_editor['blackwhite'])
        img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)
        img = cv2.GaussianBlur(img, (gauss_blur, gauss_blur), 0)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[..., 1] = hsv[..., 1] * saturation
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        kernel1 = np.multiply(kernel, sharpness)
        img = cv2.filter2D(img, -1, kernel1)
        if blackwhite == 1:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    image = Image.fromarray(img)
    image.thumbnail((1800, 900))
    photo = ImageTk.PhotoImage(image)
    image_label.config(image=photo)
    image_label.image = photo
    image_label.bind("<Button-1>", on_image_click)


def filter_edit_click(filter_name: str):
    global current_filter_editor
    global current_user
    if filter_name == "No filter":
        current_filter_editor = 0
    elif filter_name == "Gray shade":
        current_filter_editor = 1
    elif filter_name == "Negative":
        current_filter_editor = 2
    else:
        for ii,f in enumerate(current_user.filters):
            if f.name == filter_name:
                current_filter_editor = ii+3
                break
    apply_filter_editor()

side_panel_edit = tk.Frame(editor_page, bg="#090914", width=400)
side_panel_edit.pack(side=tk.RIGHT, fill=tk.Y)

current_filter_editor = 0
custom_filter_editor = {'brightness' : 0, 'contrast': 1, 'gauss_blur': 0, 'saturation': 0, 'sharpness': 0, 'blackwhite': 0}

filters_label_editor = tk.Label(side_panel_edit, text="Filters:", bg='#090914', fg='white')
filters_label_editor.pack(pady=5)

filters_panel_editor = ScrollablePanel(side_panel_edit, filter_edit_click)
filters_panel_editor.add_element(no_image, "No filter")
filters_panel_editor.add_element(gray_image, "Gray shade")
filters_panel_editor.add_element(negative_image, "Negative")
filters_panel_editor.pack(pady=5)

def update_label_editor(slider_index, value):
    global custom_filter_editor
    if slider_index == 0:
        custom_filter_editor['brightness'] = value
    elif slider_index == 1:
        custom_filter_editor['contrast'] = value
    elif slider_index == 2:
        custom_filter_editor['sharpness'] = value
    elif slider_index == 3:
        custom_filter_editor['gauss_blur'] = value
    elif slider_index == 4:
        custom_filter_editor['saturation'] = value
    elif slider_index == 5:
        custom_filter_editor['blackwhite'] = value
    apply_filter_editor()

def on_button_click_editor():
    values = [slider.get() for slider in sliders_editor]
    print("Значения слайдеров:", values)

def on_checkbutton_change_editor():
    global current_filter_editor
    if use_custom_var_filters_editor.get():
        current_filter_editor = -1
    else:
        current_filter_editor = 0

panel_editor = tk.Frame(side_panel_edit, width=350, bg='#090914')
panel_editor.pack(fill=tk.X, padx=5, pady=10)

checkbox_frame_filters_editor = tk.Frame(panel_editor, bg='#090914')
checkbox_frame_filters_editor.pack(pady=(0, 5))
use_custom_var_filters_editor = tk.IntVar()
checkbox_filters_editor = tk.Checkbutton(checkbox_frame_filters_editor, variable=use_custom_var_filters_editor, bg='#090914', fg='black', bd=0, highlightthickness=0,
                                         command=on_checkbutton_change_editor)
checkbox_filters_editor.pack(side=tk.LEFT)
label_text_filters_editor = tk.Label(checkbox_frame_filters_editor, text="Use Custom", fg='white', bg='#090914')
label_text_filters_editor.pack(padx=10,side=tk.LEFT)
save_button_filters_editor = tk.Button(checkbox_frame_filters_editor, text="Save", command=on_button_click_editor, bg="#090914", fg="white")
fixed_length = 10

sliders_editor = []
labels_editor = []

for i, (min_val, max_val, step, val, name) in enumerate(ranges):
    row_frame_editor = tk.Frame(panel_editor, bg='#090914', highlightthickness=0,borderwidth=0, height=350)
    row_frame_editor.pack(fill=tk.X, padx=5, pady=5)
    label1_editor = tk.Label(row_frame_editor, text=name, width=fixed_length, bg='#090914', fg='white')
    label1_editor.pack(side=tk.LEFT)
    slider_editor = tk.Scale(row_frame_editor, from_=min_val, to=max_val, resolution=step, orient=tk.HORIZONTAL, command=lambda value, index=i: update_label_editor(index, value),
                      bg='#090914', fg='white', bd=0,  highlightthickness=0)
    slider_editor.set(val)
    slider_editor.pack(side=tk.LEFT, padx=5, fill=tk.X)
    sliders_editor.append(slider_editor)



def on_button_click_editor():
    values = [slider.get() for slider in sliders]
    print("Значения слайдеров:", values)

def choose_file_editor(row_index):
    file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    if file_path:
        file_labels_masks_editor[row_index].config(text=file_path)

def clear_file_editor(row_index):
    file_labels_masks_editor[row_index].config(text="")
    
def save_sticker_editor():
    sticker_text = add_sticker_file_label_editor.cget("text")
    print(sticker_text)

def choose_file_sticker_editor():
    file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    if file_path:
        add_sticker_file_label_editor.config(text=file_path)

masks_label_editor = tk.Label(side_panel_edit, text="Masks:", bg='#090914', fg='white')
masks_label_editor.pack(pady=5)  # Отступ 60

masks_panel_editor = ScrollablePanel(side_panel_edit)
masks_panel_editor.add_element(no_image, "No")
masks_panel_editor.add_element(red_horror_eye, "Red Horror")
masks_panel_editor.add_element(purple_horror_eye, "Blue Horror")
masks_panel_editor.add_element(custom_image, "Image 4")
masks_panel_editor.add_element(custom_image, "Image 3")
masks_panel_editor.add_element(custom_image, "Image 4")
masks_panel_editor.pack(pady=5)

# Строка с чекбоксом
use_custom_var_masks_editor = tk.IntVar()
checkbox_frame_masks_editor = tk.Frame(side_panel_edit, bg='#090914')
checkbox_masks_editor = tk.Checkbutton(checkbox_frame_masks_editor, variable=use_custom_var_masks_editor, bg='#090914', fg='black', bd=0, highlightthickness=0)
checkbox_masks_editor.pack(side=tk.LEFT)
checkbox_frame_masks_editor.pack(pady=(0, 10))
label_text_editor = tk.Label(checkbox_frame_masks_editor, text="Use Custom", fg='white', bg='#090914')
label_text_editor.pack(padx=10,side=tk.LEFT)
save_button_mask_editor = tk.Button(checkbox_frame_masks_editor, text="Save", command=on_button_click_editor, bg="#090914", fg="white")

file_labels_masks_editor = []

file_frame_maska_editor = tk.Frame(side_panel_edit, bg='#090914')
file_frame_maska_editor.pack(pady=10)

for name in fixed_names_masks:
    row_frame_editor = tk.Frame(file_frame_maska_editor, bg='#090914')
    row_frame_editor.pack(fill=tk.X, padx=5, pady=2)

    label_editor = tk.Label(row_frame_editor, text=name, width=15, bg='#090914', fg='white')
    label_editor.pack(side=tk.LEFT)

    file_label_editor = tk.Label(row_frame_editor, text="", width=30, bg='#090914', fg='white')
    file_label_editor.pack(side=tk.LEFT)
    file_labels_masks_editor.append(file_label_editor)

    choose_button_mask_editor = tk.Button(row_frame_editor, text="Choose", command=lambda idx=len(file_labels_masks_editor)-1: choose_file_editor(idx), bg="#090914", fg="white")
    choose_button_mask_editor.pack(side=tk.LEFT)

    clear_button_mask_editor = tk.Button(row_frame_editor, text="Clear", command=lambda idx=len(file_labels_masks_editor)-1: clear_file_editor(idx), bg="#090914", fg="white")
    clear_button_mask_editor.pack(side=tk.LEFT)


stickers_label_editor = tk.Label(side_panel_edit, text="Stickers:", bg='#090914', fg='white')
stickers_label_editor.pack(pady=5)

stickers_panel_editor = ScrollablePanel(side_panel_edit)
stickers_panel_editor.add_element(trash_image, "Trash Can")
stickers_panel_editor.add_element(smile_image, "Smile")
stickers_panel_editor.pack(pady=5)

add_sticker_frame_editor = tk.Frame(side_panel_edit, bg='#090914')
add_sticker_frame_editor.pack(fill=tk.X, padx=5, pady=2)

add_sticker_label_editor = tk.Label(add_sticker_frame_editor, text="Image", width=15, bg='#090914', fg='white')
add_sticker_label_editor.pack(side=tk.LEFT)

add_sticker_file_label_editor = tk.Label(add_sticker_frame_editor, text="", width=30, bg='#090914', fg='white')
add_sticker_file_label_editor.pack(side=tk.LEFT)

choose_button_sticker_editor = tk.Button(add_sticker_frame_editor, text="Choose", command=choose_file_sticker_editor, bg="#090914", fg="white")
choose_button_sticker_editor.pack(side=tk.LEFT)

save_button_sticker_editor = tk.Button(add_sticker_frame_editor, text="Clear", command=save_sticker_editor, bg="#090914", fg="white")




upper_panel_edit = tk.Frame(editor_page, bg="#090914", height=100)
back_btn_edit = tk.Button(upper_panel_edit, width=60, height=60, bg="#090914", activebackground="#090914",
                     highlightbackground="#090914"  , image=back_image,
                     command=lambda: set_page(3), bd=0)
back_btn_edit.pack(padx=30, pady=20, side=tk.LEFT)

upper_panel_edit.pack(padx=0, pady=0, side=tk.TOP, fill=tk.X)


middle_panel_edit = tk.Frame(editor_page, bg="#181823")
middle_panel_edit.pack(padx=0, pady=0, side=tk.LEFT, fill=tk.BOTH, expand=True)


image_label = tk.Label(middle_panel_edit, bg="#090914")
image_label.pack(expand=True)



root.mainloop()