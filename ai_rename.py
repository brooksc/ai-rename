#!/usr/bin/env python3
import os
import os
import re
import subprocess

import requests


# Function to perform OCR on the file
def perform_ocr(file_path):
    ocr_text = ""
    if file_path.lower().endswith('.pdf'):
        # Convert PDF to PNG for OCR processing
        image_file = f"{os.path.splitext(file_path)[0]}.png"
        subprocess.run(['pdftoppm', file_path, os.path.splitext(file_path)[0], '-png', '-f', '1', '-singlefile'])
        if os.path.isfile(image_file):
            ocr_text = subprocess.check_output(['tesseract', image_file, '-', '-l', LANGUAGE]).decode('utf-8')
            os.remove(image_file)
    elif file_path.lower().endswith(('.jpg', '.png')):
        ocr_text = subprocess.check_output(['tesseract', file_path, '-', '-l', LANGUAGE]).decode('utf-8')
    return ocr_text.strip()


# Function to generate a filename based on OCR content using AI
def generate_filename(ocr_text):
    payload = {
        "messages": [
            {"role": "system",
             "content": "Generate a suitable filename for the following file content that briefly summarizes the content, using no more than 120 characters."},
            {"role": "user", "content": f"Here is the file content: {ocr_text}"}
        ],
        "temperature": 0,
        "max_tokens": -1,
        "stream": False
    }

    response = requests.post('http://localhost:1234/v1/chat/completions', headers={"Content-Type": "application/json"},
                             data=json.dumps(payload))
    if response.status_code == 200:
        response_json = response.json()
        filename = response_json['choices'][0]['message']['content']
        return filename.strip()
    return None


# Function to clean and validate the generated filename
def clean_filename(filename):
    cleaned_content = re.sub(r'[^a-zA-Z0-9 ]', ' ', filename)
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
    cleaned_content = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned_content)
    content_length = len(cleaned_content)

    if 15 <= content_length <= 100:
        return cleaned_content
    return None


