
# AI File Renamer

This Python script processes files in a specified directory, using Optical Character Recognition (OCR) to extract text from files, and then leverages an AI service to generate descriptive filenames based on the extracted text. The script is designed to work primarily with PDF and image files (e.g., JPG, PNG) and is capable of automatically organizing and renaming files according to the content.

## Features

- **OCR Support**: Extracts text from PDFs and images using Tesseract.
- **AI-Powered Filename Generation**: Uses AI to generate descriptive filenames based on the content of the files.
- **Original File Preservation**: Optionally retains original files while creating renamed copies.
- **Customizable Settings**: Configure OCR language and subdirectory for original files through a simple configuration file.
- **Error Handling**: Handles various edge cases, including invalid directories, failed OCR processing, and AI service errors.

## Installation

### Prerequisites

Ensure you have the following installed on your Mac:

- **Homebrew**: If you don't have Homebrew installed, install it by running the following command:

  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```

- **Tesseract**: Install Tesseract using Homebrew:

  ```bash
  brew install tesseract
  ```

- **pdftoppm**: Install the Poppler utilities, which include `pdftoppm`, using Homebrew:

  ```bash
  brew install poppler
  ```

- **Python 3**: Ensure you have Python 3 installed. You can install it via Homebrew:

  ```bash
  brew install python
  ```

### Python Dependencies

Use `pip` to install the necessary Python packages:

```bash
pip install requests argparse
```

### AI Service

Ensure you have an AI service running that can process requests as specified in the script. The AI service should be accessible at `http://localhost:1234/v1/chat/completions`.

## Usage

### Command-Line Arguments

- `directory` (required): The directory containing the files to process.
- `-d`, `--debug` (optional): Enable debug logging for more verbose output.
- `--keep-original` (optional): Set to `False` if you don't want to keep the original files after renaming. Default is `True`.

### Example Usage

```bash
python3 ai_file_renamer.py /path/to/your/files -d --keep-original=False
```

This command processes all files in the `/path/to/your/files` directory, enabling debug logging and moving the original files instead of keeping them.

### Configuration File

The script reads settings from a configuration file located at `~/.ai-rename`. If this file does not exist, the script will prompt you to enter the settings the first time it runs.

- **LANGUAGE**: Specifies the language for OCR. Default is `eng`.
- **ORIG_SUBDIR**: The subdirectory within the provided directory where original files are stored. Default is `orig`.

## Example Workflow

1. **Prepare your files**: Place the files you want to process in a directory.
2. **Run the script**: Use the command line to execute the script, specifying the directory.
3. **Review the output**: The script will generate new filenames and move the processed files to a `done` subdirectory. If `--keep-original` is set to `True`, the original files will be preserved in a separate subdirectory.

## Logging

The script logs its activity, including errors and AI responses, to the console. If the `--debug` flag is set, more detailed logs will be displayed.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.
