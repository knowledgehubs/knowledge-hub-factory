import os
import csv
import random
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
# Input/Output file names
INPUT_CSV_FILE = 'content-engine/new_keywords.csv'
PROCESSED_CSV_FILE = 'content-engine/processed_keywords.csv'

# Paths
BLOCKS_DIR = 'blocks/'
# Note: This path is relative to generator.py, going up one level (..) then into the sibling publisher content path
PUBLISHER_CONTENT_DIR = '../knowledge-hub/content/posts/' 

# Publishing Settings
NUM_POSTS_TO_GENERATE = 5 # Number of articles to generate and push per run
AFFILIATE_KEY_CHANCE = 0.6 # Probability of including an affiliate link (60%)

# Human Publishing Pattern (Random Delay in Seconds)
MIN_HUMAN_DELAY = 30
MAX_HUMAN_DELAY = 120

# Quality Requirements (English Structure)
H2_SECTIONS = ['Benefits-and-Advantages', 'Key-Challenges', 'Practical-Steps-to-Implement', 'Expert-Tips-and-Insights']
BLOCK_FILES = {
    'intro': 'intros.txt',
    'explanation': 'explanations.txt',
    'pros': 'pros.txt',
    'cons': 'cons.txt',
    'steps': 'steps.txt',
    'tips': 'tips.txt',
    'cta': 'cta.txt'
}
HUMAN_SIGNATURE = "\n---\n\n*Editor's Note: This guide was constructed by the Knowledge Hub engine to provide concise and deep insights into {keyword}. We hope it has been a valuable addition to your knowledge base.*\n"

# --- 2. CORE FUNCTIONS ---

def load_blocks():
    """Loads all blocks from text files."""
    blocks = {}
    for key, filename in BLOCK_FILES.items():
        try:
            with open(os.path.join(BLOCKS_DIR, filename), 'r', encoding='utf-8') as f:
                blocks[key] = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
             print(f"⚠️ Block file not found: {filename}")
             # Placeholder ensures the script doesn't crash if files are empty/missing
             blocks[key] = ['[Placeholder block content - please fill this file]'] 
    return blocks

def load_keywords():
    """Loads keywords from the main CSV file."""
    keywords_list = []
    if not os.path.exists(INPUT_CSV_FILE) or os.path.getsize(INPUT_CSV_FILE) == 0:
        return []

    with open(INPUT_CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if 'keyword' in row and 'title' in row:
                keywords_list.append(row)
    return keywords_list

def update_keywords_csv(remaining_keywords, processed_keywords):
    """Updates the CSV files, moving processed keywords to a dedicated file."""
    
    # Write the remaining (unprocessed) keywords back to the input file
    if remaining_keywords:
        fieldnames = ['keyword', 'title']
        with open(INPUT_CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(remaining_keywords)
    elif os.path.exists(INPUT_CSV_FILE):
        os.remove(INPUT_CSV_FILE)

    # Load previously processed data
    previous_processed = []
    if os.path.exists(PROCESSED_CSV_FILE) and os.path.getsize(PROCESSED_CSV_FILE) > 0:
        try:
            with open(PROCESSED_CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                previous_processed = list(reader)
        except Exception as e:
            print(f"Error reading previous processed CSV: {e}. Overwriting.")

    # Combine old and new processed data
    all_processed = previous_processed + processed_keywords
    
    # Write the combined list to the processed file
    if all_processed:
        fieldnames = ['keyword', 'title']
        with open(PROCESSED_CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_processed)


def generate_post_content(keyword_data, loaded_blocks):
    """Assembles content, applies structure, and quality controls."""
    keyword = keyword_data['keyword']
    title = keyword_data['title']
    
    affiliate_key = f'OFFER_{random.randint(100, 999)}' if random.random() < AFFILIATE_KEY_CHANCE else None

    # --- Content Assembly ---
    sections = []
    
    # 1. Intro
    intro_title = "Introduction: An Overview"
    intro = f"## {intro_title}\n\n" + random.choice(loaded_blocks['intro'])
    sections.append(intro.replace('{keyword}', keyword).replace('{title}', title))

    # 2. Body Sections (Randomized but structured)
    selected_h2 = random.sample(H2_SECTIONS, random.randint(3, 4))
    
    for h2_tag in selected_h2:
        section_content = ""
        block_key = ""
        
        if 'Benefits' in h2_tag:
            block_key = 'pros'
            section_content = random.choice(loaded_blocks['pros'])
        elif 'Challenges' in h2_tag:
            block_key = 'cons'
            section_content = random.choice(loaded_blocks['cons'])
        elif 'Steps' in h2_tag:
            block_key = 'steps'
            section_content = random.choice(loaded_blocks['steps'])
        elif 'Tips' in h2_tag:
            block_key = 'tips'
            section_content = random.choice(loaded_blocks['tips'])
        
        display_h2 = h2_tag.replace('-', ' ').title()
        
        sections.append(f"## {display_h2}\n\n" + section_content.replace('{keyword}', keyword))

    # 3. Conclusion (CTA)
    cta_text = random.choice(loaded_blocks['cta'])
    conclusion_title = "Conclusion: Final Thoughts and Next Steps"
    
    if affiliate_key:
        # This is the Hugo shortcode syntax that we will implement in the Publisher
        cta_text = cta_text.replace('[CTA_LINK]', f'{{{{< affiliate_link key="{affiliate_key}" text="Click Here to Start" >}}}}')
    else:
        cta_text = cta_text.replace('[CTA_LINK]', 'Visit a highly recommended resource here.') 

    sections.append(f"## {conclusion_title}\n\n" + cta_text.replace('{keyword}', keyword))
    
    # 4. Human Signature
    sections.append(HUMAN_SIGNATURE.replace('{keyword}', keyword))

    full_content = "\n\n".join(sections)
    return full_content, affiliate_key

def create_json_ld(title, date, url):
    """Creates JSON-LD Structured Data (Article) for SEO."""
    return f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title.replace('"', '\\"')}",
  "datePublished": "{date.isoformat()}",
  "mainEntityOfPage": "{url}",
  "publisher": {{
    "@type": "Organization",
    "name": "Knowledge Hub",
    "logo": {{
      "@type": "ImageObject",
      "url": "https://knowledgehubs.github.io/knowledge-hub/images/logo.png"
    }}
  }},
  "author": {{
    "@type": "Person",
    "name": "Knowledge Hub AI"
  }}
}}
</script>
"""

def generate_markdown_file(keyword_data, content, affiliate_key):
    """Assembles Front-Matter, JSON-LD, and content into a Markdown file."""
    title = keyword_data['title']
    keyword = keyword_data['keyword']
    
    # Simple English slug generation
    slug = title.lower().replace(' ', '-').replace(':', '').replace('/', '').replace('.', '').replace(',', '')[:60]
    
    # Random date within the last 10 minutes (for human-like timing)
    post_date = datetime.now() - timedelta(minutes=random.randint(1, 10))
    
    # Front Matter
    front_matter = f"""---
