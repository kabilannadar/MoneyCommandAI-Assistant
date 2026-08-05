import time
import json
import hashlib
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------
# In-Memory Cache
# ---------------------------------------------------------
class ResponseCache:
    def __init__(self, ttl=300, max_size=200):
        self.cache = {}
        self.ttl = ttl
        self.max_size = max_size
        
    def get(self, key):
        if key in self.cache:
            val, expiry = self.cache[key]
            if time.time() < expiry:
                print(f"[CACHE HIT] Key: {key[:8]}...")
                return val
            else:
                del self.cache[key]
        return None
        
    def set(self, key, val):
        if len(self.cache) >= self.max_size:
            # Evict oldest entry
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        self.cache[key] = (val, time.time() + self.ttl)

chat_cache = ResponseCache(ttl=600) # 10 minutes TTL
chat_cache.cache.clear() # Force clear cache on code changes

def get_cache_key(message: str, history: list, local_time: str = None) -> str:
    # Determine time of day from the browser-supplied local_time string so the
    # cache doesn't serve morning greetings in the evening (or vice-versa).
    hour = 12  # default to afternoon if we can't parse
    if local_time:
        try:
            import re
            time_match = re.search(r'(\d{1,2}):\d{2}\s*(AM|PM)', local_time, re.IGNORECASE)
            if time_match:
                raw_hour = int(time_match.group(1))
                period = time_match.group(2).upper()
                hour = (raw_hour % 12) + (12 if period == "PM" else 0)
        except Exception:
            pass
    else:
        # Fallback to IST
        from datetime import datetime, timezone, timedelta
        utc_now = datetime.now(timezone.utc)
        user_now = utc_now + timedelta(hours=5, minutes=30)
        hour = user_now.hour

    if 5 <= hour < 12:
        time_of_day = "morning"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 22:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    # Hash query, history, and time_of_day to form a unique cache key
    payload = {
        "message": message.strip().lower(),
        "history": [{"role": m["role"], "content": m["content"].strip().lower()} for m in history],
        "time_of_day": time_of_day
    }
    payload_str = json.dumps(payload, sort_keys=True)
    return hashlib.md5(payload_str.encode("utf-8")).hexdigest()
