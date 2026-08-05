import os
import re
import time
import httpx
import chromadb
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

# Hugging Face inference configuration
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
# If user token is placeholder, treat as empty (falls back to rate-limited public extraction)
if HF_TOKEN.startswith("hf_your_token"):
    HF_TOKEN = ""

API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"

def get_embedding(text: str) -> list[float]:
    """
    Generate semantic vector embedding for the input text using Hugging Face Inference API.
    Uses sentence-transformers/all-MiniLM-L6-v2 (384 dimensions) for maximum speed and compatibility.
    """
    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    # Try up to 3 times in case of transient API delays
    for attempt in range(3):
        try:
            r = httpx.post(
                API_URL,
                headers=headers,
                json={"inputs": text},
                timeout=15.0
            )
            
            # Hugging Face sometimes loads the model on demand, returning a 503 error with 'estimated_time'
            if r.status_code == 503:
                data = r.json()
                wait_time = min(data.get("estimated_time", 3.0), 5.0)
                logger.warning(f"Hugging Face model loading (503). Waiting {wait_time}s (attempt {attempt + 1}/3)...")
                time.sleep(wait_time)
                continue
                
            r.raise_for_status()
            vector = r.json()
            
            # Confirm response is a list of floats
            if isinstance(vector, list) and len(vector) > 0:
                # If nested list (sometimes returned by feature-extraction), flatten it
                if isinstance(vector[0], list):
                    vector = vector[0]
                return [float(val) for val in vector]
                
            raise ValueError(f"Unexpected response format from HF API: {type(vector)}")
            
        except Exception as e:
            if attempt == 2:
                logger.error(f"Failed to generate embedding via Hugging Face API: {e}")
                # Return dummy vector on ultimate failure to avoid server crash
                return [0.0] * 384
            time.sleep(1.0)
            
    return [0.0] * 384

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
client = chromadb.PersistentClient(path=db_path)

# Initialize/Get the collection with ExpenseTracker domain namespace
collection = client.get_or_create_collection("expensetracker_knowledge")

def generate_standalone_query(question, history):
    if not history:
        return question
        
    q_lower = question.lower().strip()
    
    # Track domain entities
    entities = {
        "telegram": "Telegram bot setup",
        "chat id": "Telegram bot setup link",
        "chat_id": "Telegram bot setup link",
        "budget": "Budgets weekly monthly limit",
        "goal": "Goals target completion tracker",
        "reminder": "Reminders bills overdue alerts",
        "sub": "Subscriptions active alerts",
        "recurring": "Recurring Transactions weekly monthly",
        "export": "Spreadsheet export CSV Excel format",
        "attachment": "Receipt invoice attachment uploads"
    }
    
    # Check if current question already contains entity
    has_entity = any(e in q_lower for e in entities)
    if has_entity:
        return question
        
    # Scan history backwards to find latest topic
    found_entity = None
    for msg in reversed(history):
        content_lower = msg.get("content", "").lower()
        for key, name in entities.items():
            if key in content_lower:
                found_entity = name
                break
        if found_entity:
            break
            
    if found_entity:
        enriched_query = f"{question} {found_entity}"
        logger.info(f"[RAG] Query enriched: '{question}' -> '{enriched_query}'")
        return enriched_query
        
    return question

def tokenize(text):
    return set(re.findall(r'[a-z0-9]+', text.lower()))

def keyword_search(query, all_docs, top_k=5):
    query_tokens = tokenize(query)
    scores = []
    
    for doc, meta, doc_id in zip(all_docs["documents"], all_docs["metadatas"], all_docs["ids"]):
        doc_tokens = tokenize(doc)
        overlap = len(query_tokens.intersection(doc_tokens))
        
        phrase_bonus = 0
        if query.lower() in doc.lower():
            phrase_bonus = 8
            
        alias_bonus = 0
        aliases = {
            "telegram": ["telegram setup", "chat id", "link telegram", "connect telegram", "webhook"],
            "dashboard": ["charts", "visual", "graphs", "pie", "area"],
            "export": ["excel", "csv", "download", "sheet"],
            "import": ["upload", "attachment", "receipt", "invoice"]
        }
        for key, synonyms in aliases.items():
            if key in query.lower():
                for syn in synonyms:
                    if syn in doc.lower():
                        alias_bonus += 3
        
        score = overlap + phrase_bonus + alias_bonus
        if score > 0:
            scores.append((doc_id, score, doc, meta))
            
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]

