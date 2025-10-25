import cv2
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import json

def load_replacement_mapping(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    pattern_map = {}
    for item in data:
        for val in item['value']:
            if val:
                pattern_map[val] = item['key']
    return pattern_map

def normalize_text(text):
    text_upper = text.upper()
    result = list(text_upper)
    
    replacements = {'L': '1', '|': '1', '!': '1'}
    for i in range(len(result)):
        if i > 0 and result[i] in replacements:
            result[i] = replacements[result[i]]
        if i == 0 and result[i] in replacements and len(result) > 1 and result[1].isdigit():
            result[i] = replacements[result[i]]
    
    normalized = ''.join(result)
    
    if len(normalized) == 2 and normalized[1].isdigit() and normalized[0] in ['1', 'L', '|', '!']:
        normalized = 'I' + normalized[1]
    
    special_cases = {'13': 'I3', 'L3': 'I3', '|3': 'I3', '!3': 'I3', 
                     'I8': 'I3', 'IB': 'I3', 'IE': 'I3', '18': 'I3'}
    return special_cases.get(normalized, normalized)

def matches_pattern(text, pattern):
    text_normalized = normalize_text(text)
    pattern_upper = pattern.upper()
    if text_normalized == pattern_upper:
        return True
    if text_normalized.startswith(pattern_upper) and len(text_normalized) > len(pattern_upper):
        return text_normalized[len(pattern_upper):].isdigit()
    return False

def replace_values(image_path, json_path, output_path='output.png'):
    pattern_map = load_replacement_mapping(json_path)
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Preprocessing methods
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    _, inverted = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    inverted = cv2.bitwise_not(inverted)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    images_to_try = [gray, thresh, adaptive, inverted, enhanced]
    all_detections = {}
    
    for processed_img in images_to_try:
        for psm in [6, 11, 3, 7, 8]:
            for whitelist in ['', ' -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789Il|!']:
                try:
                    config = f'--psm {psm} --oem 3{whitelist}'
                    ocr_data = pytesseract.image_to_data(processed_img, config=config, 
                                                        output_type=pytesseract.Output.DICT)
                    
                    for i in range(len(ocr_data['text'])):
                        text = ocr_data['text'][i].strip()
                        conf = int(ocr_data['conf'][i])
                        if text and conf >= 10:
                            x, y = ocr_data['left'][i], ocr_data['top'][i]
                            w, h = ocr_data['width'][i], ocr_data['height'][i]
                            pos_key = (round(x/10)*10, round(y/10)*10)
                            if pos_key not in all_detections or conf > all_detections[pos_key]['conf']:
                                all_detections[pos_key] = {'text': text, 'conf': conf, 
                                                          'x': x, 'y': y, 'w': w, 'h': h}
                except:
                    continue
    
    # Perform replacements
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_modified = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(img_modified)
    
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except:
            font = ImageFont.load_default()
    
    replaced_positions = set()
    
    for detection in all_detections.values():
        text = detection['text']
        x, y, w, h = detection['x'], detection['y'], detection['w'], detection['h']
        position_tuple = (round(x/5)*5, round(y/5)*5)
        
        if position_tuple in replaced_positions:
            continue
        
        replacement_value = None
        for pattern, replacement in pattern_map.items():
            if matches_pattern(text, pattern):
                replacement_value = replacement
                break
        
        if replacement_value:
            x, y = max(0, x - 2), max(0, y - 2)
            w, h = w + 4, h + 4
            draw.rectangle([x, y, x + w, y + h], fill='white', outline='white')
            
            bbox = draw.textbbox((0, 0), str(replacement_value), font=font)
            text_x = x + (w - (bbox[2] - bbox[0])) // 2
            text_y = y + (h - (bbox[3] - bbox[1])) // 2
            draw.text((text_x, text_y), str(replacement_value), fill='#0000FF', font=font)
            
            replaced_positions.add(position_tuple)
    
    img_modified.save(output_path, quality=95)
    return img_modified

# Usage
if __name__ == "__main__":
    replace_values("image.png", "details.json", "modified_timetable.jpg")
