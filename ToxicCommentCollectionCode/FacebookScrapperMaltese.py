import os
import re
import time
import json
import signal
import csv
import random
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from google.cloud import translate_v2 as translate

# Load environment variables
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASS = os.getenv("PASS")
MAIN_GROUP_ID = os.getenv("MAIN_GROUP_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not EMAIL or not PASS or not MAIN_GROUP_ID or not GOOGLE_APPLICATION_CREDENTIALS:
    print("Environment variables not found. Please check if the .env file has EMAIL, PASS, MAIN_GROUP_ID, and GOOGLE_APPLICATION_CREDENTIALS.")
    exit(1)

# Set Google Application Credentials environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

# Setup Google Translate API
translate_client = translate.Client()

# Setup Chrome options
options = webdriver.ChromeOptions()
options.add_argument('--disable-notifications')
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument('--ignore-certificate-errors')

# Setup Chrome driver using webdriver_manager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# CSV filename and directory
csv_dir = 'ToxicCommentCollectionCode/Data_Collection'  # Ensure this is a relative path
csv_filename = os.path.join(csv_dir, 'comments.csv')

# Ensure the directory exists
os.makedirs(csv_dir, exist_ok=True)

# Function to load existing comments from CSV file
def load_existing_comments():
    existing_comments = set()
    if os.path.isfile(csv_filename):
        with open(csv_filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                existing_comments.add(row[0])
    return existing_comments

# Function to save comments to CSV file
def save_comments_to_csv(comments):
    if not comments:
        return

    existing_comments = load_existing_comments()
    
    with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for comment in comments:
            combined_text = comment['comment']
            if 'replies' in comment:
                replies_text = ' '.join([reply['reply'] for reply in comment['replies']])
                combined_text += ' ' + replies_text
            if combined_text not in existing_comments:
                writer.writerow([combined_text])
                existing_comments.add(combined_text)

# Signal handler for graceful exit
def signal_handler(sig, frame):
    print("Interrupted! Saving comments to CSV file.")
    save_comments_to_csv(all_comments)
    driver.quit()
    exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

# Function to introduce random delay
def random_delay(min_seconds=1, max_seconds=5):
    delay = random.uniform(min_seconds, max_seconds)
    print(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

# Function to detect if text is in Maltese
def is_maltese(text, confidence_threshold=0.70):
    if text.strip() == "":
        return False
    try:
        result = translate_client.detect_language(text)
        if result['language'] == 'mt' and result['confidence'] >= confidence_threshold:
            return True
        return False
    except Exception as e:
        print(f"Error detecting language: {e}")
        return False

# Function to remove names and surnames, mentions, and emojis
def clean_text(text):
    # Remove <a href> tags and their content
    text = re.sub(r'<a href="[^"]*">[^<]*</a>', '', text)
    
    # Remove @NameSurname mentions
    text = re.sub(r'@\w+', '', text)
    
    # Remove emails
    text = re.sub(r'\S+@\S+\.\S+', '', text)
    
    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)
    
    # Remove numbers (optional)
    text = re.sub(r'\d+', '', text)
    
    # Remove special characters (optional)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Remove extra whitespaces
    text = ' '.join(text.split())

    text = text.lower()
    
    return text

# Login to Facebook
driver.get("https://mbasic.facebook.com/login.php")

random_delay()

username = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']"))
)
password = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']"))
)

random_delay()

username.clear()
username.send_keys(EMAIL)
random_delay()
password.clear()
password.send_keys(PASS)

WebDriverWait(driver, 5).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="submit"]'))
).click()

random_delay()

WebDriverWait(driver, 5).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, 'tr > td > div > form[method="post"] + div a'))
).click()

random_delay()

