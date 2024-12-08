import dlib
import tkinter as tk
import cv2
import firebase_admin
import requests
from firebase_admin import credentials, db


cred = credentials.Certificate('girliecam-firebase-adminsdk-no9ee-a4c71905f6.json')
firebase_admin.initialize_app(cred, {"databaseURL": "https://girliecam-default-rtdb.firebaseio.com/"})

ref = db.reference("/")
print(ref.get())
db.reference("/item").set({})
db.reference("/item/item1").set([1,3,3])
print(ref.get())
db.reference("/item").delete()
print(ref.get())