import customtkinter as ctk
from tkinter import filedialog, messagebox
from supporter import analysis, after_select
from PIL import Image

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

App = ctk.CTk()
App.title("App")
App.geometry("1340x720")
App.resizable(width=False, height=False)
frame = ctk.CTkFrame(master=App, width=1320, height=700)
frame.pack()

def process_image(image_path):
    messagebox.showinfo("Image Selected", f"Image file selected:\n{image_path}")

def open_image():
    file_path = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
    )
    if file_path:
        analysis(file_path=file_path)
        after_select(frame,App)

title = ctk.CTkLabel(frame, text="Select The Image with the Course List", width=400, height=60, font=ctk.CTkFont(family="Arial", size=50, weight="bold"))
title.place(relx=0.5, rely=0.13, anchor="center")

img = ctk.CTkImage(light_image=Image.open("C:/Users/chinm/Desktop/TimeTable/img/select1.png"), dark_image=Image.open("C:/Users/chinm/Desktop/TimeTable/img/select1.png"), size=(1000,480))
lbl = ctk.CTkLabel(frame, text="", image=img, corner_radius=20)
lbl.place(relx=0.5,rely=0.52, anchor="center")



btn_open = ctk.CTkButton(frame, text="Open Image", command=open_image, height=40, width=300)
btn_open.place(relx=0.5, rely=0.9, anchor="center")

App.mainloop()
