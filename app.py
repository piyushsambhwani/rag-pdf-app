import os
import io
import re
import random
import requests
from flask import Flask, request, jsonify
import PyPDF2

app = Flask(__name__)

# Your Gemini API keys — keep all your existing keys here
API_KEYS = [
    "YOUR_KEY_1",
    "YOUR_KEY_2",
    "YOUR_KEY_3",
]

# Store PDF chunks globally
pdf_chunks = []

# ── Clean text ──
def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

# ── CHUNKING: Cut big text into small pieces of 300 words ──
# Like cutting a big pizza into small slices
def split_into_chunks(text, chunk_size=300):
    words = text.split()       # Split text into individual words
    chunks = []                # Empty bag to collect pieces

    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])   # Join 300 words back together
        chunks.append(chunk)   # Add piece to bag

    return chunks              # Return all pieces

# ── RETRIEVAL: Find which chunk best matches the question ──
# Like treasure hunt — which box has the most matching words?
def find_best_chunk(question, chunks):
    stopwords = {
        'the','a','an','is','it','in','on','at','to','for','of','and','or',
        'what','how','when','where','who','which','does','do','are','was',
        'were','will','can','could','should','would','have','has','had',
        'be','been','being','me','my','your','i','tell','about','please'
    }

    # Get meaningful words from question (remove stopwords)
    question_words = set(question.lower().split()) - stopwords

    best_chunk = chunks[0]   # Default winner = first chunk
    best_score = 0           # Starting score = 0

    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        score = len(question_words & chunk_words)  # Count matching words
        if score > best_score:
            best_score = score
            best_chunk = chunk  # New winner!

    return best_chunk

@app.route('/')
def home():
    return '''<!DOCTYPE html><html><head><title>PDF AI Assistant</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:arial;height:100vh;display:flex;flex-direction:column;}
h1{color:#00d4aa;text-align:center;padding:20px;font-size:20px;background:#0f0f1a;border-bottom:2px solid #00d4aa;}
.upload-area{background:#0f0f1a;padding:15px;border-bottom:1px solid #333;}
.upload-btn{background:#00d4aa;color:#000;padding:10px 15px;border:none;border-radius:10px;cursor:pointer;font-weight:bold;}
#status{color:#00d4aa;margin-top:5px;font-size:13px;}
.chat{flex:1;overflow-y:auto;padding:15px;background:#0a0a14;}
.msg{margin:8px 0;display:flex;flex-direction:column;}
.msg.user .name{text-align:right;}
.msg.user .bubble{background:#00d4aa;color:#000;align-self:flex-end;}
.msg.ai .bubble{background:#1a1a2e;color:#fff;align-self:flex-start;border:1px solid #00d4aa;}
.bubble{padding:10px 14px;border-radius:18px;max-width:80%;font-size:14px;}
.input-area{background:#0f0f1a;padding:10px;display:flex;gap:8px;}
input[type=text]{flex:1;background:#1a1a2e;border:1px solid #333;color:#fff;padding:10px;border-radius:25px;font-size:14px;outline:none;}
button#btn{background:#00d4aa;color:#000;border:none;padding:10px 20px;border-radius:25px;font-weight:bold;cursor:pointer;}
button:disabled{opacity:0.5;}
.typing{display:none;color:#00d4aa;padding:5px 15px;font-size:13px;}
</style></head>
<body>
<h1>📄 PDF AI Assistant<br><small style="font-size:13px;">Built by Piyush Sambhwani | Powered by RAG</small></h1>
<div class="upload-area">
<input type="file" id="pdffile" accept=".pdf" style="display:none">
<button class="upload-btn" onclick="document.getElementById(\'pdffile\').click()">📎 Upload PDF</button>
<span id="status">No PDF uploaded</span>
</div>
<div class="chat" id="chat">
<div class="msg ai"><div class="bubble">👋 Hello! Upload a PDF and ask me anything about it!</div></div>
</div>
<div class="typing" id="typing">AI is thinking...</div>
<div class="input-area">
<input type="text" id="msg" placeholder="Upload PDF first then ask questions..." onkeypress="if(event.key===\'Enter\')send()">
<button id="btn" onclick="send()">Send</button>
</div>
<script>
var sid=Math.random().toString(36).substring(2);
document.getElementById("pdffile").onchange=function(){
var file=this.files[0];
if(!file){return;}
document.getElementById("status").textContent="Uploading...";
var fd=new FormData();
fd.append("pdf",file);
fetch("/upload",{method:"POST",body:fd}).then(r=>r.json()).then(d=>{
document.getElementById("status").textContent=d.message;
});
};
function send(){
var msg=document.getElementById("msg").value.trim();
if(!msg)return;
var chat=document.getElementById("chat");
var typing=document.getElementById("typing");
var btn=document.getElementById("btn");
var d=document.createElement("div");
d.innerHTML=\'<div class="msg user"><div class="name">You</div><div class="bubble">\'+msg+\'</div></div>\';
chat.appendChild(d);
document.getElementById("msg").value="";
typing.style.display="block";
btn.disabled=true;
chat.scrollTop=chat.scrollHeight;
fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg,session_id:sid})}).then(r=>r.json()).then(data=>{
typing.style.display="none";
var e=document.createElement("div");
e.innerHTML=\'<div class="msg ai"><div class="name">AI</div><div class="bubble">\'+data.reply+\'</div></div>\';
chat.appendChild(e);
chat.scrollTop=chat.scrollHeight;
btn.disabled=false;
});
}
</script>
</body></html>'''

# ── Upload PDF and create chunks ──
@app.route('/upload', methods=['POST'])
def upload():
    global pdf_chunks
    try:
        file = request.files['pdf']
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))

        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text()

        full_text = clean(full_text)

        # ✅ Split into chunks — not store raw text
        pdf_chunks = split_into_chunks(full_text, chunk_size=300)

        return jsonify({
            "message": f"✅ {len(pdf_reader.pages)} pages uploaded → {len(pdf_chunks)} chunks created!"
        })
    except Exception as e:
        return jsonify({"message": "❌ Error reading PDF!"})

# ── Chat using best matching chunk ──
@app.route('/chat', methods=['POST'])
def chat():
    global pdf_chunks
    try:
        data = request.json
        msg = data.get('message', '')

        if not pdf_chunks:
            return jsonify({"reply": "Please upload a PDF first!"})

        # ✅ Find best chunk — not pdf_text[:3000]
        best_chunk = find_best_chunk(msg, pdf_chunks)

        system = f"""You are a helpful AI assistant built by Piyush Sambhwani.
Answer questions based on this PDF content only:

{best_chunk}

Be helpful and precise. Plain text only, no ** symbols."""

        # Rotate Gemini API keys
        keys = API_KEYS.copy()
        random.shuffle(keys)

        for key in keys:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": system + "\n\nQuestion: " + msg}]}]}
            result = requests.post(url, json=payload, timeout=15).json()

            if "candidates" in result:
                reply = clean(result["candidates"][0]["content"]["parts"][0]["text"])
                return jsonify({"reply": reply})

        return jsonify({"reply": "Please try again!"})

    except Exception as e:
        return jsonify({"reply": "Something went wrong!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
