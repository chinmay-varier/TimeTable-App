import customtkinter as ctk

def after_save(app: ctk.CTk, frame1:ctk.CTkFrame, frame2: ctk.CTkFrame):
    frame1.destroy()
    frame2.destroy()