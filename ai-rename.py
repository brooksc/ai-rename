#!/usr/bin/env python3

import os
import sys
import yaml
import shutil
import logging
import argparse
import subprocess
import progressbar
import litellm
import re
from typing import Dict, Any
import tempfile
import requests
import json
# from pathlib import Path

def handle_exception(operation: str, exception: Exception) -> None:
    """
    Handle exceptions and log appropriate error messages.

    Args:
        operation (str): The operation during which the exception occurred.
        exception (Exception): The exception that was raised.
    """
    if isinstance(exception, FileNotFoundError):
        logging.error(f"File not found during {operation}: {str(exception)}")
    elif isinstance(exception, PermissionError):
        logging.error(f"Permission denied during {operation}: {str(exception)}")
    elif isinstance(exception, IOError):
        logging.error(f"I/O error occurred during {operation}: {str(exception)}")
    elif isinstance(exception, subprocess.CalledProcessError):
        logging.error(f"Subprocess error during {operation}: {str(exception)}")
    elif isinstance(exception, requests.RequestException):
        logging.error(f"Network error during {operation}: {str(exception)}")
    elif isinstance(exception, json.JSONDecodeError):
        logging.error(f"JSON decoding error during {operation}: {str(exception)}")
    else:
        logging.error(f"Unexpected error during {operation}: {str(exception)}")

