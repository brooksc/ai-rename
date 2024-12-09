import os
import requests
import magic

# List of tuples containing filenames and their corresponding URLs
files_to_download = [
    ("simple1.pdf", "https://www.learningcontainer.com/wp-content/uploads/2019/09/sample-pdf-file.pdf"),
    ("simple2.pdf", "https://smallpdf.com/blog/sample-pdf"),
    ("report1.pdf", "https://www.learningcontainer.com/wp-content/uploads/2019/09/sample-pdf-download-10-mb.pdf"),
    ("report2.pdf", "https://file-examples.com/wp-content/uploads/2017/10/file-sample_150kB.pdf"),
    ("scanned1.pdf", "https://www.learningcontainer.com/wp-content/uploads/2019/09/sample-pdf-with-images.pdf"),
    ("scanned2.pdf", "https://file-examples.com/wp-content/uploads/2017/10/file-sample_1MB.pdf"),
    ("complex1.pdf", "https://github.com/py-pdf/sample-files/raw/main/004-pdflatex-4-pages/sample.pdf"),
    ("complex2.pdf", "https://file-examples.com/wp-content/uploads/2017/10/file-sample_1MB.pdf"),
    ("damaged1.pdf", "https://github.com/py-pdf/sample-files/raw/main/017-unreadable-meta-data/sample.pdf"),
    ("damaged2.pdf", "https://github.com/ArturT/Test-PDF-Files/raw/master/corrupted.pdf"),
    ("large1.pdf", "https://www.learningcontainer.com/wp-content/uploads/2019/09/sample-large-file.pdf"),
    ("form1.pdf", "https://github.com/py-pdf/sample-files/raw/main/010-pdflatex-forms/sample.pdf"),
    ("password1.pdf", "https://github.com/py-pdf/sample-files/raw/main/005-libreoffice-writer-password/sample.pdf"),
    ("multilingual1.pdf", "https://github.com/py-pdf/sample-files/raw/main/015-arabic/sample.pdf"),
]

# Track successful and failed downloads
successful_downloads = []
failed_downloads = []

# Set to track processed URLs
processed_urls = set()

for filename, url in files_to_download:
    if url in processed_urls:
        print(f"Skipping duplicate URL for {filename}: {url}")
        continue

    print(f"Downloading {filename} from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"{filename} downloaded successfully.")

        # Validate if the file is a PDF
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(filename)
        if file_type == 'application/pdf':
            print(f"{filename} is a valid PDF.")
            successful_downloads.append(filename)
        else:
            print(f"{filename} is not a PDF (detected as {file_type}). Deleting...")
            os.remove(filename)
            failed_downloads.append(filename)
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {filename}: {e}")
        failed_downloads.append(filename)
    except Exception as e:
        print(f"An error occurred with {filename}: {e}")
        failed_downloads.append(filename)

    # Mark URL as processed
    processed_urls.add(url)

# List the directory contents
print("\nDirectory contents:")
for item in os.listdir('.'):
    if os.path.isfile(item):
        print(f"- {item}")

# Display the summary
print("\nSummary:")
print(f"Successfully downloaded PDFs: {len(successful_downloads)}")
print(f"Failed downloads or invalid files: {len(failed_downloads)}")
if failed_downloads:
    print("Missing files:")
    for file in failed_downloads:
        print(f"- {file}")