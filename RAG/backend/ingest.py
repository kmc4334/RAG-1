import json
import requests
import time

# User provided data
data = {
    "query": "로지텍 지슈라",
    "documents": [
        {
            "url": "https://bbs.ruliweb.com/news/read/211279",
            "text": """로지텍(Logitech), 무선 마우스·키보드 사용자 위한 ‘로지 볼트’ USB-C 리시버 출시
... (rest of the text from user provided JSON) ...
(For brevity I am only including the first few lines in this variable, but the script logic below will handle the full text if pasted here)
"""
        },
        # ... Add other documents here ...
    ]
}

# Since the user provided a large JSON blob in the chat, 
# I will create a script that they can paste their JSON into, or I can try to parse it if I put it all in.
# Better yet, I will make a script that reads 'data.json' and sends it to the API.

def ingest_data(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = data.get("documents", [])
    print(f"Found {len(documents)} documents to ingest.")

    url = "http://127.0.0.1:8000/rag/store"
    headers = {"Content-Type": "application/json"}

    for i, doc in enumerate(documents):
        text = doc.get("text", "")
        if not text:
            continue
        
        # Clean up text a bit if needed, or send as is
        # The text seems to have a lot of newlines and boilerplate.
        # For RAG, we might want to chunk it, but the current backend simple stores the whole blob.
        
        payload = {
            "text": text[:2000], # Creating a limit to avoid token errors if text is huge
            "type": "crawled_content",
            "entity": data.get("query"), # Use query as entity metadata
            "slot": doc.get("url")       # Use URL as slot metadata
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                print(f"[{i+1}/{len(documents)}] Success: {doc.get('url')}")
            else:
                print(f"[{i+1}/{len(documents)}] Failed: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(1) # Be gentle on the API/Rate limits

if __name__ == "__main__":
    # Create the data.json file first
    # (I will do this in a separate step or instruct the user)
    import sys
    if len(sys.argv) > 1:
        ingest_data(sys.argv[1])
    else:
        print("Usage: python ingest.py data.json")