# Define scraping functions
def replies_scraping(seen_comments):
    try:
        you_is_block = driver.find_element(
            By.XPATH,
            '//div[@title="You’re Temporarily Blocked"]/h2',
        ).text

        print("You’re Temporarily Blocked from viewing replies.")
        exit(1)
    except:
        pass
    
    replies = []
    next_page_btn_id = None

    while True:
        random_delay(1, 2)
        
        box_replies = driver.find_elements(
            By.XPATH,
            '//div[@id="root"]/div[@class]/div[not(@id)]/div[div]',
        )
        if len(box_replies) > 0:
            for idx, box in enumerate(box_replies):
                reply_by = box.find_element(By.XPATH, 'div/h3').text
                try:
                    reply_to = box.find_element(By.XPATH, 'div/div[1]/a').text
                except:
                    reply_to = None
                reply_array = box.find_elements(By.XPATH, "div/div[1]")
                reply_comment = ''.join([span.text for span in reply_array])
                if reply_to is not None:
                    reply_comment = reply_comment.replace(f'{reply_to} ', '')
                
                reply_comment = clean_text(reply_comment)

                if is_maltese(reply_comment):
                    reply = {
                        "reply_by": clean_text(reply_by),
                        "reply_to": clean_text(reply_to) if reply_to else None,
                        "reply": reply_comment,
                        "reply_order": idx
                    }
                    
                    reply_identifier = f"{reply['reply_by']}: {reply['reply']}"
                    if reply_identifier in seen_comments:
                        continue
                    seen_comments.add(reply_identifier)

                    print(f"{reply['reply_by']}{ ' To ' + reply.get('reply_to', '') if reply.get('reply_to', None) else '' } -> reply: {reply['reply']}")
                    replies.append(reply)
                
        if next_page_btn_id is None:
            try:
                next_page_btn_id = driver.find_element(By.XPATH, '//div[@id="root"]//div[starts-with(@id, "comment_replies_more_")]').get_attribute('id')
            except:
                break
        try:
            next_page_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f'//div[@id="root"]//div[@id="{next_page_btn_id}"]/a',
                    )
                )
            )
            next_page_btn.click()
            random_delay(1, 2)
        except:
            break
    return replies

def get_post_id_from_url(url):
    patterns = [
        r"/permalink/(\d+)",                      # /permalink/123456789
        r"story_fbid=(\w+)",                      # ?story_fbid=123456789
        r"groups/\d+/permalink/(\d+)",            # /groups/123456789/permalink/123456789
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def comments_scraping(seen_comments):
    post_id = get_post_id_from_url(driver.current_url)
    comments = []
    next_page_btn_id = None

    while True:
        random_delay(1, 2)
        
        box_comments = driver.find_elements(
            By.XPATH,
            '//*[@id="m_story_permalink_view"]/div[@id]/div/div[not(@id)]/div[div]',
        )
        if len(box_comments) > 0:
            for box_comment in box_comments:
                comment_by = box_comment.find_element(By.XPATH, "div/h3").text
                comment_text = box_comment.find_element(By.XPATH, "div/div[1]").text
                comment_text = clean_text(comment_text)
                
                if is_maltese(comment_text):
                    comment = {"comment_by": clean_text(comment_by), "comment": comment_text}
                    
                    comment_identifier = f"{comment['comment_by']}: {comment['comment']}"
                    if comment_identifier in seen_comments:
                        continue
                    seen_comments.add(comment_identifier)
                    
                    print(f"{comment_by} -> comment: {comment_text}")

                    replies_href = None
                    try:
                        replies_href = box_comment.find_element(
                            By.XPATH, 
                            'div[last()]/div/div//a[contains(text(), "replied")]').get_attribute('href')
                    except:
                        pass
                    if replies_href is not None:
                        driver.execute_script(f"window.open('{replies_href}', '_blank')")
                        random_delay(1, 2)
                        driver.switch_to.window(driver.window_handles[2])
                        replies = replies_scraping(seen_comments)
                        if len(replies) != 0:
                            comment["replies"] = replies
                        driver.close()
                        random_delay(1, 2)
                        driver.switch_to.window(driver.window_handles[1])
                    comments.append(comment)

        if next_page_btn_id is None:
            try:
                next_page_btn_id = driver.find_element(
                    By.XPATH,
                    '//*[@id="m_story_permalink_view"]/div[last()]/div/div[not(@id)]/div[a]'
                ).get_attribute('id')
            except:
                break
        try:
            next_page_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, f'//div[@id="root"]//div[@id="{next_page_btn_id}"]/a'))
            )
            next_page_btn.click()
            random_delay(1, 2)
        except:
            break
    print(f"Complete post_id: {post_id}")
    return comments

