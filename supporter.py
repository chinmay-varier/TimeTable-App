import cv2
import pytesseract
import json
import customtkinter as ctk
from tkinter import messagebox
import os
from manipulator import afterSave

def analysis(file_path):
    img = cv2.imread(file_path)


    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    """cv2.imshow('i', gray)
    cv2.waitKey(0)
    cv2.destroyAllWindows()"""
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                cv2.THRESH_BINARY, 15, 10)
    """cv2.imshow('i', thresh)
    cv2.waitKey(0)
    cv2.destroyAllWindows()"""


    ocrR = pytesseract.image_to_string(thresh, config='--psm 6')

    lines = [line.strip() for line in ocrR.split('\n') if line.strip()]
    colVal = []

    for line in lines:
        if not line.lower().startswith('c.'):
            if line.startswith('I') or line.startswith('|'):
                line = line[1:]
            
            if len(line) > 2:
                abcd = line[:2]
                rest = line[2:]
                
                def lCorrecter(s):
                    if len(s) == 0:
                        return s
                    
                    replaced = ''.join('1' if (c == 'L' and i != len(s) - 1) else c for i, c in enumerate(s))
                    return replaced
                
                rest = rest.replace('I', '1').replace('l', '1').replace('S', '8').replace('i', '1').replace('&', '8')
                rest_fixed = lCorrecter(rest)
                corrected_line = abcd + rest_fixed
            else:
                corrected_line = line

            colVal.append(corrected_line)

    with open("details.json", "w") as f:
        data = [{'key':i, "value": ""} for i in colVal]
        json.dump(data,f)

def after_select(frame: ctk.CTkFrame, app: ctk.CTk):
    frame.destroy()
    json_path = "details.json"

    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
        except json.JSONDecodeError:
            json_data = []
    else:
        json_data = []



    scrollFrame = ctk.CTkScrollableFrame(app, width=460, height=580)
    scrollFrame.pack(padx=20, pady=20, fill="both", expand=True)

    entry_widgets = []

    def addEntry(key="", value=""):
        key_entry = ctk.CTkTextbox(scrollFrame, width=250, height=45)
        key_entry.insert("1.0", key)
        key_entry.pack(pady=5)

        value_box = ctk.CTkTextbox(scrollFrame, width=600, height=55)
        value_box.insert("1.0", value)
        value_box.pack(pady=5)
        entry_widgets.append((key_entry, value_box))

    def render_entries():
        for k, v in entry_widgets:
            k.destroy()
            v.destroy()
        entry_widgets.clear()
        for item in json_data:
            addEntry(item.get("key", ""), item.get("value", ""))

    def addNew():
        addEntry()

    def saveData():
        data2 = []
        keys = set()
        for k_entry, v_box in entry_widgets:
            k = k_entry.get("1.0", "end-1c").strip()
            v = v_box.get("1.0", "end-1c").strip()
            if k:
                if k in keys:
                    messagebox.showerror("Duplicate keys detected!")
                    return
                keys.add(k)
                json_data.append({'key':k ,'value': v})
                data2.append({'key':k ,'value': v})
        with open(json_path, "w", encoding="utf-8") as f:
            if len(json_data) > 9:    json.dump(data2, f)
            else: json.dump(json_data,f)
        messagebox.showinfo("Saved", "JSON file updated successfully.")
        afterSave(app, scrollFrame)

    btn_add = ctk.CTkButton(app, text="Add New Courses", command=addNew)
    btn_add.pack(side="left", padx=15, pady=10)

    btn_save = ctk.CTkButton(app, text="Save Changes", command=saveData)
    btn_save.pack(side="right", padx=15, pady=10)

    render_entries()

    win2 = ctk.CTkToplevel(app)
    win2.title("Instructions")
    from PIL import Image
    img = ctk.CTkImage(light_image=Image.open("img/select2.png"), dark_image=Image.open("img/select2.png"), size=(1000,480))
    imglbl = ctk.CTkLabel(win2, text="", image=img)
    imglbl.pack()
    win2.geometry("1100x500")