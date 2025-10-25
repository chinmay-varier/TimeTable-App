import customtkinter as ctk
import json
from test import replace_values

def after_save(app: ctk.CTk, frame1:ctk.CTkFrame):
    app.quit()
    replace_values("image.png", "details.json", "modified_timetable.jpg")
    App = ctk.CTk()
    App.title("Time Table")
    App.geometry("1340x720")
    App.resizable(width=False, height=False)
    frame = ctk.CTkFrame(master=App, width=1320, height=700)
    frame.pack()
    new_dat = []
    with open("details.json", "r+") as f:
        data = json.load(f)
    
    for item in data:
        new_dat.append({"key": item["key"], "value": item["value"].split(",")})

    with open("details.json", "w") as f:
        json.dump(new_dat, f)
    print(new_dat)

    

    App.mainloop()