import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from datetime import datetime
import urllib.parse
import os
import shutil

BASE_URL_SITE = "https://www.drishtiias.com"
API_BASE_URL = f"{BASE_URL_SITE}/current-affairs-news-analysis-editorials/news-analysis/"
IMAGES_DIR_NAME = "Output Images"
SKIP_TAG_NAMES = {'script', 'style', 'form', 'nav', 'footer', 'aside', 'noscript', 'ins'} # Add tag names to skip
SKIP_CSS_CLASSES = {'banner-static','next-post','tags-new',"mobile-ad-banner","desktop-ad-banner",'advertisement', 'social-shares', 'comments-section', 'hidden', 'no-print', 'adsbygoogle', 'a2a_kit'} # Add CSS classes to skip
#For keeping Style
KEEP_STYLE_TAG = [""]
KEEP_STYLE_CSS_CLASS = [""]
KEEP_STYLE_ID =[""]

_CURRENT_ACTUAL_IMAGES_SAVE_DIR_INTERNAL = IMAGES_DIR_NAME
HTML_IMAGES_RELATIVE_PATH_PREFIX = "../Output Images"

def get_daily_url():
    """"Generates the URL for the current day's news analysis"""
    today = datetime.now()
    date_str = today.strftime("%d-%m-%Y")
    return f"{API_BASE_URL}03-06-2025"

