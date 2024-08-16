#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import requests
import json
import re
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize argument parser
parser = argparse.ArgumentParser(description='Process files in a directory using OCR and AI to generate filenames.')
parser.add_argument('directory', type=str, help='The directory containing files to process.')
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging.')
parser.add_argument('--keep-original', type=bool, default=True, help='Preserve the original file after renaming. Default is True.')

args = parser.parse_args()

# Configure logging based on debug flag
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

# Configuration variables
LANGUAGE = 'eng'
ORIG_SUBDIR = "orig"

DIR = args.directory
KEEP_ORIGINAL = args.keep_original

# Check if the provided argument is a valid directory
if not os.path.isdir(DIR):
    logging.error(f"The directory '{DIR}' does not exist.")
    sys.exit(1)

# Create a 'done' directory within the provided directory to store processed files
DONE_DIR = os.path.join(DIR, 'done')
os.makedirs(DONE_DIR, exist_ok=True)
ORIG_DIR = os.path.join(DIR, ORIG_SUBDIR)
os.makedirs(ORIG_DIR, exist_ok=True)


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
        try:
            ocr_text = subprocess.check_output(['tesseract', file_path, '-', '-l', LANGUAGE]).decode('utf-8')
        except subprocess.CalledProcessError as e:
            logging.error(f"OCR processing failed for file '{file_path}': {e}")
            return ""
    return ocr_text.strip()


# Function to generate a filename based on OCR content using AI
def generate_filename(ocr_text):
    payload = {
        "messages": [
            {"role": "system",
             "content": "Generate a suitable filename for the following file content that briefly summarizes the content, using no more than 120 characters. Ensure your response is a valid JSON object containing 'filename' and 'justification' fields. Respond only with valid JSON. Do not write an introduction or summary."},
            {"role": "user", "content": f"Here is the file content: {ocr_text}"}
        ],
        "temperature": 0,
        "max_tokens": -1,
        "stream": False
    }

    response = requests.post('http://localhost:1234/v1/chat/completions', headers={"Content-Type": "application/json"},
                             data=json.dumps(payload))
    logging.debug(f"AI service response: {response.text}")
    try:
        response_json = response.json()
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON response: {e}")
        return None
    if response.status_code == 200:
        try:
            ai_response = response_json['choices'][0]['message']['content']
            ai_response = json.loads(ai_response)
            assert isinstance(ai_response, dict), "AI response is not a valid JSON object"
        except (json.JSONDecodeError, AssertionError) as e:
            logging.error(f"Invalid JSON response from AI service: {e}")
            return None
        filename = ai_response.get('filename', '').strip()
        justification = ai_response.get('justification', '')
        return filename, justification
    else:
        logging.error(f"AI service returned non-200 status code: {response.status_code}")
        return None


# Function to clean and validate the generated filename
def clean_filename(filename):
    cleaned_content = re.sub(r'[^a-zA-Z0-9 ]', ' ', filename)
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
    cleaned_content = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned_content)
    content_length = len(cleaned_content)

    # Remove any existing file extension from the cleaned content
    cleaned_content = os.path.splitext(cleaned_content)[0]

    if 15 <= content_length <= 100:
        return cleaned_content
    return None


