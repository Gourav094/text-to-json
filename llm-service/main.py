import ollama
import json 
from fastapi import FastAPI
from pydantic import BaseModel

model="phi3:mini"

app = FastAPI()

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

@app.post("/llm/extract/profiles")
def profile_extractor(req: ExtractRequest):

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
        print(f"Extracted data: {data}")
        return {
            "name": data.get("name"),
            "organization": data.get("working_at"),
            "education": data.get("education"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "address": data.get("address"),
        }

    except Exception as e:
        print(f"Error in generating response from llm {e} ")