def check_command_exists(command: str) -> bool:
    """
    Check if a command exists in the system's PATH.

    Args:
        command (str): The command to check.

    Returns:
        bool: True if the command exists, False otherwise.
    """
    try:
        subprocess.run([command, '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def check_required_commands() -> None:
    """
    Check if all required commands are installed.

    Exits the script if any required command is missing.
    """
    required_commands = ['magick', 'mogrify', 'tesseract']
    missing_commands = [cmd for cmd in required_commands if not check_command_exists(cmd)]

    if missing_commands:
        logging.error(f"The following required commands are not installed: {', '.join(missing_commands)}")
        logging.error("Please install these commands before running the script.")
        sys.exit(1)

class FileProcessor:
    def __init__(self, config: Dict[str, Any], args: argparse.Namespace):
        self.config = config
        self.args = args
        self.extension_to_function = {'.pdf': self.process_pdf, '.jpg': self.process_image, '.png': self.process_image}
        check_required_commands()
        self.temp_dir = tempfile.TemporaryDirectory(prefix='ai_rename_')
        self.ai_rename_dir = self.temp_dir.name
        self.create_directory(self.ai_rename_dir)
        if self.args.debug:
            logging.debug(f"Temporary directory created: {self.ai_rename_dir}")
        # else:
        #     self.temp_dir.cleanup()
        # Set default value for keep_original if not provided
        self.args.keep_original = getattr(self.args, 'keep_original', True)
    def cleanup(self):
        self.temp_dir.cleanup()

    def setup_directories(self, base_dir: str) -> Dict[str, str]:
        done_dir = os.path.join(base_dir, 'done')
        orig_dir = os.path.join(base_dir, self.config.get('ORIG_SUBDIR', 'orig'))
        if self.args.rename or self.args.move:
            self.create_directory(done_dir)
            self.create_directory(orig_dir)
        return {'DONE_DIR': done_dir if self.args.rename or self.args.move else None, 'ORIG_DIR': orig_dir if self.args.rename or self.args.move else None}

    def create_directory(self, dir_path: str) -> None:
        try:
            os.makedirs(dir_path, exist_ok=True)
            logging.info(f"Directory '{dir_path}' created.")
        except Exception as e:
            handle_exception("directory creation", e)
            sys.exit(1)

    def process_files(self, dir_path: str) -> None:
        for root, dirs, files in os.walk(dir_path):
            dirs = self.setup_directories(root)
            total_files = sum(1 for file in files if file.lower().endswith(('.pdf', '.jpg', '.png')))

            if self.args.progress_bar and total_files > 0:
                bar = self.setup_progress_bar(total_files)
            else:
                bar = None

            for file_count, file_name in enumerate(files):
                self.process_single_file(root, file_name, dirs, file_count, bar)

            if bar:
                bar.finish()

            if self.args.dry_run:
                logging.info("Dry run completed. No files were renamed.")

    def count_files(self, dir_path: str) -> int:
        return sum(1 for file_name in os.listdir(dir_path)
                   if os.path.isfile(os.path.join(dir_path, file_name))
                   and file_name.lower().endswith(('.pdf', '.jpg', '.png')))

    def setup_progress_bar(self, total_files: int) -> progressbar.ProgressBar:
        return progressbar.ProgressBar(maxval=total_files,
                                       widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])

    def process_single_file(self, dir_path: str, file_name: str, dirs: Dict[str, str],
                            file_count: int, bar: progressbar.ProgressBar) -> None:
        if (dirs['DONE_DIR'] is None or dirs['ORIG_DIR'] is None) and (self.args.rename or self.args.move):
            logging.error("Required directories not initialized.")
            return

        file_path = os.path.join(dir_path, file_name)
        file_extension = os.path.splitext(file_name)[1].lower()

        if os.path.isfile(file_path) and file_extension in self.extension_to_function:
            self.process_file(file_path, file_name, self.extension_to_function[file_extension], dirs)

        if bar:
            bar.update(file_count + 1)

    def process_file(self, file_path: str, file_name: str, process_func: callable, dirs: Dict[str, str]) -> None:
        if self.args.debug:
            logging.debug(f"Processing file: {file_path}")

        try:
            process_func(file_path, file_name, dirs['DONE_DIR'], dirs['ORIG_DIR'])
        except Exception as e:
            handle_exception("file processing", e)

        if self.args.summarize:
            try:
                self.generate_summary(file_path, file_name)
            except Exception as e:
                handle_exception("summary generation", e)

    def generate_summary(self, file_path: str, file_name: str) -> None:
        try:
            ocr_text = self.perform_ocr(file_path)
            summarization_prompt = f"{self.config['prompts']['summarization']}:{ocr_text}"
            summary = self.call_llm(summarization_prompt)
            if summary:
                self.save_summary(file_path, file_name, summary)
            else:
                logging.warning(f"Failed to generate summary for {file_path}")
        except Exception as e:
            logging.error(f"Error generating summary for {file_path}: {str(e)}")

    def save_summary(self, file_path: str, file_name: str, summary: str) -> None:
        summary_filename = f"{os.path.splitext(file_name)[0]}_summary.txt"
        summary_filepath = os.path.join(self.ai_rename_dir, summary_filename)
        with open(summary_filepath, 'w') as f:
            f.write(summary)
        logging.info(f"Summary saved to '{summary_filepath}'")

    def perform_ocr(self, file_path: str) -> str:
        ocr_text = ""
        if file_path.lower().endswith('.pdf'):
            ocr_text = self.perform_pdf_ocr(file_path)
        elif file_path.lower().endswith(('.jpg', '.png')):
            ocr_text = self.perform_image_ocr(file_path)
        return ocr_text.strip()

    def perform_pdf_ocr(self, file_path: str) -> str:
        base_name = os.path.splitext(file_path)[0]
        image_file = f"{base_name}-%d.png"

        # Check if images have already been generated
        cached_images = [f for f in os.listdir(self.ai_rename_dir) if f.startswith(os.path.basename(base_name)) and f.endswith('.png')]
        if not cached_images:
            # Convert PDF to high-res images
            cmd = ['magick', 'convert', '-density', '300', file_path, '-depth', '8', '-strip', '-background', 'white', '-alpha', 'off', f"{self.ai_rename_dir}/{os.path.basename(base_name)}-%d.png"]
            if self.args.debug:
                logging.debug(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if self.args.debug:
                logging.debug(f"Command output: {result.stdout}\nErrors: {result.stderr}")
            cached_images = [f for f in os.listdir(self.ai_rename_dir) if f.startswith(os.path.basename(base_name)) and f.endswith('.png')]
        else:
            logging.info(f"Using cached images for {file_path}")

        ocr_text = ""
        for image_file in sorted(cached_images):
            page_image = os.path.join(self.ai_rename_dir, image_file)
            bw_image = f"{page_image}_bw.png"

            if not os.path.exists(bw_image):
                # Preprocess the image
                cmd = ['mogrify', '-contrast', '-sharpen', '0x1', page_image]
                if self.args.debug:
                    logging.debug(f"Executing command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if self.args.debug:
                    logging.debug(f"Command output: {result.stdout}\nErrors: {result.stderr}")

                cmd = ['magick', 'convert', page_image, '-threshold', '50%', bw_image]
                if self.args.debug:
                    logging.debug(f"Executing command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if self.args.debug:
                    logging.debug(f"Command output: {result.stdout}\nErrors: {result.stderr}")
            else:
                logging.info(f"Using cached preprocessed image {bw_image}")

            # Perform OCR on the preprocessed image
            cmd = [
                'tesseract', bw_image, 'stdout',
                '-l', self.config['LANGUAGE'],
                '--dpi', '300',
                '--psm', '6',
                '--oem', '1'
            ]
            if self.args.debug:
                logging.debug(f"Executing tesseract command: {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                ocr_text += result.stdout + "\n\n"  # Add page break between pages
                if self.args.debug:
                    logging.debug(f"Tesseract output: {result.stdout}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Tesseract error: {e}")
                logging.error(f"Tesseract stderr: {e.stderr}")
            except UnicodeDecodeError as e:
                logging.error(f"Unicode decode error: {e}")
                logging.error(f"Trying to decode with utf-8 ignoring errors")
                result = subprocess.run(cmd, capture_output=True, check=True)
                ocr_text += result.stdout.decode('utf-8', errors='ignore') + "\n\n"

        return ocr_text

    def perform_image_ocr(self, file_path: str) -> str:
        base_name = os.path.splitext(file_path)[0]
        bw_file_path = os.path.join(self.ai_rename_dir, f"{os.path.basename(base_name)}_bw.png")

        # Check if the image has already been processed
        if not os.path.exists(bw_file_path):
            # Preprocess the image
            cmd = ['mogrify', '-contrast', '-sharpen', '0x1', file_path]
            if self.args.debug:
                logging.debug(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if self.args.debug:
                logging.debug(f"Command output: {result.stdout}\nErrors: {result.stderr}")

            cmd = ['magick', 'convert', file_path, '-threshold', '50%', bw_file_path]
            if self.args.debug:
                logging.debug(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if self.args.debug:
                logging.debug(f"Command output: {result.stdout}\nErrors: {result.stderr}")
        else:
            logging.info(f"Using cached preprocessed image {bw_file_path}")

        # Perform OCR on the preprocessed image
        cmd = [
            'tesseract', bw_file_path, 'stdout',
            '-l', self.config['LANGUAGE'],
            '--dpi', '300',
            '--psm', '6',
            '--oem', '1'
        ]
        if self.args.debug:
            logging.debug(f"Executing tesseract command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            ocr_text = result.stdout
            if self.args.debug:
                logging.debug(f"Tesseract output: {ocr_text}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Tesseract error: {e}")
            logging.error(f"Tesseract stderr: {e.stderr}")
            ocr_text = ""
        except UnicodeDecodeError as e:
            logging.error(f"Unicode decode error: {e}")
            logging.error(f"Trying to decode with utf-8 ignoring errors")
            result = subprocess.run(cmd, capture_output=True, check=True)
            ocr_text = result.stdout.decode('utf-8', errors='ignore')

        return ocr_text

    def call_llm(self, prompt: str) -> str:
        model = self.config.get("MODEL", "gpt2")
        for attempt in range(2):
            try:
                logging.debug(f"prompt:\n---\n{prompt}\n---\n")

                response = litellm.completion(
                    model=f"huggingface/{model}",  # Specify the LLM provider
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    stream=False
                )
                llm_response = response['choices'][0]['message']['content'].strip()
                logging.debug(f"response:\n---\n{llm_response}\n---\n")
                return llm_response
            except litellm.exceptions.BadRequestError as e:
                if attempt == 0:
                    logging.warning(f"Request failed: {str(e)}. Retrying...")
                    continue
                handle_exception("LLM API call", e)
                return ''
            except (KeyError, IndexError) as e:
                handle_exception("LLM response parsing", e)
                return ''
        return ''

    def test_llm_connectivity(self) -> bool:
        test_prompt = "Test prompt: Please respond with 'Test successful'"
        logging.info("Testing LLM connectivity...")
        response = self.call_llm(test_prompt)
        try:
            if "Test successful" in response:
                logging.info("LLM connectivity test successful.")
                return True
            else:
                logging.error("LLM connectivity test failed.")
                return False
        except Exception as e:
            logging.error(f"Error parsing LLM response: {str(e)}")
            return False

    def process_pdf(self, file_path: str, file_name: str, done_dir: str, orig_dir: str) -> None:
        ocr_text = self.perform_ocr(file_path)
        if not ocr_text:
            logging.warning(f"OCR failed for file: {file_path}")
            return

        if self.args.rename:
            self.rename_file(file_path, file_name, done_dir, orig_dir, ocr_text)

    def process_image(self, file_path: str, file_name: str, done_dir: str, orig_dir: str) -> None:
        ocr_text = self.perform_ocr(file_path)
        if not ocr_text:
            logging.warning(f"OCR failed for file: {file_path}")
            return

        if self.args.rename:
            self.rename_file(file_path, file_name, done_dir, orig_dir, ocr_text)

    def rename_file(self, file_path: str, file_name: str, done_dir: str, orig_dir: str, ocr_text: str) -> None:
        ai_generated_filename = self.generate_filename(ocr_text)
        if not ai_generated_filename:
            logging.warning(f"Failed to generate filename for: {file_path}")
            return

        cleaned_filename = self.clean_filename(ai_generated_filename)
        if not cleaned_filename:
            logging.warning(f"Generated filename is invalid for: {file_path}")
            return

        file_extension = os.path.splitext(file_name)[1]
        new_filename = f"{cleaned_filename}{file_extension}"
        new_filepath = os.path.join(done_dir, new_filename)

        # Log the new filename
        logging.info(f"Would rename '{file_name}' to '{new_filename}'")

        try:
            self.move_or_copy_file(file_path, new_filepath, orig_dir, file_name)
        except OSError as e:
            logging.error(f"Error renaming file {file_path}: {str(e)}")

    def generate_filename(self, ocr_text: str) -> str:
        filename_prompt = self.config['prompts']['filename_generation']
        payload = {
            "messages": [
                {"role": "system", "content": filename_prompt},
                {"role": "user", "content": f"Here is the file content: {ocr_text}"}
            ],
            "temperature": 0,
            "max_tokens": 100,
            "stream": False
        }

        try:
            api_base = self.config.get('API_BASE', 'https://api-inference.huggingface.co/models/gpt2')
            response = requests.post(
                api_base,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.config['API_TOKEN']}"},
                data=json.dumps(payload),
                timeout=90
            )
            response.raise_for_status()
            response_json = response.json()
            return response_json['choices'][0]['message']['content'].strip()
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            logging.error(f"Error generating filename: {str(e)}")
            return ''

    def clean_filename(self, filename: str) -> str:
        cleaned_content = re.sub(r'[^a-zA-Z0-9 ]', ' ', filename)
        cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
        cleaned_content = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned_content)
        content_length = len(cleaned_content)

        if 15 <= content_length <= 100:
            return cleaned_content
        return ''

    def move_or_copy_file(self, file_path: str, new_filepath: str, orig_dir: str, file_name: str) -> None:
        if self.args.dry_run:
            logging.info(f"Dry run: '{file_path}' would be renamed to '{new_filepath}'")
            return

        try:
            if self.args.move:
                shutil.move(file_path, new_filepath)
                logging.info(f"'{file_path}' was successfully renamed to '{new_filepath}' and moved")
            elif self.args.copy:
                shutil.copy2(file_path, new_filepath)
                shutil.move(file_path, os.path.join(orig_dir, file_name))
                logging.info(f"'{file_path}' was successfully renamed to '{new_filepath}' and copied")
            else:
                os.rename(file_path, new_filepath)
                logging.info(f"'{file_path}' was successfully renamed to '{new_filepath}'")
        except (IOError, OSError) as e:
            handle_exception("file operation", e)

def setup_logging(debug: bool) -> None:
    """
    Set up logging configuration.

    Args:
        debug (bool): If True, sets the logging level to DEBUG, otherwise to INFO.
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('file_processor.log')
        ]
    )

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Process files in a directory using OCR and AI to generate filenames.')
    directory_help = 'The directory containing files to process. Optional when -t is used.'
    parser.add_argument('directory', nargs='?', type=str, help=directory_help)
    parser.add_argument('-n', '--dry-run', action='store_true', help='Simulate the renaming process without actually renaming files. Default is off.')
    parser.add_argument('-r', '--rename', action='store_true', help='Rename the files after processing. Default is off.')
    parser.add_argument('-m', '--move', action='store_true', help='Move the files after processing. Default is off.')
    parser.add_argument('-c', '--copy', action='store_true', help='Copy the files after processing. Default is off.')
    parser.add_argument('-s', '--summarize', action='store_true', help='Enable summarization of the OCR text. Default is off.')
    parser.add_argument('-o', '--keep-ocr-output', action='store_true', help='Keep a copy of the OCR output per file in the same directory. Default is off.')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging. Default is off.')
    parser.add_argument('--progress-bar', action='store_true', help='Enable progress bar during file processing. Default is off.')
    parser.add_argument('--keep-original', action='store_true', default=False, help='Preserve the original file after renaming. Default is off.')
    parser.add_argument('-t', '--test-llm', action='store_true', help='Test connectivity with the LLM by sending a test prompt and verifying a response. Default is off.')
    parser.add_argument('--model', type=str, default=None, help='Specify the model to use for LLM. Default is gpt2.')
    return parser.parse_args()

def read_config() -> Dict[str, Any]:
    """
    Read the configuration from a YAML file.

    Returns:
        Dict[str, Any]: The configuration dictionary.
    """
    config_file = 'config.yaml'
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError as e:
        handle_exception("config file reading", e)
        return {}
    except yaml.YAMLError as e:
        handle_exception("config file parsing", e)
        return {}

def write_config(config: Dict[str, Any]) -> None:
    """
    Write the configuration to a YAML file.

    Args:
        config (Dict[str, Any]): The configuration dictionary to write.
    """
    config_file = 'config.yaml'
    try:
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    except IOError as e:
        handle_exception("config file writing", e)

def create_config() -> Dict[str, Any]:
    """
    Create a configuration dictionary by prompting the user for input.

    Returns:
        Dict[str, Any]: The created configuration dictionary.
    """
    LANGUAGE = input(f"Enter the language for OCR (default: eng): ") or 'eng'
    ORIG_SUBDIR = input(f"Enter the original subdirectory (default: orig): ") or 'orig'
    return {'LANGUAGE': LANGUAGE, 'ORIG_SUBDIR': ORIG_SUBDIR}

def main():
    """
    The main function to execute the file processing script.
    """
    args = parse_arguments()
    setup_logging(args.debug)

    # Log script start
    logging.info("File processing script started")

    # Log configuration details
    logging.info(f"Processing directory: {args.directory}")
    logging.info(f"Rename mode: {'Enabled' if args.rename else 'Disabled'}")
    logging.info(f"Summarize mode: {'Enabled' if args.summarize else 'Disabled'}")
    logging.info(f"Move files: {'Yes' if args.move else 'No'}")
    logging.info(f"Keep original: {'Yes' if args.keep_original else 'No'}")
    logging.info(f"Debug mode: {'Enabled' if args.debug else 'Disabled'}")

    config = read_config()
    if not config:
        config = create_config()
        write_config(config)

    if args.model:
        config["MODEL"] = args.model

    check_required_commands()

    processor = FileProcessor(config, args)

    if args.test_llm:
        if not processor.test_llm_connectivity():
            logging.error("LLM connectivity test failed. Exiting.")
            sys.exit(1)
    else:
        if not args.directory:
            logging.error("The directory argument is required unless -t is used.")
            sys.exit(1)
        if os.path.isfile(args.directory):
            dirs = processor.setup_directories(os.path.dirname(args.directory))
            processor.process_single_file(os.path.dirname(args.directory), os.path.basename(args.directory), dirs, 0, None)
        elif os.path.isdir(args.directory):
            processor.process_files(args.directory)
        else:
            logging.error(f"The path '{args.directory}' does not exist.")
            sys.exit(1)
    if not args.debug:
        processor.cleanup()
if __name__ == '__main__':
    main()
