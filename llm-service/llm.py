import ollama
import json

model="phi3:mini"

system_prompt="""
You are a strict information extraction engine.
Extract factual information present in the input text.
Rules:
- Don't infer about missing data
- if field is missing give null
- Dont add explanaiton and comments. Give only structured JSON response.
Output format: (JSON only)
"""

def extractor(text:str, retries: int = 2) -> str:
    prompt = text

    for attempt in range(retries + 1):
        response=ollama.chat(
            model=model,
            messages=[
                {"role":"system", "content": system_prompt},
                {"role":"user", "content" : prompt}
            ],
            format="json"
        )

        raw = response["message"]["content"].strip()

        try:
            data=json.loads(raw)
            return data
        except Exception as e:
            last_error = e
            prompt += "\nReturn only JSON. nothing else. Not even a single word"
            continue
    
    return RuntimeError(f"Failed after retries: {last_error}")
    