def post_scraping(seen_comments):
    comments = comments_scraping(seen_comments)
    return comments

driver.switch_to.window(driver.window_handles[0])
main_group_link = f"https://mbasic.facebook.com/{MAIN_GROUP_ID}/"
driver.get(main_group_link)

def reset_tab():
    for idx, tab in enumerate(driver.window_handles):
        if idx == 0:
            continue
        driver.switch_to.window(tab)
        driver.close()
    driver.switch_to.window(driver.window_handles[0])
    driver.get(main_group_link)
    random_delay()

reset_tab()

all_comments = []
seen_comments = load_existing_comments()

def scrape_group_posts():
    while True:
        anchor_all = driver.find_elements(
            By.XPATH, '//article/footer/div[last()]/a[contains(text(), "Full Story")]'
        )
        anchor_all = [a.get_attribute("href") for a in anchor_all]
        anchor_post_shares = driver.find_elements(
            By.XPATH,
            '//article[descendant::article]/footer/div[last()]/a[contains(text(), "Full Story")]',
        )
        anchor_post_shares = [a.get_attribute("href") for a in anchor_post_shares]
        anchors = list(set(anchor_all) - set(anchor_post_shares))
        if len(anchors) > 0:
            for a in anchors:
                try:
                    post_id = re.search(r"/permalink/(\d+)", a).group(1)
                except AttributeError:
                    print("No post ID found, skipping this post.")
                    continue

                driver.execute_script(f"window.open('{a}', '_blank')")
                random_delay(1, 2)
                driver.switch_to.window(driver.window_handles[1])
                print(f"Start scraping post_id: {post_id}.")

                comments = post_scraping(seen_comments)
                all_comments.extend(comments)

                driver.close()
                random_delay(1, 2)
                driver.switch_to.window(driver.window_handles[0])
                random_delay(1, 2)

        try:
            see_more_posts_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "section + div > a:has(span)",
                    )
                )
            )
            see_more_posts_btn.click()
            random_delay(2, 3)
        except:
            print("An error occurred.")
            print(f"Error URL: {driver.current_url}")
            reset_tab()
            break

def scrape_search_results():
    while True:
        posts = driver.find_elements(By.XPATH, '//div[@id="BrowseResultsContainer"]//article')
        if not posts:
            break

        for post in posts:
            try:
                full_story_link = post.find_element(By.XPATH, './/footer//a[contains(text(), "Full Story")]').get_attribute("href")
            except:
                print("Full Story link not found, skipping this post.")
                continue

            driver.execute_script(f"window.open('{full_story_link}', '_blank')")
            random_delay(1, 2)
            driver.switch_to.window(driver.window_handles[1])

            print(f"Start scraping search result post.")
            comments = post_scraping(seen_comments)
            all_comments.extend(comments)

            driver.close()
            random_delay(1, 2)
            driver.switch_to.window(driver.window_handles[0])
            random_delay(1, 2)

        try:
            see_more_results_btn = driver.find_element(By.XPATH, '//div[@id="see_more_pager"]/a')
            driver.execute_script("arguments[0].scrollIntoView(true);", see_more_results_btn)
            see_more_results_btn.click()
            random_delay(2, 3)
        except:
            break

# Usage
# To scrape group posts
# scrape_group_posts()

# To scrape search results
# search_url = "https://mbasic.facebook.com/search/posts/?q=Malta"
search_url = "https://mbasic.facebook.com/groups/631352428861145"

driver.get(search_url)
scrape_search_results()

# Save comments to CSV file upon normal completion
print("Saving comments to CSV file.")
save_comments_to_csv(all_comments)
print("Comments saved to CSV file.")