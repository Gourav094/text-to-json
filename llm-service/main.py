import ollama
import json 
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import threading
import re

model="mistral"

app = FastAPI()

_metrics = {"total": 0, "success": 0, "fail": 0}
_metrics_lock = threading.Lock()

profile_system_prompt="""
You are a strict information extraction engine.
Your task is to ONLY extract information that is EXPLICITLY stated in the text.
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
    attempts = 1
    last_error = None
    with _metrics_lock:
        _metrics['total'] += 1

    try:
        for attempts in range(req.retries + 1):
            try:
                response=ollama.chat(
                    model=model,
                    messages=[
                        {"role":"system", "content":profile_system_prompt},
                        {"role":"user" , "content": req.text}
                    ],
                )
            
                raw = response["message"]["content"].strip()
                if not raw:
                    raise ValueError("Profile: Output format is diff from json")
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
                    print(f"Profile Extraction failed")
                    continue
            
        with _metrics_lock:
            _metrics['fail'] += 1
        raise HTTPException(status_code=500, detail=f"Extraction failed after {attempts-1} retries: {last_error}")
    
    finally:
        latency = (time.perf_counter() - start) * 1000.0
        with _metrics_lock:
            success_count = _metrics['success']
            total = _metrics['total']
        success_rate = (success_count / total) * 100 if total else 0.0
        print(f"observability metrics: retry_count={attempts-1} latency_ms={latency:.2f} success_rate={success_rate:.2f}%")

project_system_prompt = """ 
You are a information extraction engine.
Your task is to ONLY extract information that is EXPLICITLY stated in the text.
Rules:
- Do NOT infer missing details. 
- Don't Assume. DO NOT add comments. not event a single word. Don't ask for missing fields 
- Do not add new fields. DO NOT rephrase or summarize.
- Output ONLY valid JSON. No text before or after.
- use null if missing. No text outside json
- Technologies must be concrete tools, languages, or frameworks (e.g., Node.js, Redis). 
Output: Json (Return exactly this schema)
Schema:
{
    "project_name": null,
    "description": null,
    "technologies": []
}
"""

@app.post("/llm/extract/project")
def project_extractor(req: ExtractRequest):
    last_error = None
    try:
        for attempt in range(req.retries + 1):
            try:
                response = ollama.chat(
                    model = model,
                    messages = [
                        {"role": "system", "content":project_system_prompt},
                        {"role": "user", "content" :req.text}
                    ]
                )
                raw = response["message"]["content"].strip()
                if not raw:
                    raise ValueError("Project: Output format is diff from json")
                
                data = json.loads(raw)
                return {
                    "project_name": data.get("project_name"),
                    "description": data.get("description"),
                    "technologies": data.get("technologies") or []
                }
            except Exception as e:
                last_error = e
                print("Project Extraction failed!")
                continue
        raise HTTPException(status_code=500, detail=f"Project extraction failed with error: {last_error}")
    finally:
        print(f"Project metrics: retry_count: {attempt+1}")


intent_system_prompt = """
Role: intent classifier
Task: Decide which extractors are needed for the given input
Rules:
- choose ONLY from a fixed list
- include ALL that apply
- do not invent new intents
- output ONLY JSON
- no explanation. no comment. don't infer missing 
List of extractors: "profile" or "Project"
Output format: {"intents" : ["profile" , "project"]}
"""

@app.post("/intents")
def intent_extractor(req: ExtractRequest) -> dict:
    print(f"model")
    attempt = 1
    last_error = None
    try:
        for attempt in range(1, req.retries + 1):
            try:
                response=ollama.chat(
                    model=model,
                    messages=[
                        {"role":"system", "content":intent_system_prompt},
                        {"role":"user" , "content":req.text}
                    ]
                )
                raw = response['message']['content'].strip()
                if not raw:
                    raise ValueError("Empty response from model")
                
                data = json.loads(raw)
                
                intents = data.get("intents") or []
                # if llm gives only "profile" - convert it into ["profile"]
                if isinstance(intents, str):
                    intents = [intents]
                intents = [str(i).lower() for i in intents]

                return {"intents": intents}

            except Exception as e:
                last_error=e
                print("Error in generating intent from llm")
                continue
        raise HTTPException(status_code=500, detail=f"Intent extraction failed with error: {last_error}")
    finally:
        print(f"attempt: {attempt + 1}")