import requests
import os

GROQ_KEY = "your_key_here"

def search(question, knowledge):
    stopwords = {'what', 'is', 'are', 'the', 'a', 'an',
                 'do', 'you', 'we', 'i', 'how', 'can',
                 'does', 'tell', 'me'}
    question_words = set(question.lower().split()) - stopwords
    best_score = -1
    best_chunk = knowledge[0]
    for chunk in knowledge:
        chunk_words = set(chunk.lower().split())
        score = len(question_words & chunk_words)
        if score > best_score:
            best_score = score
            best_chunk = chunk
    return best_chunk

def ask_ai(question, context, history):
    # Build messages with full history
    messages = [
        {
            "role": "system",
            "content": f"""You are a helpful assistant.
Use ONLY this info to answer:
{context}
If you don't know, say 'I don't have that information.'"""
        }
    ]
    # Add all previous conversation
    for chat in history:
        messages.append(chat)
    # Add current question
    messages.append({"role": "user", "content": question})

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": messages
        }
    )
    result = response.json()
    if "choices" not in result:
        return f"Error: {result}"
    return result["choices"][0]["message"]["content"]

# Simple knowledge for testing
knowledge = [
    "Basic package costs 999 rupees per month.",
    "Standard package costs 1999 rupees per month.",
    "Premium package costs 3999 rupees per month.",
    "All packages include free home delivery.",
    "We offer 30 day free trial for all packages.",
    "Consultation fee is 500 rupees.",
    "We are open from 9 AM to 6 PM.",
    "We accept cash and UPI payments.",
]

# Empty history at start
history = []

print("Chat Assistant Ready! (remembers conversation)")
print("Type 'quit' to exit\n")

while True:
    question = input("You: ").strip()
    if question.lower() == "quit":
        print("Bye!")
        break
    if not question:
        continue

    context = search(question, knowledge)
    answer = ask_ai(question, context, history)

    # Save to history
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})

    print(f"Bot: {answer}\n")
    print(f"(History: {len(history)//2} messages)\n")
