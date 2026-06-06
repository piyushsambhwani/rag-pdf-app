import requests

# ============================
# YOUR GROQ API KEY
# ============================
API_KEY = os.environ.get("API_KEY", "your_key_here")

# ============================
# YOUR SHOP KNOWLEDGE
# Add or remove lines as you want!
# ============================
knowledge = [
    "We are open from 9 AM to 9 PM, Monday to Saturday.",
    "We are closed on Sundays and national holidays.",
    "We deliver within 5 km radius. Minimum order is 200 rupees.",
    "Home delivery takes 30 to 45 minutes.",
    "We sell groceries, snacks, cold drinks, and household items.",
    "We accept GPay, PhonePe, and Paytm. No cash accepted.",
    "Full refund within 7 days with bill. No refund after 7 days.",
    "Bulk orders above 2000 rupees get 5 percent discount.",
    "Call us at 98765-43210 for orders or questions.",
]

# ============================
# STEP 1 — FIND BEST ANSWER
# ============================
def search(question):
    # These words are useless for searching
    stopwords = {'what', 'is', 'are', 'the', 'a', 'an',
                 'do', 'you', 'we', 'i', 'how', 'can', 'does', 'tell', 'me'}

    # Get meaningful words from question only
    question_words = set(question.lower().split()) - stopwords

    best_score = -1
    best_chunk = knowledge[0]  # Default to first chunk

    for chunk in knowledge:
        chunk_words = set(chunk.lower().split())

        # Count how many question words appear in this chunk
        score = len(question_words & chunk_words)

        if score > best_score:
            best_score = score
            best_chunk = chunk

    return best_chunk

# ============================
# STEP 2 — ASK GROQ AI
# ============================
def ask_ai(question, context):
    prompt = f"""You are a helpful shop assistant.
Use ONLY this info to answer:
{context}

Customer question: {question}
Give a short and friendly answer."""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    return response.json()["choices"][0]["message"]["content"]

# ============================
# MAIN — START CHATTING!
# ============================
print("🛒 Shop Assistant Ready!")
print("Type 'quit' to exit\n")

while True:
    question = input("You: ").strip()

    if question.lower() == "quit":
        print("Bye!")
        break

    if not question:
        continue

    context = search(question)
    answer = ask_ai(question, context)

    print(f"Bot: {answer}\n")
