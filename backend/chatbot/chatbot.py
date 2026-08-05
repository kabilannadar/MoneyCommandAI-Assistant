import json
import time
import asyncio
from chatbot.intent import detect_intent
from chatbot.web_search import search_web, should_use_web_search
from utils.logger import logger

# Modular components
import config
groq_client = config.groq_client

from chatbot.security import (
    is_vulgar,
    is_negative
)
from chatbot.cache import chat_cache, get_cache_key
from chatbot.prompts import get_system_prompt
from chatbot.responses import REPLIES

# Conditional RAG imports to maintain original behavior
try:
    from rag.rag import retrieve_context_with_sources
    RAG_AVAILABLE = True
except Exception as e:
    logger.error(f"Could not import RAG modules in chatbot service: {e}")
    RAG_AVAILABLE = False

def format_history(history):
    formatted = []
    for msg in history:
        formatted.append({
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["content"]
        })
    return formatted

# Track prompt count in memory per session
session_prompts = {}  # session_id -> count

# ---------------------------------------------------------
# Streaming SSE Generator
# ---------------------------------------------------------
async def response_generator(
    message: str,
    history: list,
    client_ip: str,
    local_time: str = None,
    local_day: str = None,
    local_date: str = None,
    session_id: str = None,
    user_id: int = None,
):
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    ist = _tz(_td(hours=5, minutes=30))
    user_start_time = _dt.now(ist)

    if session_id:
        session_prompts[session_id] = session_prompts.get(session_id, 0) + 1

    # ---------------------------------------------------------
    # Safety & Exclusion Intercepts
    # ---------------------------------------------------------
    msg_clean = message.strip()
    
    # 1. Vulgar prompt check
    if is_vulgar(msg_clean):
        logger.warning(f"Safety block triggered: vulgar prompt from IP {client_ip}: '{message}'")
        reply = REPLIES["vulgar"]
        for char in reply:
            yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
            await asyncio.sleep(0.002)
        yield f"data: {json.dumps({'type': 'suggestions', 'content': []})}\n\n"
        yield f"data: {json.dumps({'type': 'citations', 'content': []})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
        return

    # 2. Negative prompt check
    if is_negative(msg_clean):
        logger.warning(f"Safety block triggered: negative prompt from IP {client_ip}: '{message}'")
        reply = REPLIES["negative"]
        for char in reply:
            yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
            await asyncio.sleep(0.002)
        yield f"data: {json.dumps({'type': 'suggestions', 'content': []})}\n\n"
        yield f"data: {json.dumps({'type': 'citations', 'content': []})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
        return

    cache_key = get_cache_key(message, history, local_time)

    # Check cache first
    cached_val = chat_cache.get(cache_key)
    if cached_val:
        logger.info(f"Cache HIT: serving cached response for message preview '{message[:40]}'")
        # Stream cached text
        for char in cached_val["text"]:
            yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
            await asyncio.sleep(0.002)  # Subtle artificial delay for smooth rendering
        # Stream cached empty suggestions and citations
        yield f"data: {json.dumps({'type': 'suggestions', 'content': []})}\n\n"
        yield f"data: {json.dumps({'type': 'citations', 'content': []})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
        return
    else:
        logger.info(f"Cache MISS: no cached response for message preview '{message[:40]}'")

    # ---------------------------------------------------------
    # Heuristic Intercept for Working Hours / Operational Timings
    # ---------------------------------------------------------
    msg_lower = message.lower().strip()
    is_hours_query = any(kw in msg_lower for kw in ["working hour", "office hour", "working time", "office time", "opening hour", "closing hour", "operation hour", "shift timing", "office timing", "work hour", "shift hour"]) or \
                     (any(kw in msg_lower for kw in ["timing", "hour", "when"]) and any(kw in msg_lower for kw in ["open", "close", "work", "office"]))
                     
    if is_hours_query:
        logger.info(f"Heuristic working hours intercept triggered for message: '{message}'")
        reply = REPLIES["working_hours"]
        
        # Stream the response
        for char in reply:
            yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
            await asyncio.sleep(0.002)
            
        yield f"data: {json.dumps({'type': 'suggestions', 'content': []})}\n\n"
        yield f"data: {json.dumps({'type': 'citations', 'content': []})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
        return

    # ---------------------------------------------------------
    # Heuristic Intercept for Price / Fees / Salary / Compensation
    # ---------------------------------------------------------
    is_price_salary_query = any(kw in msg_lower for kw in ["price", "pricing", "cost", "fee", "fees", "charge", "charges", "rate", "rates", "tuition", "subscription", "salary", "package", "pay", "compensation", "stipend", "ctc", "wage", "remuneration", "income", "payout", "earnings"]) or \
                            (any(kw in msg_lower for kw in ["how much"]) and not any(kw in msg_lower for kw in ["time", "experience", "exp"]))
                      
    if is_price_salary_query:
        logger.info(f"Heuristic pricing/salary intercept triggered for message: '{message}'")
        reply = REPLIES["pricing_salary"]
        
        # Stream the response
        for char in reply:
            yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
            await asyncio.sleep(0.002)
            
        yield f"data: {json.dumps({'type': 'suggestions', 'content': []})}\n\n"
        yield f"data: {json.dumps({'type': 'citations', 'content': []})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
        return


    # ── Recommended Flow Implementation ──────────────────────────────────────────
    # Step 1: Detect intent first (fast, no RAG needed yet)
    greetings = {
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
        "how are you", "who are you", "what is your name", "hola", "yo",
        "tell me about yourself", "help", "greet", "greetings",
        "thank you", "thanks", "bye", "goodbye", "see you"
    }
    q_clean = message.strip().lower().rstrip("?!.")
    is_greeting = q_clean in greetings or any(q_clean.startswith(g + " ") for g in greetings)

    # Determine if this is a short follow-up query to inherit previous query context
    query_to_search = message
    followup_words = {
        "and", "more", "what else", "next", "then", "anything else", 
        "continue", "else", "what more", "tell me more"
    }
    is_followup = q_clean in followup_words and history
    if is_followup:
        last_user_query = None
        for msg in reversed(history):
            if msg["role"] == "user":
                last_user_query = msg["content"]
                break
        if last_user_query:
            query_to_search = last_user_query
            logger.info(f"Follow-up short query detected: '{message}'. Inheriting previous query context: '{last_user_query}'")

    context = ""
    has_context = False
    citations = []

    from auth.admin_config import get_setting
    db_rag = await get_setting("ENABLE_RAG", "false")
    enable_rag = db_rag.lower() == "true"

    db_live = await get_setting("ENABLE_LIVE_SUPPORT", "true")
    enable_live_support = db_live.lower() == "true"

    if enable_rag and RAG_AVAILABLE:
        logger.info("RAG ENABLED — retrieving context from ChromaDB.")
        try:
            context, sources, is_relevant = retrieve_context_with_sources(query_to_search, history)
            if context.strip():
                has_context = True
                citations = [{"title": s["title"], "url": s["url"]} for s in sources]
                logger.info(f"RAG context retrieved successfully: {context[:100]}...")
            else:
                logger.info("RAG returned no relevant context for this query.")
        except Exception as e:
            logger.error(f"Failed to retrieve RAG context: {e}")
    else:
        logger.info(f"RAG DISABLED — skipping context retrieval (ENABLE_RAG={enable_rag}, RAG_AVAILABLE={RAG_AVAILABLE}).")

    try:
        intent = detect_intent(query_to_search, has_context=has_context)
    except Exception as e:
        logger.error(f"Intent detection failed. Fallback to GENERAL_KNOWLEDGE: {e}")
        intent = "GENERAL_KNOWLEDGE"

    web_context = ""

    # Check if we should run web search as a fallback
    if not is_greeting:
        if should_use_web_search(query_to_search, has_rag_context=False):
            try:
                web_context = search_web(query_to_search, max_results=2)
                if web_context:
                    logger.info(f"Web search executed. Augmenting context for query: '{query_to_search}'")
            except Exception as e:
                logger.error(f"Web search execution failed: {e}")

    logger.info(f"Chat request - Message: '{message}' | Search: '{query_to_search}' | Intent: {intent} | RAG Context: {has_context} | Web Search: {bool(web_context)}")
    
    system_prompt = get_system_prompt(intent, context, has_context=has_context, web_context=web_context, local_time=local_time, local_day=local_day, local_date=local_date, query=query_to_search, history=history, enable_live_support=enable_live_support)

    def _make_groq_call(temperature=0.5):
        return groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                *format_history(history),
                {"role": "user", "content": message}
            ],
            temperature=temperature,
            max_tokens=600,
            stream=True
        )

    # Call Groq Streaming — retry once with higher temperature on empty-output error
    response = None
    groq_start = time.time()
    for attempt, temp in enumerate([0.7, 0.85]):
        try:
            response = _make_groq_call(temperature=temp)
            groq_ttfb = time.time() - groq_start
            logger.info(f"Groq API call succeeded (attempt {attempt+1}, temp={temp}) — TTFB: {groq_ttfb:.3f}s")
            break
        except Exception as e:
            err_str = str(e)
            logger.error(f"Groq API call attempt {attempt+1} failed after {time.time()-groq_start:.3f}s: {err_str}")
            if attempt == 1 or "empty" not in err_str.lower():
                yield f"data: {json.dumps({'type': 'token', 'content': 'Sorry, I encountered an error. Please try again.'})}\n\n"
                yield "data: {\"type\": \"done\"}\n\n"
                return

    if response is None:
        yield f"data: {json.dumps({'type': 'token', 'content': 'Sorry, I could not get a response. Please try again.'})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
        return

    full_response_text = ""
    stream_start = time.time()
    for chunk in response:
        token = chunk.choices[0].delta.content
        if token:
            full_response_text += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
    stream_elapsed = time.time() - stream_start
    total_elapsed = time.time() - groq_start
    logger.info(
        f"Groq streaming complete — tokens: {len(full_response_text)} chars, "
        f"stream: {stream_elapsed:.3f}s, total: {total_elapsed:.3f}s"
    )

    # ── Upsert session conversation JSON ────────────────────────────────────
    # Each unique frontend session_id = its own new ChatSession record in the DB.
    # The full conversation (history + current exchange) is stored as a JSON array.
    if session_id:
        try:
            from db.database import AsyncSessionLocal
            from db.models import ChatSession, SessionType
            from sqlalchemy import select
            user_time_iso = user_start_time.isoformat()
            assistant_time_iso = _dt.now(ist).isoformat()

            async with AsyncSessionLocal() as db:
                sess_q = await db.execute(
                    select(ChatSession).where(
                        ChatSession.frontend_session_id == session_id
                    )
                )
                chat_sess = sess_q.scalar_one_or_none()

                if not chat_sess:
                    # Always create a new record per frontend session UUID
                    chat_sess = ChatSession(
                        user_id=user_id,
                        frontend_session_id=session_id,
                        session_type=SessionType.ai,
                    )
                    db.add(chat_sess)
                    
                    # If starting fresh, initialize from request history payload
                    db_conv = []
                    for msg in history:
                        entry = {"role": msg["role"], "content": msg["content"]}
                        if "timestamp" in msg:
                            entry["timestamp"] = msg["timestamp"]
                        else:
                            entry["timestamp"] = user_time_iso
                        db_conv.append(entry)
                else:
                    if user_id and not chat_sess.user_id:
                        chat_sess.user_id = user_id
                    try:
                        db_conv = json.loads(chat_sess.conversation_json) if chat_sess.conversation_json else []
                    except Exception:
                        db_conv = []
                    
                    # Fallback to history payload if DB has no messages but history has them
                    if not db_conv and history:
                        for msg in history:
                            entry = {"role": msg["role"], "content": msg["content"]}
                            if "timestamp" in msg:
                                entry["timestamp"] = msg["timestamp"]
                            db_conv.append(entry)

                # Append current user and assistant turns
                db_conv.append({"role": "user",      "content": message,                     "timestamp": user_time_iso})
                db_conv.append({"role": "assistant",  "content": full_response_text.strip(), "timestamp": assistant_time_iso})

                chat_sess.conversation_json = json.dumps(db_conv)
                await db.commit()

                logger.info(f"Session '{session_id}' JSON history updated ({len(db_conv)} turns) in DB.")
        except Exception as e:
            logger.error(f"Failed to upsert session JSON history: {e}")

    yield f"data: {json.dumps({'type': 'suggestions', 'content': []})}\n\n"
    yield f"data: {json.dumps({'type': 'citations', 'content': citations})}\n\n"

    if enable_live_support and session_id and session_prompts.get(session_id, 0) >= 3:
        yield f"data: {json.dumps({'type': 'suggest_live_support'})}\n\n"

    yield "data: {\"type\": \"done\"}\n\n"

    # Save to cache
    chat_cache.set(cache_key, {
        "text": full_response_text.strip(),
        "suggestions": [],
        "citations": citations
    })