# Process each file in the directory
for file_name in os.listdir(DIR):
    file_path = os.path.join(DIR, file_name)

    if os.path.isfile(file_path) and file_path.lower().endswith('.pdf'):
        logging.info(f"Processing file: {file_path}")

        logging.info("Starting OCR recognition ...")
        ocr_text = perform_ocr(file_path)

        if ocr_text.strip():
            logging.info("OCR successful")
            logging.debug(f"OCR text: {ocr_text}")
            logging.info("Starting AI request ...")

            ai_generated_filename, justification = generate_filename(ocr_text)
            if ai_generated_filename:
                logging.debug(f"AI generated filename: {ai_generated_filename}")
                logging.debug(f"Justification: {justification}")
                cleaned_filename = clean_filename(ai_generated_filename)
                if cleaned_filename:
                    file_extension = os.path.splitext(file_name)[1]
                    new_filename = f"{cleaned_filename}{file_extension}"
                    new_filepath = os.path.join(DONE_DIR, new_filename)
                    counter = 1
                    while os.path.exists(new_filepath):
                        base_name, ext = os.path.splitext(new_filename)
                        new_filename = f"{base_name}_{counter}{ext}"
                        new_filepath = os.path.join(DONE_DIR, new_filename)
                        counter += 1

                    if KEEP_ORIGINAL:
                        shutil.copy2(file_path, new_filepath)
                        shutil.move(file_path, os.path.join(ORIG_DIR, file_name))
                        logging.info(f"'{file_path}' was successfully renamed to '{new_filepath}' and copied")
                    else:
                        shutil.move(file_path, new_filepath)
                        logging.info(f"'{file_path}' was successfully renamed to '{new_filepath}' and moved")
                else:
                    logging.error("Resulting filename is not between 15 - 100 characters")
            else:
                logging.error("No valid filename could be extracted from the AI response.")
        else:
            logging.error(f"OCR processing of '{file_path}' failed or no text recognized. Keeping original filename.")
            new_filepath = os.path.join(DONE_DIR, file_name)
            if KEEP_ORIGINAL:
                shutil.copy2(file_path, new_filepath)
                shutil.move(file_path, os.path.join(ORIG_DIR, file_name))
                logging.info(f"'{file_path}' was moved to '{new_filepath}' with original filename")
            else:
                shutil.move(file_path, new_filepath)
                logging.info(f"'{file_path}' was moved to '{new_filepath}' with original filename")
import os
import sys
import shutil
import subprocess
import requests
import json
import re

# Color codes for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

LANGUAGE = 'eng'
KEEP_ORIGINAL = 1
ORIG_SUBDIR = "orig"


# Create a 'done' directory within the provided directory to store processed files
DONE_DIR = os.path.join(DIR, 'done')
os.makedirs(DONE_DIR, exist_ok=True)
ORIG_DIR = os.path.join(DIR, ORIG_SUBDIR)
os.makedirs(ORIG_DIR, exist_ok=True)


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


# Process each file in the directory
for file_name in os.listdir(DIR):
    file_path = os.path.join(DIR, file_name)

    if os.path.isfile(file_path) and file_path.lower().endswith(('.pdf', '.jpg', '.png')):
        print(f"{BLUE}{file_path}{NC}")

        print(f"{YELLOW}Starting OCR recognition ...{NC}")
        ocr_text = perform_ocr(file_path)

        if ocr_text:
            print(f"{GREEN}OCR successful{NC}")
            print(f"{YELLOW}Starting AI request ...{NC}")

            ai_generated_filename = generate_filename(ocr_text)
            if ai_generated_filename:
                cleaned_filename = clean_filename(ai_generated_filename)
                if cleaned_filename:
                    file_extension = os.path.splitext(file_name)[1]
                    new_filename = f"{cleaned_filename}{file_extension}"
                    new_filepath = os.path.join(DONE_DIR, new_filename)

                    if KEEP_ORIGINAL:
                        shutil.copy2(file_path, new_filepath)
                        shutil.move(file_path, os.path.join(ORIG_DIR, file_name))
                        print(f"{GREEN}'{file_path}' was successfully renamed to '{new_filepath}' and copied{NC}")
                    else:
                        shutil.move(file_path, new_filepath)
                        print(f"{GREEN}'{file_path}' was successfully renamed to '{new_filepath}' and moved{NC}")
                else:
                    print(f"{RED}Resulting filename is not between 15 - 100 characters{NC}")
            else:
                print(f"{RED}No valid filename could be extracted from the AI response.{NC}")
        else:
            print(f"{RED}OCR processing of '{file_path}' failed or no text recognized.{NC}")