_cached_all_docs = None

def get_all_docs():
    global _cached_all_docs
    if _cached_all_docs is None:
        try:
            _cached_all_docs = collection.get()
            logger.info(f"[RAG] Loaded {len(_cached_all_docs['documents'])} chunks into keyword search cache.")
        except Exception as e:
            logger.error(f"[RAG] Failed to load all docs for keyword search: {str(e)}")
            _cached_all_docs = {"documents": [], "metadatas": [], "ids": []}
    return _cached_all_docs

def retrieve_context_with_sources(question, history=None, top_k=5):
    standalone_query = generate_standalone_query(question, history)
    
    aliases = {
        "telegram": "Telegram setup link bot Chat ID connecting Settings",
        "chat id": "Telegram setup link bot Chat ID connecting Settings",
        "chat_id": "Telegram setup link bot Chat ID connecting Settings",
        "budget": "Budgets tracking category limits weekly monthly",
        "goal": "Goals target amount progress percentage",
        "reminder": "Reminders overdue status schedule bills",
        "sub": "Subscriptions recurring renewal alerts",
        "recurring": "Recurring transactions weekly monthly automated",
        "export": "Export CSV Excel formatting date filters",
        "import": "Invoice receipt attachment file upload"
    }
    
    search_query = standalone_query
    for alias, actual in aliases.items():
        if alias in standalone_query.lower():
            search_query += f" {actual}"

    # Vector search (using Hugging Face API embedding)
    _vs_start = time.time()
    query_embedding = get_embedding(search_query)
    
    vector_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    _vs_elapsed = time.time() - _vs_start
    logger.info(f"[RAG] ChromaDB vector search completed in {_vs_elapsed:.3f}s")

    vector_docs = vector_results["documents"][0]
    vector_metadatas = vector_results["metadatas"][0]
    vector_ids = vector_results["ids"][0]

    # Keyword Search
    all_docs = get_all_docs()
    _kw_start = time.time()
    keyword_results = keyword_search(standalone_query, all_docs, top_k=top_k)
    _kw_elapsed = time.time() - _kw_start
    logger.info(f"[RAG] Keyword search completed in {_kw_elapsed:.3f}s")
    
    # Merge results (Hybrid search)
    merged_candidates = []
    seen_ids = set()
    
    for doc, meta, doc_id in zip(vector_docs, vector_metadatas, vector_ids):
        merged_candidates.append((doc, meta, doc_id))
        seen_ids.add(doc_id)
        
    for doc_id, score, doc, meta in keyword_results:
        if doc_id not in seen_ids:
            if score >= 8:
                merged_candidates.insert(0, (doc, meta, doc_id))
            else:
                merged_candidates.append((doc, meta, doc_id))
            seen_ids.add(doc_id)
            
    final_candidates = merged_candidates[:top_k]
    
    # Sources list
    sources = []
    seen_urls = set()
    
    for doc, meta, doc_id in final_candidates:
        if meta and "url" in meta:
            url = meta["url"]
            title = meta.get("title", url)
            if url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "title": title,
                    "url": url
                })
                
    context_text = "\n\n".join([f"Source: {meta.get('title', 'ExpenseTracker Page')} ({meta.get('url', '')})\nContent: {doc}" for doc, meta, doc_id in final_candidates])
    
    # Evaluate relevance dynamically
    stop_words = {"what", "is", "are", "the", "a", "an", "of", "in", "on", "at", "for", "to", "with", "about", "how", "who", "where", "why", "you", "i", "do", "does", "did", "can", "could", "would", "should"}
    query_tokens = tokenize(standalone_query) - stop_words
    
    is_relevant = False
    if keyword_results and keyword_results[0][1] >= 8:
        is_relevant = True
    elif query_tokens:
        for doc, meta, doc_id in final_candidates[:4]:
            doc_tokens = tokenize(doc)
            overlap = query_tokens.intersection(doc_tokens)
            if len(overlap) >= 1:
                is_relevant = True
                break
                
    return context_text, sources, is_relevant