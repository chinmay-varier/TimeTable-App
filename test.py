import cv2
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import json
from pathlib import Path
import threading


def load_replacement_mapping(json_path):
    """Load JSON - handles both list and comma-separated string values."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    pattern_map = {}
    for item in data:
        key = str(item.get('key', ''))
        values = item.get('value', [])
        
        if isinstance(values, str):
            values = [v.strip() for v in values.split(',') if v.strip()]
        
        if isinstance(values, list):
            for v in values:
                if v:
                    v_clean = str(v).upper().strip()
                    pattern_map[v_clean] = key
    
    return pattern_map


def normalize_for_pattern(text, pattern):
    """Smart normalization based on what pattern we're looking for."""
    if not text or not pattern:
        return text.upper().strip() if text else ""
    
    text_upper = str(text).upper().strip().replace(' ', '').replace('.', '')
    pattern_upper = str(pattern).upper().strip()
    
    # Special case: I3 pattern
    if pattern_upper == "I3":
        # Convert common I3 misreads
        if len(text_upper) == 2 and text_upper[1] == '3':
            if text_upper[0] in ['1', 'L', '|', '!']:
                return 'I3'
        # OCR reads 3 as 8, B, or E
        i3_map = {'13': 'I3', 'L3': 'I3', '|3': 'I3', '!3': 'I3',
                 'I8': 'I3', 'IB': 'I3', 'IE': 'I3', '18': 'I3', 'L8': 'I3'}
        if text_upper in i3_map:
            return 'I3'
    
    # Special case: F1 pattern
    elif pattern_upper == "F1":
        if len(text_upper) == 2 and text_upper[0] == 'F':
            if text_upper[1] in ['L', 'l', '|', '!', 'I']:
                return 'F1'
        f1_map = {'FL': 'F1', 'F|': 'F1', 'F!': 'F1', 'FI': 'F1'}
        if text_upper in f1_map:
            return 'F1'
    
    # For all other patterns: standard normalization
    # Convert O to 0
    text_upper = text_upper.replace('O', '0')
    
    # For 2-character patterns, convert L/l/|/! to 1 at position 1
    if len(text_upper) == 2:
        if text_upper[1] in ['L', 'l', '|', '!']:
            text_upper = text_upper[0] + '1'
    
    return text_upper


def matches_pattern(text, pattern):
    """Match text against pattern with smart normalization."""
    text_upper = str(text).upper().strip()
    pattern_upper = str(pattern).upper().strip()
    
    # Direct exact match first
    if text_upper == pattern_upper:
        return True
    
    # Try pattern-specific normalization
    text_norm = normalize_for_pattern(text_upper, pattern_upper)
    if text_norm == pattern_upper:
        return True
    
    # Pattern + digits (B matches B1, B2, B3, etc.)
    if text_norm.startswith(pattern_upper):
        rest = text_norm[len(pattern_upper):]
        if rest and rest.isdigit():
            return True
    
    return False


def replace_text_in_cells(image_path, json_path, output_path='output.png'):
    """OCR replacement with pattern-specific normalization."""
    
    # Validate paths
    image_path = Path(str(image_path).strip('"')).resolve()
    json_path = Path(str(json_path).strip('"')).resolve()
    output_path = Path(str(output_path).strip('"')).resolve()
    
    if not image_path.exists() or not json_path.exists():
        raise FileNotFoundError("Files not found")
    
    # Load patterns
    pattern_map = load_replacement_mapping(json_path)
    
    # Read image
    img = cv2.imread(str(image_path))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    img_out = pil_img.copy()
    draw = ImageDraw.Draw(img_out)
    
    # Font
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
    
    # Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, binary_low = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)
    
    images_to_try = [binary, adaptive, denoised, binary_low]
    
    replacements = []
    processed = set()
    all_detections = {}
    
    # Multiple OCR passes
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
                    
                    # Low threshold for 2-char, higher for longer
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
    
    # Process detections
    for pos, det in all_detections.items():
        try:
            text_orig = str(det['text'])
            x, y, w, h = det['x'], det['y'], det['w'], det['h']
            
            check_pos = (x // 10 * 10, y // 10 * 10)
            if check_pos in processed:
                continue
            
            # Find replacement
            replacement = None
            matched_pattern = None
            
            # Try each pattern
            for pattern, repl in pattern_map.items():
                if matches_pattern(text_orig, pattern):
                    replacement = repl
                    matched_pattern = pattern
                    break
            
            if replacement and matched_pattern:
                # Draw white box
                pad = 8
                draw.rectangle(
                    [x-pad, y-pad, x+w+pad, y+h+pad],
                    fill='white', outline=None
                )
                
                # Center text
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
    
    # Save
    img_out.save(str(output_path), quality=95)
    
    return img_out, replacements


# Aliases
replace_values_fixed = replace_text_in_cells


# Async
def replace_values_async(image_path, json_path, output_path='output.png',
                        tesseract_cmd=None, callback=None, progress_callback=None):
    """Async wrapper."""
    
    def run():
        try:
            if progress_callback:
                progress_callback(50)
            
            img, reps = replace_text_in_cells(image_path, json_path, output_path)
            
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


if __name__ == "__main__":
    try:
        img, reps = replace_text_in_cells("image.png", "details.json", "output.jpg")
        print(f"✓ Success! Made {len(reps)} replacements:")
        for r in reps[:30]:
            print(f"  '{r['original']}' → '{r['replacement']}' (pattern: {r['pattern']})")
    except Exception as e:
        print(f"✗ Error: {e}")
