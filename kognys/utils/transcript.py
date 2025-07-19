# kognys/utils/transcript.py
from copy import deepcopy
from typing import List, Dict, Any

def append_entry(
    transcript: List[Dict[str, Any]],
    agent: str,
    action: str,
    details: str | None = None,
    output: Any | None = None
) -> List[Dict[str, Any]]:
    new_log = deepcopy(transcript)
    new_log.append({
        "agent": agent,
        "action": action,
        **({"details": details} if details else {}),
        **({"output": output} if output is not None else {})
    })
    return new_log