def fetch_page_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        print(f"Fetching: {url}")
        response = requests.get(url , headers=headers , timeout= 15)
        response.raise_for_status()
        print(f"Successfully fetched: {url}")
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def download_image(image_url , local_images_base_dir , article_idx, img_counter):
    if not image_url:
        return None
    try:
        # Create a somewhat unique filename
        url_path = urllib.parse.urlparse(image_url).path
        filename_base, ext_original = os.path.splitext(os.path.basename(url_path))
        
        img_filename_only = f'article_{article_idx}_img_{img_counter}{ext_original if ext_original and len(ext_original) <=5 else ".jpg"}' # Basic ext check
        
        if not filename_base or not ext_original or len(ext_original) > 5 or '/' in ext_original :
            query_ext_list = urllib.parse.parse_qs(urllib.parse.urlparse(image_url).query).get('format')
            ext_from_query = query_ext_list[0] if query_ext_list and len(query_ext_list[0]) <= 4 else None
            ext_from_url_part = image_url.split('.')[-1] if '.' in image_url else None
            
            final_ext = '.jpg' # default
            if ext_from_url_part and len(ext_from_url_part) <= 4 and '/' not in ext_from_url_part:
                final_ext = '.' + ext_from_url_part
            elif ext_from_query:
                final_ext = '.' + ext_from_query
            img_filename_only = f'article_{article_idx}_img_{img_counter}{final_ext}'

        # local_images_base_dir here is the actual absolute path like "PROJECT_ROOT/Output Images"
        local_image_full_path = os.path.join(local_images_base_dir, img_filename_only)
        
        # Ensure the directory exists (it should have been created by parse_content)
        os.makedirs(local_images_base_dir, exist_ok=True) 
        
        
        
        if os.path.exists(local_image_full_path):
            print(f"Image already exists: {local_image_full_path}")
            return os.path.join(HTML_IMAGES_RELATIVE_PATH_PREFIX, img_filename_only).replace("\\", "/")
        
        print(f"Attempting to download image: {image_url}")
        img_response = requests.get(image_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        img_response.raise_for_status()
        with open(local_image_full_path, 'wb') as f_img:
            shutil.copyfileobj(img_response.raw, f_img)
        print(f"Successfully downloaded {img_filename_only} to {local_images_base_dir}")
        # Return the relative path for HTML
        return os.path.join(HTML_IMAGES_RELATIVE_PATH_PREFIX , img_filename_only).replace('\\', "/") # Ensure forward slashes for HTML
    except Exception as e :
        print(f"An unexpected error occurred while downloading {image_url}: {e}")
        return None

def should_this_node_be_skipped(node):
    if not isinstance(node, Tag):
        return False    # Don't skip non-tags like NavigableString by default here
    if node.name in SKIP_TAG_NAMES:
        return True
    if node.has_attr("class"):
        node_classes = node.get('class' , [])
        if any (c in SKIP_CSS_CLASSES for c in node_classes):
            return True
    return False

def process_node_for_output(node_element, article_idx , image_counters , convert_youtube_to_link=True):
    global _CURRENT_ACTUAL_IMAGES_SAVE_DIR_INTERNAL
    """
    Modifies the node_element in-place:
    1. Removes all 'style' attributes from the element and its descendants.
    2. Converts relative 'href' attributes in <a> tags to absolute URLs.
    """
    if not isinstance(node_element , Tag):
        return
    
    if should_this_node_be_skipped(node_element):
        node_element.decompose() # Remove it from the tree
        return # Stop processing this branch
    
    # --- Process children first (recursively) ---
    for child in list(node_element.children):
        if isinstance(child, Tag):
            process_node_for_output(child, article_idx, image_counters, convert_youtube_to_link)
    
    # --- If this is the starRating div, transform its children ---
    
    if node_element.name =='div' and node_element.has_attr("class") and "starRating"in node_element.get("class" , []):
        new_star_spans = []
        original_comment = None 
        for star_span in node_element.find_all("span" , class_=lambda x: x and ('fa-star' in x) ):
            # Create a new span, we'll add text to it
            new_span = BeautifulSoup("" , "html.parser").new_tag("span")
            if "checked" in star_span.get("class" , []):
                new_span.string = "★"
                new_span['class'] = "star-checked" # Keep for color styling
            else:
                new_span.string = "☆"
                new_span['class'] = "star-unchecked"
            new_star_spans.append(new_span)
        node_element.clear()
        for new_span in new_star_spans:
            node_element.append(new_span)
            node_element.append(NavigableString(' '))




    # --- Now process the current node_element itself (since it wasn't skipped) ---
    # 1. Remove inline styles from the element itself and all descendants
    
    if node_element.has_attr('style'):
        keep_style = False
        if node_element.name in KEEP_STYLE_TAG:
            keep_style = True
        if not keep_style and node_element.has_attr('class') and \
           any(cls in KEEP_STYLE_CSS_CLASS for cls in node_element.get("class", [])):
            keep_style = True
        if not keep_style and node_element.has_attr('id') and \
           node_element.get("id") in KEEP_STYLE_ID:
            keep_style = True
        
        if not keep_style:
            del node_element['style']
    #same thing
    #if node_element.has_attr('style') and (node_element.name not in KEEP_STYLE_TAG and not any(cls in KEEP_STYLE_CSS_CLASS for cls in node_element.get("class" , []))and node_element.get("id") not in KEEP_STYLE_ID):
        #del node_element['style']
    #for  descendant in node_element.find_all(True):
        #if descendant.has_attr('style') and (descendant.name not in KEEP_STYLE_TAG and not any(cls in KEEP_STYLE_CSS_CLASS for cls in descendant.get("class" , []))and descendant.get("id") not in KEEP_STYLE_ID):
            #del descendant['style']
    
    
    # 2. Fix relative links in <a> tags within the element and its descendants
    #--- Handle <iframe> (including YouTube) BEFORE general <a> tag processing for unwrapping ---
    if node_element.name == 'iframe':
        iframe_src = node_element.get('src', '')
        is_youtube = 'youtube.com/embed/' in iframe_src
        
        if is_youtube and convert_youtube_to_link:
            youtube_link_src = ("https:" + iframe_src) if iframe_src.startswith('//') else iframe_src
            
            current_soup = node_element.find_parent()# Find any ancestor
            if current_soup:
                current_soup = current_soup.soup 
            else:
                current_soup = node_element
            if not hasattr(current_soup , "new_tag"):# Fallback if current_soup is not a full soup object
                temp_soup_for_replacement = BeautifulSoup("", "html.parser")
                p_tag = temp_soup_for_replacement.new_tag("p")
                a_tag_yt = temp_soup_for_replacement.new_tag("a", href=youtube_link_src, target="_blank")
            else:
                p_tag = current_soup.new_tag("p")
                a_tag_yt = current_soup.new_tag("a", href=youtube_link_src, target="_blank")
            
            link_text_node = NavigableString("[Watch Video on YouTube: ")
            a_tag_yt.string = youtube_link_src # Display the link
            closing_text_node = NavigableString("]")
            
            p_tag.append(link_text_node)
            p_tag.append(a_tag_yt)
            p_tag.append(closing_text_node)
            
            node_element.replace_with(p_tag)
            return # The iframe is replaced, no further processing for this node
        elif iframe_src.startswith('//'): # For non-YouTube protocol-relative iframes
             node_element['src'] = "https:" + iframe_src

    if node_element.name == 'a' and node_element.has_attr('href'):
        href = node_element['href']
        if href and not href.startswith(('http://', 'https://', '#', 'mailto:', 'tel:')):
            if href.startswith('//'):
                node_element['href'] = "https:" + href
            else:
                node_element['href'] = urllib.parse.urljoin(BASE_URL_SITE, href)
    for a_tag in node_element.find_all('a' , href = True):
        href = a_tag['href']
        # Check if it's a relative URL that needs fixing
        if href and not href.startswith(('http://', 'https://', '#', 'mailto:', 'tel:')):
        # Handle protocol-relative URLs like //www.example.com  
            if href.startswith('//'):
                a_tag['href'] ="https:" + href
            else:# Handle paths like /path/to/page or path/to/page
                a_tag['href'] = urllib.parse.urljoin(BASE_URL_SITE, href)
    
    img_children = [child for child in node_element.children if isinstance(child, Tag) and child.name == "img"]
    other_tag_children = [child for child in node_element.children if isinstance(child, Tag) and child.name != 'img']
    text_node_strpped = "".join(node_element.find_all(string=True , recursive=False)).strip()
    if len(img_children) == 1 and not other_tag_children and not text_node_strpped:
        img_to_unwarap = img_children[0]
        node_element.replace_with(img_to_unwarap)
        return
    

    # 3. Download images in <img> tags (only for the current node_element)
    if node_element.name == 'img' and node_element.has_attr('src'):
        img_src = node_element['src']

        # Avoid re-processing already local images
        if IMAGES_DIR_NAME in img_src:
            return
        
        absolute_img_url = None
        if img_src and not img_src.startswith(('data:', 'http://', 'https://')):
            absolute_img_url = urllib.parse.urljoin(BASE_URL_SITE, img_src)
        elif img_src and (img_src.startswith('http://') or img_src.startswith('https://')):
            absolute_img_url = img_src
        
        if absolute_img_url:
            image_counters[article_idx] = image_counters.get(article_idx, 0) + 1
            img_counter = image_counters[article_idx]
            
            local_img_html_path = download_image(absolute_img_url, _CURRENT_ACTUAL_IMAGES_SAVE_DIR_INTERNAL, article_idx, img_counter)
            if local_img_html_path:
                node_element['src'] = local_img_html_path
            else:
                print("\nFailed to download\n")
                # Optionally, if download fails:
                # node_element['alt'] = f"Failed to download: {absolute_img_url}"
                # node_element['src'] = "#image-download-failed" # Placeholder
                pass


all_articles_data = []
def parse_content (html_bytes , images_save_dir=None):
    """Parses the HTML content and extracts relevant data for the main article."""
    global _CURRENT_ACTUAL_IMAGES_SAVE_DIR_INTERNAL
    if not html_bytes:
        print("NO html content to parse")
        return
    if images_save_dir:
        _CURRENT_ACTUAL_IMAGES_SAVE_DIR_INTERNAL = images_save_dir
    else:
        # Fallback to the module's default if not provided by caller
        # (though main.py always provides it in this setup)
        _CURRENT_ACTUAL_IMAGES_SAVE_DIR_INTERNAL = os.path.abspath(IMAGES_DIR_NAME)
    # Create images directory , delete old directory
    if os.path.exists(_CURRENT_ACTUAL_IMAGES_SAVE_DIR_INTERNAL):
        shutil.rmtree(_CURRENT_ACTUAL_IMAGES_SAVE_DIR_INTERNAL)
    os.makedirs(_CURRENT_ACTUAL_IMAGES_SAVE_DIR_INTERNAL)
    print(f"Created directory: {_CURRENT_ACTUAL_IMAGES_SAVE_DIR_INTERNAL}")

    html_content_str = html_bytes.decode('utf-8', errors = 'ignore')
    soup = BeautifulSoup(html_content_str , 'html.parser')

    page_main_tittle_tag = soup.title
    page_main_tittle = page_main_tittle_tag.string.strip() if page_main_tittle_tag and page_main_tittle_tag.string else "No main title found for page"

    print(f"HTML page Title : {page_main_tittle} ")

    list_category_div = soup.find('div' , class_='list-category')
    if not list_category_div:
        print("Error: Could not find 'list-category' div.")
        return
    
    main_article_wrapper_tag = list_category_div.find('article', recursive=False)
    if not main_article_wrapper_tag:
        print("Error: Could not find the main <article> tag within 'list-category'.")
        return
    
    article_detail_divs = main_article_wrapper_tag.find_all('div', class_ = 'article-detail')
    if not article_detail_divs: print("No 'article-detail' divs found."); return
    print(f"Found {len(article_detail_divs)} articles")

    # --- loop to each article-detail ---
        
    image_counters = {} # To generate unique image names per article
    temp_articles_data = [] 
    for index , article_detail_div in enumerate(article_detail_divs): # 'index' is for unique ID

        original_h1_text = "N/A"

        # Step 1: Process all relevant nodes within this article_detail_div.
        # Modifications will happen in the main 'soup'.
        title_h1 = article_detail_div.find('h1', recursive=False)
        if title_h1:
            original_h1_text = title_h1.get_text(strip=True)
            # --- Remove inline styles from H1 and its children ---
            process_node_for_output(title_h1, index , image_counters, convert_youtube_to_link=True)
            # Iterate through actual content nodes (siblings of H1 or all children if no H1)
            siblings_to_process = list(title_h1.find_next_siblings())
            for content_node in siblings_to_process:
                process_node_for_output(content_node,index,image_counters, convert_youtube_to_link=True)         
        else:
            print(f"Warning: No h1 found in article_detail at index {index}.")
            children_to_process = list(article_detail_div.children)
            for child_node in children_to_process:
                if isinstance(child_node , Tag):
                    process_node_for_output(child_node , index , image_counters,convert_youtube_to_link=True)
        
        star_count = 0
        star_rating_div_processed = article_detail_div.find("div", class_ ='starRating')
        if star_rating_div_processed:
            checked_stars = star_rating_div_processed.find_all("span" , class_ ='star-checked')
            star_count = len(checked_stars)
        # Step 2: Now that all processing for this article_detail_div is done,
        # rebuild the article_data from the modified soup.
        current_article_html_parts = []
        final_h1 = article_detail_div.find('h1', recursive=False)
        if final_h1:
           current_article_html_parts.append(final_h1.prettify())
           for final_content_node in final_h1.find_next_siblings():
               current_article_html_parts.append(final_content_node.prettify())
        else:# No H1, so collect all children of article_detail_div
            for final_child_node in article_detail_div.children:
                if isinstance(final_child_node, NavigableString) and final_child_node.strip():
                    current_article_html_parts.append(str(final_child_node))
                elif isinstance(final_child_node, Tag):
                    current_article_html_parts.append(final_child_node.prettify())
        
        if current_article_html_parts:
            temp_articles_data.append({
                "index": index,
                "original_h1": original_h1_text,
                "content_html": current_article_html_parts,
                "star_count": star_count
            })
    sorted_articles_data = sorted(temp_articles_data, key=lambda x: x['star_count'], reverse=True)
    return sorted_articles_data
