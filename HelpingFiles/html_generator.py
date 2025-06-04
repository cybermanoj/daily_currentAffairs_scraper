# html_generator.py
import os 
from datetime import datetime
today = datetime.now()
date_str_for_filename = today.strftime("%d-%m-%Y")

HTML_OUTPUT_FILENAME = f"{date_str_for_filename}.html"
CSS_DIR_NAME = "HtmlStyles"
CSS_FILENAME_ONLY = "styles.css"
CSS_RELATIVE_PATH_IN_HTML = CSS_FILENAME_ONLY
# IMAGES_DIR_NAME is implicitly handled as paths in content_html are already relative to HTML_OUTPUT_FILENAME

def generate_html_file(articles_data, output_dir="."):
    """
    Generates an HTML file from the provided articles_data.
    Assumes articles_data is a list of dicts, each with 'content_html', 'original_h1', 'star_count'.
    """
    html_file_path = os.path.join(output_dir, HTML_OUTPUT_FILENAME)

    if os.path.exists(html_file_path):
        os.remove(html_file_path)
        print(f"Deleted existing HTML file: {html_file_path}")

    with open(html_file_path, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html>\n")
        f.write("<html lang=\"en\">\n")
        f.write("<head>\n")
        f.write("    <meta charset=\"UTF-8\">\n")
        f.write("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n")
        f.write("    <title>Scraped Articles</title>\n")
        f.write(f'    <link rel="stylesheet" type="text/css" href="{CSS_RELATIVE_PATH_IN_HTML}">\n') # styles.css is relative
        f.write("</head>\n")
        f.write("<body>\n")
        f.write(f"    <h1>Current Affairs {date_str_for_filename}</h1>\n")
        f.write(f"    <h3 >Credit - Drishti Ias</h3>\n")

        if not articles_data:
            f.write("    <p>No article data was extracted.</p>\n")
        else:
            for i, article_info in enumerate(articles_data):
                # Using 'original_index' from extractor if you need to link back to original image names,
                # or just 'i' if images are named based on sorted order (simpler for this structure)
                f.write(f'    <div class="article-container" id="article-sorted-{i}">\n')
                full_article_html = "\n".join(article_info["content_html"])
                f.write(full_article_html)

                f.write("    </div>\n")
                if i < len(articles_data) - 1:
                     f.write("    <hr>\n")
        f.write("</body>\n")
        f.write("</html>\n")
        print(f"Successfully wrote scraped articles to {html_file_path}")
    return html_file_path