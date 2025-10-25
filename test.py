import cv2
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import json
from pathlib import Path
import threading


def loadReplacementMapping(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    patrnMap = {}
    for item in data:
        key = str(item.get('key', ''))
        values = item.get('value', [])
        
        if isinstance(values, str):
            values = [v.strip() for v in values.split(',') if v.strip()]
        
        if isinstance(values, list):
            for v in values:
                if v:
                    v_clean = str(v).upper().strip()
                    patrnMap[v_clean] = key
    
    return patrnMap


def normalizeForPattern(text, pattern):
    if not text or not pattern:
        return text.upper().strip() if text else ""
    
    txtU = str(text).upper().strip().replace(' ', '').replace('.', '')
    ptrnU = str(pattern).upper().strip()
 
    if ptrnU == "I3":
        if len(txtU) == 2 and txtU[1] == '3':
            if txtU[0] in ['1', 'L', '|', '!']:
                return 'I3'
        i3_map = {'13': 'I3', 'L3': 'I3', '|3': 'I3', '!3': 'I3',
                 'I8': 'I3', 'IB': 'I3', 'IE': 'I3', '18': 'I3', 'L8': 'I3'}
        if txtU in i3_map:
            return 'I3'
    
    elif ptrnU == "F1":
        if len(txtU) == 2 and txtU[0] == 'F':
            if txtU[1] in ['L', 'l', '|', '!', 'I']:
                return 'F1'
        f1_map = {'FL': 'F1', 'F|': 'F1', 'F!': 'F1', 'FI': 'F1'}
        if txtU in f1_map:
            return 'F1'
    
    elif ptrnU == "E1":
        if len(txtU) == 2 and txtU[0] == 'E':
            if txtU[1] in ['L', 'l', '|', '!', 'I']:
                return 'E1'
        e1_map = {'EL': 'E1', 'E|': 'E1', 'E!': 'E1', 'EI': 'E1'}
        if txtU in e1_map:
            return 'E1'
  
    txtU = txtU.replace('O', '0')
    

    if len(txtU) == 2:
        if txtU[1] in ['L', 'l', '|', '!', 'I']:
            txtU = txtU[0] + '1'
    
    return txtU


def matchesPattern(text, pattern):
    txtU = str(text).upper().strip()
    ptrnU = str(pattern).upper().strip()
    

    if txtU == ptrnU:
        return True
    

    text_norm = normalizeForPattern(txtU, ptrnU)
    if text_norm == ptrnU:
        return True
    

    if text_norm.startswith(ptrnU):
        rest = text_norm[len(ptrnU):]
        if rest and rest.isdigit():
            return True
    
    return False


def replacetxtCells(image_path, json_path, output_path='output.png'):
    

    image_path = Path(str(image_path).strip('"')).resolve()
    json_path = Path(str(json_path).strip('"')).resolve()
    output_path = Path(str(output_path).strip('"')).resolve()
    
    if not image_path.exists() or not json_path.exists():
        raise FileNotFoundError("Files not found")
    

    patrnMap = loadReplacementMapping(json_path)
    

    patterns_sorted = sorted(patrnMap.items(), key=lambda x: len(x[0]), reverse=True)
    

    img = cv2.imread(str(image_path))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    imgo = pil_img.copy()
    draw = ImageDraw.Draw(imgo)
    
 
    font = None
    for fp in ["arial.ttf", "C:/Windows/Fonts/arial.ttf", "/Windows/Fonts/arial.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        try:
            font = ImageFont.truetype(fp, 18)
            break
        except:
            pass
    if not font:
        font = ImageFont.load_default()
    

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, blow = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)
    
    images_to_try = [binary, adaptive, denoised, blow]
    
    replacements = []
    processed = set()
    all_detections = {}
    

    for img_proc in images_to_try:
        for psm in [6, 11, 3, 8, 10, 7]:
            try:
                ocr_data = pytesseract.image_to_data(
                    img_proc,
                    config=f'--psm {psm} --oem 3',
                    output_type=pytesseract.Output.DICT
                )
                
                for i in range(len(ocr_data.get('text', []))):
                    text = str(ocr_data['text'][i]).strip()
                    if not text:
                        continue
                    
                    try:
                        conf = int(ocr_data['conf'][i])
                    except:
                        conf = 0
                    
                    min_conf = 10 if len(text) <= 2 else 25
                    if conf < min_conf:
                        continue
                    
                    x = int(ocr_data['left'][i])
                    y = int(ocr_data['top'][i])
                    w = int(ocr_data['width'][i])
                    h = int(ocr_data['height'][i])
                    
                    pos = (x // 15 * 15, y // 15 * 15)
                    
                    if pos not in all_detections or conf > all_detections[pos]['conf']:
                        all_detections[pos] = {
                            'text': text, 'conf': conf,
                            'x': x, 'y': y, 'w': w, 'h': h
                        }
            except:
                continue
    

    for pos, det in all_detections.items():
        try:
            text_orig = str(det['text'])
            x, y, w, h = det['x'], det['y'], det['w'], det['h']
            
            check_pos = (x // 10 * 10, y // 10 * 10)
            if check_pos in processed:
                continue
            

            replacement = None
            matched_pattern = None
            
            for pattern, repl in patterns_sorted:
                if matchesPattern(text_orig, pattern):
                    replacement = repl
                    matched_pattern = pattern
                    break
            
            if replacement and matched_pattern:

                pad = 8
                draw.rectangle(
                    [x-pad, y-pad, x+w+pad, y+h+pad],
                    fill='white', outline=None
                )
                

                bbox = draw.textbbox((0, 0), replacement, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                tx = x + (w - tw) // 2
                ty = y + (h - th) // 2
                
                draw.text((tx, ty), replacement, fill='#0000FF', font=font)
                
                processed.add(check_pos)
                replacements.append({
                    'original': text_orig,
                    'replacement': replacement,
                    'pattern': matched_pattern
                })
        except:
            continue
    

    imgo.save(str(output_path), quality=95)
    
    return imgo, replacements



replace_values_fixed = replacetxtCells



def replaceValuesAsync(image_path, json_path, output_path='output.png',
                        tesseract_cmd=None, callback=None, progress_callback=None):

    
    def run():
        try:
            if progress_callback:
                progress_callback(50)
            
            img, reps = replacetxtCells(image_path, json_path, output_path)
            
            if progress_callback:
                progress_callback(100)
            
            if callback:
                callback(img, reps, None)
        except Exception as e:
            if callback:
                callback(None, None, str(e))
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

