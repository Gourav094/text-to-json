import ollama
import json 
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import threading
import re

model="phi3:mini"

app = FastAPI()

_metrics = {"total": 0, "success": 0, "fail": 0}
_metrics_lock = threading.Lock()

system_prompt="""
You are a strict information extraction engine.
Rules:
- Extract ONLY information explicitly present. 
- Do NOT infer or assume. Not even a single line of explanation
- Do NOT add new fields
- Use null if missing. Don't ask for missing fields
- Output ONLY valid JSON

Output: JSON

Schema:
{
    "name": string or null,
    "working_at": string or null,
    "education": string or null,
    "email": string or null,
    "phone": string or null,
    "address": string or null
}
"""

class ExtractRequest(BaseModel):
    text: str
    retries: int = 2

phone = re.compile(r"^[+()\d\s-]{6,}$")
email = re.compile(r".+@.+\..+")

def sanitize_data(data: dict) -> dict:
    if data.get("working_at") and phone.match(data["working_at"]):
        data["working_at"] = None
    if data.get("email") and not email.match(data["email"]):
        data["email"] = None
    if data.get("phone") and not phone.match(data["phone"]):
        data["phone"] = None
    return data

@app.post("/llm/extract/profiles")
def profile_extractor(req: ExtractRequest):
    print(f"Using model :: {model}")
    start = time.perf_counter()
    attempts = 0
    last_error = None
    with _metrics_lock:
        _metrics['total'] += 1

    try:
        for attempts in range(req.retries + 1):
            try:
                response=ollama.chat(
                    model=model,
                    messages=[
                        {"role":"system", "content":system_prompt},
                        {"role":"user" , "content": req.text}
                    ],
                )
            
                raw = response["message"]["content"].strip()
                if not raw:
                    raise ValueError("Empty response from model")
                data=json.loads(raw)
                data  = sanitize_data(data)
                print(f"Extracted data: {data}")
                with _metrics_lock:
                    _metrics['success'] += 1

                return {
                    "name": data.get("name"),
                    "organization": data.get("working_at"),
                    "education": data.get("education"),
                    "email": data.get("email"),
                    "phone": data.get("phone"),
                    "address": data.get("address"),
                }
            except Exception as e:
                    last_error = e
                    print(f"Error in generating response from llm")
                    continue
            
        with _metrics_lock:
            _metrics['fail'] += 1
        raise HTTPException(status_code=500, detail=f"Extraction failed after {attempts} retries: {last_error}")
    
    finally:
        latency = (time.perf_counter() - start) * 1000.0
        with _metrics_lock:
            success_count = _metrics['success']
            total = _metrics['total']
        success_rate = (success_count / total) * 100 if total else 0.0
        print(f"observability metrics: retry_count={attempts} latency_ms={latency:.2f} success_rate={success_rate:.2f}%")