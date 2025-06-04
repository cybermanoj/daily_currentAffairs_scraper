# pdf_generator.py
import os
import pdfkit # Ensure pdfkit is imported
from datetime import datetime

# Default HTML output filename, used if importing from html_generator fails
_HTML_OUTPUT_FILENAME_DEFAULT = "default_from_pdf_gen.html"
try:
    # Try to get the HTML_OUTPUT_FILENAME from html_generator for consistency if needed elsewhere
    from html_generator import HTML_OUTPUT_FILENAME
except ImportError:
    print("pdf_generator.py: Could not import HTML_OUTPUT_FILENAME from html_generator. Using default.")
    HTML_OUTPUT_FILENAME = _HTML_OUTPUT_FILENAME_DEFAULT

today = datetime.now()
date_str_for_filename = today.strftime("%d-%m-%Y")
PDF_OUTPUT_FILENAME = f"Today ({date_str_for_filename}).pdf"

# For Strategy 3, generate_pdf_from_html does NOT need user_stylesheet_path
def generate_pdf_from_html(html_input_path, pdf_output_path):
    if os.path.exists(pdf_output_path):
        try:
            os.remove(pdf_output_path)
            print(f"Deleted existing PDF: {pdf_output_path}")
        except OSError as e:
            print(f"Error deleting existing PDF {pdf_output_path}: {e}. PDF generation may fail or overwrite.")


    print(f"Attempting to generate PDF: {pdf_output_path} from {html_input_path}")

    if not os.path.exists(html_input_path):
        print(f"Error: HTML input file not found at {html_input_path}")
        return

    # --- OPTIONS FOR STRATEGY 3 (Minimal options, print-media-type enabled) ---
    options = {
        'page-size': 'A4',
        'orientation': 'Portrait',
        'margin-top': '0',    # PDFKit margins, CSS body margins will apply within this box
        'margin-right': '0',
        'margin-bottom': '0.',
        'margin-left': '0',
        'encoding': "UTF-8",
        'enable-local-file-access': None, # ESSENTIAL
        'print-media-type': None,         # CRITICAL CHANGE: Set to None or OMIT
        'disable-smart-shrinking': None,  # Usually safe and good
        'zoom': '1.1',                    # Usually safe
        'load-error-handling': 'ignore',  # Usually safe
        'dpi': 300,
        'disable-smart-shrinking': True,
        'image-quality': 100

        # Try adding outline back if the above works
        # 'outline': None,
        # 'outline-depth': 3,
    }
    # --- END OPTIONS FOR STRATEGY 3 ---

    try:
        abs_html_input_path = os.path.abspath(html_input_path)
        print(f"Generating PDF with options: {options}") # Log the options being used
        pdfkit.from_file(abs_html_input_path, pdf_output_path, options=options)
        print(f"Successfully generated PDF: {pdf_output_path}")
    except FileNotFoundError:
        print("wkhtmltopdf not found. Please install it and ensure it's in your PATH, or configure the path in pdf_generator.py.")
        # You can add detailed instructions for wkhtmltopdf installation here if needed.
    except Exception as e:
        print(f"An error occurred during PDF generation with pdfkit: {e}")
        error_message = str(e).lower()
        if "done" not in error_message and "exit with code 1" not in error_message and "exit with code 2" not in error_message and "incorrect location" not in error_message:
            print("PDF generation might have failed or produced an empty/corrupt file for reasons unrelated to flag placement.")
        elif "incorrect location" in error_message:
            print(f"Still getting 'incorrect location' error. This suggests a persistent conflict with how PDFKit uses 'print-media-type': 'print' with your wkhtmltopdf version. Error details: {e}")
        elif "exit with code 1" in error_message or "exit with code 2" in error_message:
             print(f"wkhtmltopdf exited with an error code, indicating a problem during conversion. Check for messages like 'QXcbConnection' if on Linux without headless setup, or other wkhtmltopdf errors. Details: {e}")
        else: # "Done" might be in some success messages that still have exit code 1 for warnings
            print("PDF generation command likely finished. Review PDF for correctness. wkhtmltopdf may have emitted warnings.")