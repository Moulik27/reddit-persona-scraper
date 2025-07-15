import os
import sys
import re
import time
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import google.generativeai as genai
from dotenv import load_dotenv

# --- CONFIG ---
REDDIT_BASE = "https://old.reddit.com"
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; RedditScraperBot/1.0)'}
MAX_POSTS = 50  # Limit for demo; adjust as needed
MAX_COMMENTS = 100

# --- GEMINI SETUP ---
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
if not GEMINI_API_KEY:
    print("[ERROR] Please set your Gemini API key in the GEMINI_API_KEY environment variable.")
    sys.exit(1)
genai.configure(api_key=GEMINI_API_KEY)

# --- SCRAPING FUNCTIONS ---
def get_username_from_url(url):
    match = re.search(r"reddit.com/user/([\w\-_.]+)/?", url)
    if match:
        return match.group(1)
    raise ValueError("Invalid Reddit user URL.")

def scrape_user_posts(username):
    posts = []
    after = None
    count = 0
    for page in range(5):  # Up to 5 pages
        url = f"{REDDIT_BASE}/user/{username}/submitted/?count={count}" + (f"&after={after}" if after else "")
        print(f"[DEBUG] Fetching posts page {page+1}: {url}")
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"[ERROR] Failed to fetch posts page {page+1} (status {resp.status_code})")
            break
        soup = BeautifulSoup(resp.text, 'html.parser')
        found = 0
        for post in soup.select('div.thing.link'):
            title = post.select_one('a.title')
            content = post.select_one('div.expando > div.usertext-body')
            link = post.get('data-permalink')
            post_data = {
                'title': title.text.strip() if title else '',
                'content': content.text.strip() if content else '',
                'url': REDDIT_BASE + link if link else ''
            }
            print(f"[DEBUG] Extracted post: Title='{post_data['title'][:60]}', URL={post_data['url']}")
            posts.append(post_data)
            found += 1
            if len(posts) >= MAX_POSTS:
                print(f"[INFO] Reached MAX_POSTS ({MAX_POSTS})")
                return posts
        print(f"[DEBUG] Found {found} posts on page {page+1}, total so far: {len(posts)}")
        next_button = soup.find('span', class_='next-button')
        if next_button and next_button.a:
            after = None
            url = next_button.a['href']
        else:
            print("[DEBUG] No next page button found for posts.")
            break
        time.sleep(1)
    print(f"[INFO] Total posts scraped: {len(posts)}")
    return posts

def scrape_user_comments(username):
    comments = []
    after = None
    count = 0
    for page in range(5):
        url = f"{REDDIT_BASE}/user/{username}/comments/?count={count}" + (f"&after={after}" if after else "")
        print(f"[DEBUG] Fetching comments page {page+1}: {url}")
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"[ERROR] Failed to fetch comments page {page+1} (status {resp.status_code})")
            break
        soup = BeautifulSoup(resp.text, 'html.parser')
        found = 0
        for comment in soup.select('div.thing.comment'):
            body = comment.select_one('div.usertext-body > div.md')
            link = comment.get('data-permalink')
            comment_data = {
                'body': body.text.strip() if body else '',
                'url': REDDIT_BASE + link if link else ''
            }
            print(f"[DEBUG] Extracted comment: Excerpt='{comment_data['body'][:60]}', URL={comment_data['url']}")
            comments.append(comment_data)
            found += 1
            if len(comments) >= MAX_COMMENTS:
                print(f"[INFO] Reached MAX_COMMENTS ({MAX_COMMENTS})")
                return comments
        print(f"[DEBUG] Found {found} comments on page {page+1}, total so far: {len(comments)}")
        next_button = soup.find('span', class_='next-button')
        if next_button and next_button.a:
            after = None
            url = next_button.a['href']
        else:
            print("[DEBUG] No next page button found for comments.")
            break
        time.sleep(1)
    print(f"[INFO] Total comments scraped: {len(comments)}")
    return comments

def build_prompt(posts, comments, username):
    prompt = f"""
You are an expert at building user personas from Reddit data. Given the following posts and comments from the user '{username}', generate a detailed user persona in the following format. Only use the provided data; do not guess or infer any information that is not explicitly present. If there is not enough information for a field, leave it blank or mark as 'Not enough data'.

---
Name: {username}
AGE: 
OCCUPATION: 
STATUS: 
LOCATION: 
TIER: 
ARCHETYPE: 

TRAITS: 

MOTIVATIONS:
- Convenience: 
- Wellness: 
- Speed: 
- Preferences: 
- Comfort: 
- Dietary Needs: 

PERSONALITY:
- Introvert/Extrovert: 
- Intuition/Sensing: 
- Feeling/Thinking: 
- Perceiving/Judging: 

QUOTE: ""

BEHAVIOUR & HABITS:

FRUSTRATIONS:

GOALS & NEEDS:

For each trait, motivation, habit, frustration, or goal, cite the specific post or comment (by quoting a short excerpt and/or providing the URL) that supports it. If there is not enough information, leave the field blank or mark as 'Not enough data'.

---

Posts:
"""
    for post in posts:
        prompt += f"\nTitle: {post['title']}\nContent: {post['content']}\nURL: {post['url']}\n"
    prompt += "\nComments:\n"
    for comment in comments:
        prompt += f"\nComment: {comment['body']}\nURL: {comment['url']}\n"
    return prompt

def get_persona_from_gemini(prompt):
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    return response.text

def main():
    if len(sys.argv) != 2:
        print("Usage: python reddit_persona.py <reddit_user_profile_url>")
        sys.exit(1)
    url = sys.argv[1]
    username = get_username_from_url(url)
    print(f"[INFO] Scraping posts for user: {username}")
    posts = scrape_user_posts(username)
    print(f"[INFO] Scraping comments for user: {username}")
    comments = scrape_user_comments(username)
    print(f"[INFO] Building prompt for Gemini API...")
    prompt = build_prompt(posts, comments, username)
    print(f"[INFO] Sending data to Gemini API...")
    persona = get_persona_from_gemini(prompt)
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{username}_persona.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(persona)
    print(f"[SUCCESS] Persona written to {output_file}")

if __name__ == "__main__":
    main() 