title: "{title}"
date: {post_date.isoformat()}
description: "{title[:140].strip()} - A deep dive into {keyword} and its key applications."
slug: "{slug}"
affiliate_key: "{affiliate_key if affiliate_key else ''}"
canonical: "/posts/{slug}/"
---
"""
    # JSON-LD
    json_ld = create_json_ld(title, post_date, f"/posts/{slug}/")
    
    # Final Content
    final_content = front_matter + "\n" + json_ld + "\n\n" + content
    
    # Save the file
    filename = f"{slug}.md"
    # Note: We create the file in the relative path that points to the Publisher's content folder
    filepath = os.path.join(PUBLISHER_CONTENT_DIR, filename)
    
    # Ensure the path exists before writing (important for CI environment)
    os.makedirs(os.path.dirname(filepath), exist_ok=True) 

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    return filepath

def execute_git_push(commit_message):
    """Executes the Git Commit operation (The Action handles the Push)."""
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    os.chdir('..') # Move to the factory root

    print("--- 🔄 Starting Git operations... ---")
    
    # 1. Add Files
    # Add files inside content-engine/ (CSV files) and new posts inside the relative publisher path
    os.system('git add content-engine/') 
    os.system(f'git add {PUBLISHER_CONTENT_DIR.replace("../", "")}') 

    # 2. Commit
    commit_command = f'git commit -m "{commit_message}"'
    os.system(commit_command)

    print("--- ✅ Commit successful. The Workflow will handle the secure Push. ---")
    
# --- 3. MAIN EXECUTION ---

if __name__ == "__main__":
    SYSTEM_MODE = os.environ.get('SYSTEM_MODE', 'TEST')
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    loaded_blocks = load_blocks()
    all_keywords = load_keywords()
    
    if not all_keywords:
        print("🛑 No new keywords to process in the input CSV. Script exiting.")
        exit(0)

    keywords_to_process_batch = random.sample(all_keywords, min(len(all_keywords), NUM_POSTS_TO_GENERATE))
    
    print(f"🎉 Starting generation and push of {len(keywords_to_process_batch)} articles in {SYSTEM_MODE} mode.")
    
    processed_count = 0
    processed_batch_data = [] 
    
    for data in keywords_to_process_batch:
        if SYSTEM_MODE == 'TEST':
            print(f"📝 TEST mode: Article '{data['title']}' generated. Skipping permanent update and push.")
            processed_batch_data.append(data) # Still mark as processed in test to see the next batch next time
            continue

        try:
            content, affiliate_key = generate_post_content(data, loaded_blocks)
            filepath = generate_markdown_file(data, content, affiliate_key)
            
            processed_batch_data.append(data) 
            processed_count += 1
            
            print(f"✅ Successfully generated {filepath}. Simulating human delay...")
            
            delay = random.randint(MIN_HUMAN_DELAY, MAX_HUMAN_DELAY)
            print(f"⏳ Delaying for {delay} seconds to simulate human pattern...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"❌ Failed to generate article '{data['title']}': {e}")
            
    # Final keyword management: remove processed keywords from the input list
    remaining_keywords = [k for k in all_keywords if k not in processed_batch_data]
    update_keywords_csv(remaining_keywords, processed_batch_data)

    if processed_count > 0 and SYSTEM_MODE == 'LIVE':
        commit_msg = f"AUTO: Publish {processed_count} new articles on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        execute_git_push(commit_msg)
        print("🚀 Script finished. The Workflow Action will now execute the secure push.")
    elif SYSTEM_MODE == 'LIVE':
         print("✅ Nothing new to commit or push.")
