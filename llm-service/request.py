import json
import time
import random
import requests

URL = "http://localhost:8000/llm/extract/profiles"

prompts = [
    "Name: Priya Sharma\nWorking at: Infosys\nEducation: B.Tech\nEmail: priya@infosys.com\nPhone: +91 98765 43210\nAddress: Bengaluru",
    "I'm Arjun Mehta, a Data Analyst at Flipkart.",
    "Best,\nAnita Iyer | Product Manager\nAcme Corp\nanita@acme.com | +44 20 7946 0958\n221B Baker Street, London",
    "<div><h1>Rahul N.</h1><p>Software Engineer at Zoho</p><p>Email: rahul@zoho.com</p></div>",
    "Name: Neha Gupta\nWorking at: Salesforce\nPhone: +1 415-555-1200",
    "Rohan Verma, Adobe, rohan@adobe.com, +1 650-555-7788, San Jose",
    "Name: Chen Li\nEducation: M.Sc. CS, Tsinghua",
    "Email: maria.garcia@bbva.com\nWorking at: BBVA",
    "Phone: +33 1 42 68 53 00\nAddress: Paris",
    "Name: John Doe\nAddress: 123 Main St, NYC",
    "Working at: Google\nEmail: jd@google.com",
    "Education: BSc Physics, MIT",
    "Name: Satya\nWorking at: Unknown",
    "Name: A. Kumar | Infosys | a.kumar@infy.com",
    "Contact: +1-212-555-0100",
    "Signature:\nSuresh K\nVP, TCS\nsuresh.k@tcs.com",
    "Profile: Elena Petrova, Yandex, Moscow",
    "Card:\nName: Omar\nEmail: omar@company.com",
    "Jane Roe\nSoftware Engineer\nAcme Ltd\njane.roe@acme.co",
    "Name: Karan\nPhone: +91-90000-11111\nAddress: Pune"
]

for i, text in enumerate(prompts, 1):
    payload = {"text": text, "retries": 2}
    try:
        r = requests.post(URL, json=payload, timeout=60)
        print(f"[{i:02d}] status={r.status_code} resp={r.text[:200]}")
    except Exception as e:
        print(f"[{i:02d}] error={e}")
    time.sleep(random.uniform(0.1, 0.3))