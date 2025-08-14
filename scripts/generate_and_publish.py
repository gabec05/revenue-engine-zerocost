import os
import openai
from airtable import Airtable
from dotenv import load_dotenv
import re
import datetime

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
airtable = Airtable(os.getenv("AIRTABLE_BASE_ID"), os.getenv("AIRTABLE_TABLE_NAME"), api_key=os.getenv("AIRTABLE_API_KEY"))
markdown_path = "content/"
keyword_batch_size = 5

with open("prompts.md", "r") as f:
    prompts = f.read()

affiliate_links = {
    "standing desk": "https://amzn.to/3P2sWzX", # REPLACE WITH YOUR AMAZON LINKS
    "ergonomic chair": "https://amzn.to/4Q3tXyY", # REPLACE WITH YOUR AMAZON LINKS
    "monitor light bar": "https://amzn.to/4R4uYzZ", # REPLACE WITH YOUR AMAZON LINKS
    "webcam": "https://amzn.to/3E5rWzX" # REPLACE WITH YOUR AMAZON LINKS
}

def generate_article(keyword):
    """Generate content using LLM."""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompts},
                {"role": "user", "content": f"Generate a comprehensive, SEO-optimized blog post for the keyword: '{keyword}'"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating content for {keyword}: {e}")
        return None

def insert_affiliate_links(content):
    """Find product names and replace with affiliate links."""
    for product, link in affiliate_links.items():
        content = re.sub(r'\b' + re.escape(product) + r'\b', f"[{product}]({link})", content, flags=re.IGNORECASE)
    return content

def save_content(keyword, content):
    """Save the content to a markdown file with Hugo front matter."""
    slug = keyword.lower().replace(" ", "-").replace("?", "").replace(":", "").replace("/", "")
    filename = f"{slug}.md"
    filepath = os.path.join(markdown_path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: \"{keyword}\"\ndate: \"{datetime.datetime.now().isoformat()}\"\nslug: \"{slug}\"\n---\n\n")
        f.write(content)
    print(f"Saved article for {keyword} to {filepath}")
    return filepath

def process_keywords():
    records = airtable.get_all(view='To Process', max_records=keyword_batch_size)
    if not records:
        print("No new keywords to process.")
        return

    for record in records:
        keyword = record['fields']['Keyword']
        if not keyword:
            continue
        
        print(f"Processing keyword: {keyword}")
        article_content = generate_article(keyword)
        
        if article_content:
            article_content_with_links = insert_affiliate_links(article_content)
            save_content(keyword, article_content_with_links)
            airtable.update(record['id'], {'Status': 'Published'})
            print(f"Successfully processed and saved: {keyword}")

if __name__ == "__main__":
    process_keywords()
