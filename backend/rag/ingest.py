import os
import re
import glob
import time
import httpx
import chromadb
from dotenv import load_dotenv

# Ensure we read environment from backend directory
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
if HF_TOKEN.startswith("hf_your_token"):
    HF_TOKEN = ""

API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")

def get_embedding(text: str) -> list[float]:
    """Generates embeddings using Hugging Face's hosted API, with a dummy vector fallback on offline/network errors."""
    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    for attempt in range(3):
        try:
            r = httpx.post(
                API_URL,
                headers=headers,
                json={"inputs": text},
                timeout=20.0
            )
            if r.status_code == 503:
                # Model loading, sleep and try again
                data = r.json()
                wait_time = min(data.get("estimated_time", 4.0), 5.0)
                print(f"HF API loading model... waiting {wait_time}s (attempt {attempt + 1}/3)")
                time.sleep(wait_time)
                continue
                
            r.raise_for_status()
            vector = r.json()
            if isinstance(vector, list) and len(vector) > 0:
                if isinstance(vector[0], list):
                    vector = vector[0]
                return [float(v) for v in vector]
            raise ValueError(f"Invalid format: {type(vector)}")
        except Exception as e:
            # Check for network resolution/offline errors to print a clear warning
            if "getaddrinfo failed" in str(e) or "ConnectError" in str(e):
                print(f"WARNING: Network offline/resolution failed. Falling back to dummy vector for local development.")
                return [0.0] * 384
            if attempt == 2:
                print(f"ERROR: Failed to embed text chunk: {e}")
                return [0.0] * 384
            time.sleep(2.0)
    return [0.0] * 384

def clean_jsx_content(content: str) -> str:
    """Cleans JSX file content into readable plain text blocks, removing components/styling markup."""
    # Remove imports and setup
    content = re.sub(r'import\s+.*?;', '', content, flags=re.DOTALL)
    # Remove SVG paths/tags completely
    content = re.sub(r'<svg.*?>.*?</svg>', '', content, flags=re.DOTALL)
    content = re.sub(r'<path.*?>', '', content, flags=re.DOTALL)
    # Clean HTML/JSX tags
    content = re.sub(r'<[^>]+>', ' ', content)
    # Clean CSS classes / styling templates
    content = re.sub(r'className=".*?"', '', content)
    content = re.sub(r'\{\s*.*?\s*\}', '', content)
    # Compress whitespaces
    content = re.sub(r'\s+', ' ', content).strip()
    return content

def extract_chunks():
    chunks = []
    
    # ── 1. Read README.md ─────────────────────────────────────────────────────
    readme_path = "D:/ExpenseTracker/README.md"
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Split by markdown headers
        sections = re.split(r'(?=\n##\s+)', text)
        for i, s in enumerate(sections):
            s = s.strip()
            if s:
                chunks.append({
                    "text": s,
                    "title": f"Readme - Section {i+1}",
                    "url": "https://expensetrackertn.vercel.app/help"
                })
        print(f"Loaded {len(sections)} chunks from README.md")

    # ── 2. Read Frontend Page Layouts ─────────────────────────────────────────
    pages_glob = "D:/ExpenseTracker/frontend/src/pages/*.jsx"
    pages = glob.glob(pages_glob)
    
    for page_path in pages:
        filename = os.path.basename(page_path)
        pagename = filename.replace(".jsx", "")
        
        # Skip backups/non-user pages
        if "bak" in pagename or pagename in ("Auth", "Login", "Register"):
            continue
            
        with open(page_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        cleaned = clean_jsx_content(content)
        if len(cleaned) > 50:
            # Split into reasonable length chunks
            words = cleaned.split(" ")
            chunk_size = 80
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i+chunk_size]
                chunk_text = " ".join(chunk_words).strip()
                if len(chunk_text) > 40:
                    # Provide navigation URL mapping based on filename
                    url_path = pagename.lower()
                    if url_path == "dashboard":
                        url_path = ""
                    elif url_path == "telegramsetup":
                        url_path = "telegram"
                        
                    chunks.append({
                        "text": f"ExpenseTracker page '{pagename}' guide: {chunk_text}",
                        "title": f"App Page: {pagename}",
                        "url": f"https://expensetrackertn.vercel.app/{url_path}"
                    })
            print(f"Loaded page chunks for: {pagename}")
            
    return chunks

def run_ingestion():
    print(f"Initializing ChromaDB connection at: {DB_PATH}")
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    
    # Drop existing collection if it exists to refresh database cleanly
    try:
        chroma_client.delete_collection("expensetracker_knowledge")
        print("Dropped old 'expensetracker_knowledge' collection.")
    except Exception:
        pass
        
    collection = chroma_client.create_collection("expensetracker_knowledge")
    
    chunks = extract_chunks()
    if not chunks:
        print("No chunks found to ingest!")
        return
        
    print(f"Starting ingestion of {len(chunks)} text chunks...")
    
    documents = []
    metadatas = []
    ids = []
    embeddings = []
    
    for i, c in enumerate(chunks):
        text = c["text"]
        print(f"Ingesting [{i+1}/{len(chunks)}] embedding generation...")
        
        vector = get_embedding(text)
        embeddings.append(vector)
        documents.append(text)
        metadatas.append({
            "title": c["title"],
            "url": c["url"]
        })
        ids.append(f"doc_{i+1}")
        
    # Write to local ChromaDB
    collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print("Ingestion completed successfully!")

if __name__ == "__main__":
    run_ingestion()
