import requests
import PyPDF2

API_KEY = os.environ.get("API_KEY", "your_key_here")

def load_pdf(filename):
    knowledge = []
    with open(filename, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                for line in lines:
                    clean = line.strip()
                    if clean:
                        knowledge.append(clean)
    return knowledge

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

def ask_ai(question, context):
    prompt = f"""You are a helpful assistant.
Use ONLY this info to answer:
{context}
Question: {question}
Give a short and clear answer."""
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

knowledge = load_pdf("document.pdf")
print(f"✅ Loaded {len(knowledge)} lines from PDF!")
print("📄 PDF Assistant Ready!")
print("Type 'quit' to exit\n")

while True:
    question = input("You: ").strip()
    if question.lower() == "quit":
        print("Bye!")
        break
    if not question:
        continue
    context = search(question, knowledge)
    answer = ask_ai(question, context)
    print(f"Bot: {answer}\n")
