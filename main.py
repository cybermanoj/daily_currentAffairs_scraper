# main.py
import os
import shutil
import sys
import glob

# Add Helping Files to Python's search path for modules
PROJECT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
HELPING_FILES_DIR = os.path.join(PROJECT_ROOT_DIR, "HelpingFiles")
sys.path.insert(0, HELPING_FILES_DIR) # Or use package imports if __init__.py is present

# Now import from the "Helping Files" package/directory
from HelpingFiles import extractor
from HelpingFiles import html_generator
from HelpingFiles import pdf_generator

# Define output directory paths based on the new structure
OUTPUT_IMAGES_DIR = os.path.join(PROJECT_ROOT_DIR, "Output Images")
OUTPUT_HTML_DIR = os.path.join(PROJECT_ROOT_DIR, "Output Html")
OUTPUT_PDF_DIR = os.path.join(PROJECT_ROOT_DIR, "Output Pdf")

# CSS source and destination
CSS_SOURCE_PATH = os.path.join(HELPING_FILES_DIR, html_generator.CSS_FILENAME_ONLY) # e.g., Helping Files/styles.css
CSS_DESTINATION_DIR = OUTPUT_HTML_DIR # CSS will be placed alongside HTML
CSS_DESTINATION_PATH = os.path.join(CSS_DESTINATION_DIR, html_generator.CSS_FILENAME_ONLY) # e.g., Output Html/styles.css


def clear_directory_contents(directory_path, file_extension_pattern="*"):
    """Deletes all files matching the pattern within the specified directory."""
    if not os.path.isdir(directory_path):
        print(f"Directory not found, cannot clear: {directory_path}")
        return
    
    # Use glob to find all files matching the pattern (e.g., "*.html")
    files_to_delete = glob.glob(os.path.join(directory_path, file_extension_pattern))
    
    for f_path in files_to_delete:
        try:
            if os.path.isfile(f_path) or os.path.islink(f_path): # Check if it's a file or a symlink
                os.remove(f_path)
                print(f"Deleted old file: {f_path}")
            # Optionally, if you also wanted to remove subdirectories:
            # elif os.path.isdir(f_path):
            #     shutil.rmtree(f_path) 
        except Exception as e:
            print(f"Error deleting {f_path}: {e}")

def main():
    print("--- Starting Scraper ---")

    # --- Create output directories ---
    os.makedirs(OUTPUT_IMAGES_DIR, exist_ok=True)
    os.makedirs(OUTPUT_HTML_DIR, exist_ok=True)
    os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)

    # Step 1: Extract data
    print("\n--- Fetching and Parsing Content ---")
    source_url = extractor.get_daily_url()
    raw_html_content = extractor.fetch_page_content(source_url)

    if not raw_html_content:
        print("Failed to fetch content. Exiting.")
        return

    # Pass the absolute path where images should be saved.
    articles_data = extractor.parse_content(
        raw_html_content,
        images_save_dir=OUTPUT_IMAGES_DIR # e.g., PROJECT_ROOT/Output Images
    )

    if not articles_data:
        print("No articles extracted. Exiting.")
        return
    print(f"Successfully extracted {len(articles_data)} new articles. Proceeding to generate output.")

    print(f"\n--- Clearing previous HTML and PDF files ---")
    clear_directory_contents(OUTPUT_HTML_DIR, "*.html") # Clear all .html files
    clear_directory_contents(OUTPUT_PDF_DIR, "*.pdf")   # Clear all .pdf files
    # Note: Output Images directory was already cleared by extractor.py's parse_content by this point
    
    if os.path.exists(CSS_SOURCE_PATH):
        shutil.copy(CSS_SOURCE_PATH, CSS_DESTINATION_PATH)
        print(f"Copied {CSS_SOURCE_PATH} to {CSS_DESTINATION_PATH}")
    else:
        print(f"Warning: Source CSS file not found at {CSS_SOURCE_PATH}. HTML might not be styled correctly.")

    # Step 2: Generate HTML file
    print("\n--- Generating HTML File ---")
    # html_generator will save the HTML file into OUTPUT_HTML_DIR.
    # The HTML will reference images like ../Output Images/image.jpg
    # and CSS like styles.css (if copied directly to OUTPUT_HTML_DIR)
    generated_html_path = html_generator.generate_html_file(
        articles_data,
        output_dir=OUTPUT_HTML_DIR # e.g., PROJECT_ROOT/Output Html
    )

    if not generated_html_path or not os.path.exists(generated_html_path):
        print("HTML generation failed or file not found. Exiting.")
        return

    # Step 3: Generate PDF file
    print("\n--- Generating PDF File ---")
    # Construct the full path for the PDF file within OUTPUT_PDF_DIR
    pdf_target_path = os.path.join(OUTPUT_PDF_DIR, pdf_generator.PDF_OUTPUT_FILENAME)
    pdf_generator.generate_pdf_from_html(generated_html_path, pdf_target_path)

    print("\n--- Scraper Finished ---")
    print(f"Outputs generated in respective 'Output ...' directories under {PROJECT_ROOT_DIR}")

if __name__ == "__main__":
    main()

