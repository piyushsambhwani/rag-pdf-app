import requests
import PyPDF2
import os

app = Flask(__name__)

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
    if not os.path.exists(folder):
        return all_knowledge
    pdf_files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
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
    print(f"Loaded {len(pdf_files)} PDFs, {len(all_knowledge)} chunks")
    return all_knowledge

def search(question, knowledge):
    if not knowledge:
        return "No knowledge available"
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
    messages = [
        {
            "role": "system",
            "content": f"""You are a helpful assistant.
Use ONLY this info to answer:
{context}
If you don't know, say 'I don't have that information.'"""
        }
    ]
    for chat in history[-10:]:
        messages.append(chat)
    messages.append({"role": "user", "content": question})
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {get_next_key()}",
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

knowledge = load_all_pdfs("documents")

# Store history per session
sessions = {}

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "")
    session_id = data.get("session_id", "default")
    if not question:
        return jsonify({"error": "No question provided"}), 400
    if session_id not in sessions:
        sessions[session_id] = []
    history = sessions[session_id]
    context = search(question, knowledge)
    answer = ask_ai(question, context, history)
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    return jsonify({"answer": answer})

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
