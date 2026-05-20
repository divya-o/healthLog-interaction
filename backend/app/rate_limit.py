from datetime import datetime, timedelta, timezone
from collections import defaultdict

from fastapi import HTTPException, status

#rate limit store 
# { rep_id: { "log_interaction": {"count": 3, "reset_at": datetime}, ... } }

_llm_rate_limits: dict = defaultdict(lambda: {})

LIMITS = {
    "log_interaction": {"calls": 10, "minutes": 1},    
    "edit_interaction": {"calls": 10, "minutes": 1},   
    "chat_message": {"calls": 20, "minutes": 1},       
}


def check_llm_rate_limit(rep_id: str, operation: str) -> None:
    
    if operation not in LIMITS:
        return  

    limit_config = LIMITS[operation]
    max_calls = limit_config["calls"]
    window_minutes = limit_config["minutes"]

    
    rep_tracker = _llm_rate_limits[rep_id]
    if operation not in rep_tracker:
        rep_tracker[operation] = {"count": 0, "reset_at": datetime.now(timezone.utc)}

    tracker = rep_tracker[operation]
    now = datetime.now(timezone.utc)

    
    if now >= tracker["reset_at"]:
        tracker["count"] = 0
        tracker["reset_at"] = now + timedelta(minutes=window_minutes)

    if tracker["count"] >= max_calls:
        reset_in_seconds = int((tracker["reset_at"] - now).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"LLM rate limit exceeded. {operation}: "
                   f"{max_calls} calls per {window_minutes} minute(s). "
                   f"Try again in {reset_in_seconds} second(s).",
        )

    
    tracker["count"] += 1


def reset_llm_rate_limit(rep_id: str, operation: str) -> None:
   
    if rep_id in _llm_rate_limits and operation in _llm_rate_limits[rep_id]:
        del _llm_rate_limits[rep_id][operation]