import customtkinter as ctk
import json
from PIL import Image
from test import replaceValuesAsync
from API import main1


def afterSave(app: ctk.CTk, frame1: ctk.CTkFrame):
    main1.main()
    
    image_path = "image.png"
    json_path = "details.json"
    output_path = "modified_timetable.jpg"
    
    pwin = ctk.CTkToplevel(app)
    pwin.title("Processing Timetable")
    pwin.geometry("400x150")
    pwin.resizable(False, False)
    
    pwin.transient(app)
    pwin.grab_set()
    
    status_label = ctk.CTkLabel(
        pwin, 
        text="Starting OCR processing...",
        font=("Arial", 14)
    )
    status_label.pack(pady=20)
    
    pbar = ctk.CTkProgressBar(pwin, width=350)
    pbar.pack(pady=10)
    pbar.set(0)
    
    perce = ctk.CTkLabel(pwin, text="0%")
    perce.pack(pady=5)
    
    def upProg(percentage):
        try:
            app.after(0, lambda: pbar.set(percentage / 100))
            app.after(0, lambda: perce.configure(text=f"{percentage}%"))
            
            if percentage < 20:
                app.after(0, lambda: status_label.configure(text="Loading image and JSON..."))
            elif percentage < 70:
                app.after(0, lambda: status_label.configure(text="Running OCR detection..."))
            elif percentage < 90:
                app.after(0, lambda: status_label.configure(text="Replacing values..."))
            else:
                app.after(0, lambda: status_label.configure(text="Saving output..."))
        except:
            pass
    
    def onComp(modified_img, replacements, error):
        try:
            pwin.destroy()
        except:
            pass
        
        if error:
            errwin = ctk.CTkToplevel(app)
            errwin.title("Error")
            errwin.geometry("400x150")
            
            error_label = ctk.CTkLabel(
                errwin, 
                text=f"Error during processing:\n{error}",
                text_color="red"
            )
            error_label.pack(pady=20)
            
            ok_button = ctk.CTkButton(
                errwin, 
                text="OK", 
                command=errwin.destroy
            )
            ok_button.pack(pady=10)
            return
        
        suwin = ctk.CTkToplevel(app)
        suwin.title("Success")
        suwin.geometry("400x200")
        
        numrep = len(replacements) if replacements else 0
        
        sulabel = ctk.CTkLabel(
            suwin,
            text=f"✓ Processing Complete!\n\n{numrep} replacements made",
            font=("Arial", 16),
            text_color="green"
        )
        sulabel.pack(pady=20)
        
        if replacements and len(replacements) > 0:
            try:
                dettext = "Replacements:\n"
                counts = {}
                
                for rep in replacements[:10]:
                    try:
                        pattern = rep.get('pattern', rep.get('matched_pattern', 'Unknown'))
                        counts[pattern] = counts.get(pattern, 0) + 1
                    except:
                        continue
                
                for pattern, count in counts.items():
                    dettext += f"  {pattern}: {count} instances\n"
                
                delabel = ctk.CTkLabel(
                    suwin,
                    text=dettext,
                    font=("Arial", 12)
                )
                delabel.pack(pady=10)
            except:
                pass
        
        cbutt = ctk.CTkButton(
            suwin,
            text="Close",
            command=suwin.destroy
        )
        cbutt.pack(pady=10)
        
        try:
            display_modified_image(app, output_path)
        except Exception as e:
            print(f"Could not display image: {e}")
    
    try:
        replaceValuesAsync(
            image_path=image_path,
            json_path=json_path,
            output_path=output_path,
            callback=onComp,
            progress_callback=upProg
        )
    except Exception as e:
        pwin.destroy()
        
        errwin = ctk.CTkToplevel(app)
        errwin.title("Error")
        errwin.geometry("400x150")
        
        error_label = ctk.CTkLabel(
            errwin, 
            text=f"Failed to start processing:\n{str(e)}",
            text_color="red"
        )
        error_label.pack(pady=20)
        
        ok_button = ctk.CTkButton(
            errwin, 
            text="OK", 
            command=errwin.destroy
        )
        ok_button.pack(pady=10)


def display_modified_image(app, image_path):
    img_window = ctk.CTkToplevel(app)
    img_window.title("Modified Timetable")
    
    pil_image = Image.open(image_path)
    
    max_width, max_height = 1200, 800
    if pil_image.width > max_width or pil_image.height > max_height:
        pil_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    
    img_window.geometry(f"{pil_image.width + 40}x{pil_image.height + 40}")
    
    ctk_image = ctk.CTkImage(
        light_image=pil_image,
        dark_image=pil_image,
        size=(pil_image.width, pil_image.height)
    )
    
    image_label = ctk.CTkLabel(img_window, image=ctk_image, text="")
    image_label.pack(padx=20, pady=20)
    
    image_label.image = ctk_image


def prepare_json_for_ocr():
    try:
        with open("details.json", "r") as f:
            data = json.load(f)
        
        new_data = []
        for item in data:
            if isinstance(item.get("value"), str):
                new_data.append({
                    "key": item["key"],
                    "value": [v.strip() for v in item["value"].split(",") if v.strip()]
                })
            elif isinstance(item.get("value"), list):
                new_data.append(item)
        
        with open("details.json", "w") as f:
            json.dump(new_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error preparing JSON: {e}")
        return False


if __name__ == "__main__":
    app = ctk.CTk()
    app.title("Timetable Editor")
    app.geometry("1340x720")
    app.resizable(width=False, height=False)
    
    main_frame = ctk.CTkFrame(master=app, width=1320, height=700)
    main_frame.pack(pady=10)
    
    title_label = ctk.CTkLabel(
        main_frame,
        text="Timetable OCR Editor",
        font=("Arial", 24, "bold")
    )
    title_label.pack(pady=20)
    
    instructions = ctk.CTkLabel(
        main_frame,
        text="Click 'Process Timetable' to start OCR replacement",
        font=("Arial", 14)
    )
    instructions.pack(pady=10)
    
    save_button = ctk.CTkButton(
        main_frame,
        text="Process Timetable",
        font=("Arial", 16),
        width=200,
        height=50,
        command=lambda: afterSave(app, main_frame)
    )
    save_button.pack(pady=30)
    
    prepare_button = ctk.CTkButton(
        main_frame,
        text="Prepare JSON File",
        font=("Arial", 14),
        width=200,
        command=prepare_json_for_ocr
    )
    prepare_button.pack(pady=10)
    
    status_label = ctk.CTkLabel(
        main_frame,
        text="Ready",
        font=("Arial", 12),
        text_color="gray"
    )
    status_label.pack(pady=10)
    
    app.mainloop()
