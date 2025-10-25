import customtkinter as ctk
import json
from PIL import Image
from test import replaceValuesAsync


def after_save(app: ctk.CTk, frame1: ctk.CTkFrame):
    """Called when save button is clicked. Processes image with OCR in background."""
    
    # File paths
    image_path = "image.png"
    json_path = "details.json"
    output_path = "modified_timetable.jpg"
    
    # Create progress window
    progress_window = ctk.CTkToplevel(app)
    progress_window.title("Processing Timetable")
    progress_window.geometry("400x150")
    progress_window.resizable(False, False)
    
    # Center the window
    progress_window.transient(app)
    progress_window.grab_set()
    
    # Progress label
    status_label = ctk.CTkLabel(
        progress_window, 
        text="Starting OCR processing...",
        font=("Arial", 14)
    )
    status_label.pack(pady=20)
    
    # Progress bar
    progress_bar = ctk.CTkProgressBar(progress_window, width=350)
    progress_bar.pack(pady=10)
    progress_bar.set(0)
    
    # Percentage label
    percent_label = ctk.CTkLabel(progress_window, text="0%")
    percent_label.pack(pady=5)
    
    def update_progress(percentage):
        """Update progress bar and label safely from any thread"""
        try:
            app.after(0, lambda: progress_bar.set(percentage / 100))
            app.after(0, lambda: percent_label.configure(text=f"{percentage}%"))
            
            # Update status messages based on progress
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
    
    def on_complete(modified_img, replacements, error):
        """Called when OCR processing completes"""
        try:
            # Close progress window
            progress_window.destroy()
        except:
            pass
        
        if error:
            # Show error dialog
            error_window = ctk.CTkToplevel(app)
            error_window.title("Error")
            error_window.geometry("400x150")
            
            error_label = ctk.CTkLabel(
                error_window, 
                text=f"Error during processing:\n{error}",
                text_color="red"
            )
            error_label.pack(pady=20)
            
            ok_button = ctk.CTkButton(
                error_window, 
                text="OK", 
                command=error_window.destroy
            )
            ok_button.pack(pady=10)
            return
        
        # Success! Show results
        success_window = ctk.CTkToplevel(app)
        success_window.title("Success")
        success_window.geometry("400x200")
        
        num_replacements = len(replacements) if replacements else 0
        
        success_label = ctk.CTkLabel(
            success_window,
            text=f"✓ Processing Complete!\n\n{num_replacements} replacements made",
            font=("Arial", 16),
            text_color="green"
        )
        success_label.pack(pady=20)
        
        # Show some replacement details
        if replacements and len(replacements) > 0:
            try:
                details_text = "Replacements:\n"
                pattern_counts = {}
                
                for rep in replacements[:10]:  # Show first 10
                    try:
                        pattern = rep.get('pattern', rep.get('matched_pattern', 'Unknown'))
                        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                    except:
                        continue
                
                for pattern, count in pattern_counts.items():
                    details_text += f"  {pattern}: {count} instances\n"
                
                details_label = ctk.CTkLabel(
                    success_window,
                    text=details_text,
                    font=("Arial", 12)
                )
                details_label.pack(pady=10)
            except:
                pass
        
        close_button = ctk.CTkButton(
            success_window,
            text="Close",
            command=success_window.destroy
        )
        close_button.pack(pady=10)
        
        # Optional: Display the modified image
        try:
            display_modified_image(app, output_path)
        except Exception as e:
            print(f"Could not display image: {e}")
    
    # Start async OCR processing (non-blocking)
    try:
        replaceValuesAsync(
            image_path=image_path,
            json_path=json_path,
            output_path=output_path,
            callback=on_complete,
            progress_callback=update_progress
        )
    except Exception as e:
        progress_window.destroy()
        
        error_window = ctk.CTkToplevel(app)
        error_window.title("Error")
        error_window.geometry("400x150")
        
        error_label = ctk.CTkLabel(
            error_window, 
            text=f"Failed to start processing:\n{str(e)}",
            text_color="red"
        )
        error_label.pack(pady=20)
        
        ok_button = ctk.CTkButton(
            error_window, 
            text="OK", 
            command=error_window.destroy
        )
        ok_button.pack(pady=10)


def display_modified_image(app, image_path):
    """Display the modified timetable image in a new window"""
    
    img_window = ctk.CTkToplevel(app)
    img_window.title("Modified Timetable")
    
    # Load image
    pil_image = Image.open(image_path)
    
    # Resize if too large
    max_width, max_height = 1200, 800
    if pil_image.width > max_width or pil_image.height > max_height:
        pil_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    
    img_window.geometry(f"{pil_image.width + 40}x{pil_image.height + 40}")
    
    # Convert to CTkImage
    ctk_image = ctk.CTkImage(
        light_image=pil_image,
        dark_image=pil_image,
        size=(pil_image.width, pil_image.height)
    )
    
    # Display in label
    image_label = ctk.CTkLabel(img_window, image=ctk_image, text="")
    image_label.pack(padx=20, pady=20)
    
    # Keep reference to prevent garbage collection
    image_label.image = ctk_image


def prepare_json_for_ocr():
    """Prepare JSON file format for OCR processing."""
    try:
        with open("details.json", "r") as f:
            data = json.load(f)
        
        new_data = []
        for item in data:
            # If value is a string, split by comma
            if isinstance(item.get("value"), str):
                new_data.append({
                    "key": item["key"],
                    "value": [v.strip() for v in item["value"].split(",") if v.strip()]
                })
            # If already a list, keep as is
            elif isinstance(item.get("value"), list):
                new_data.append(item)
        
        # Save formatted JSON
        with open("details.json", "w") as f:
            json.dump(new_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error preparing JSON: {e}")
        return False


# Example usage in your main app
if __name__ == "__main__":
    
    # Main application window
    app = ctk.CTk()
    app.title("Timetable Editor")
    app.geometry("1340x720")
    app.resizable(width=False, height=False)
    
    # Main frame
    main_frame = ctk.CTkFrame(master=app, width=1320, height=700)
    main_frame.pack(pady=10)
    
    # Title
    title_label = ctk.CTkLabel(
        main_frame,
        text="Timetable OCR Editor",
        font=("Arial", 24, "bold")
    )
    title_label.pack(pady=20)
    
    # Instructions
    instructions = ctk.CTkLabel(
        main_frame,
        text="Click 'Process Timetable' to start OCR replacement",
        font=("Arial", 14)
    )
    instructions.pack(pady=10)
    
    # Save/Process button
    save_button = ctk.CTkButton(
        main_frame,
        text="Process Timetable",
        font=("Arial", 16),
        width=200,
        height=50,
        command=lambda: after_save(app, main_frame)
    )
    save_button.pack(pady=30)
    
    # Prepare JSON button
    prepare_button = ctk.CTkButton(
        main_frame,
        text="Prepare JSON File",
        font=("Arial", 14),
        width=200,
        command=prepare_json_for_ocr
    )
    prepare_button.pack(pady=10)
    
    # Status label
    status_label = ctk.CTkLabel(
        main_frame,
        text="Ready",
        font=("Arial", 12),
        text_color="gray"
    )
    status_label.pack(pady=10)
    
    app.mainloop()
