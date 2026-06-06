import requests
import PyPDF2
import os

GROQ_KEYS = [
    os.environ.get("GROQ_KEY_1", "your_key_here"),
    os.environ.get("GROQ_KEY_2", "your_key_here"),
    os.environ.get("GROQ_KEY_3", "your_key_here"),
    os.environ.get("GROQ_KEY_4", "your_key_here"),
]

current_key = 0

def get_next_key():
    global current_key
    key = GROQ_KEYS[current_key]
    current_key = (current_key + 1) % len(GROQ_KEYS)
    return key

def load_all_pdfs(folder):
    all_knowledge = []
    pdf_files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDFs: {pdf_files}")
    for pdf_file in pdf_files:
        path = os.path.join(folder, pdf_file)
        with open(path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    lines = text.split("\n")
                    for line in lines:
                        clean = line.strip()
                        if clean:
                            all_knowledge.append(clean)
        print(f"Loaded: {pdf_file}")
    return all_knowledge

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
            "Authorization": f"Bearer {get_next_key()}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    result = response.json()
    if "choices" not in result:
        return f"Error: {result}"
    return result["choices"][0]["message"]["content"]

knowledge = load_all_pdfs("documents")
print(f"\nTotal chunks loaded: {len(knowledge)}")
print("Multi-doc Assistant Ready!")
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
