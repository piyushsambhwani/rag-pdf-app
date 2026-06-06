import requests
import numpy as np

GEMINI_KEY = "AIzaSyDzvSsKHjY11yTNzOhwgD569WQHQ6HAb3s"

def get_embedding(text):
    url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key=" + GEMINI_KEY
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={
            "model": "models/text-embedding-004",
            "content": {
                "parts": [{"text": text}]
            }
        }
    )
    result = response.json()
    if "embedding" not in result:
        print("Error:", result)
        return None
    return result["embedding"]["values"]

sentences = [
    "consultation fee is 500 rupees",
    "we are open from 9 AM to 6 PM",
    "we accept cash and UPI payments",
]

question = "what are the charges?"

print("Testing embeddings...")
q_vec = np.array(get_embedding(question))
best_score = -1
best_match = ""

for s in sentences:
    vec = np.array(get_embedding(s))
    score = np.dot(q_vec, vec)
    if score > best_score:
        best_score = score
        best_match = s

print("Question: " + question)
print("Best match: " + best_match)
