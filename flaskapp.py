import io
import re
import os
import math
import random
import requests
from flask import Flask, request, jsonify
import PyPDF2

app = Flask(__name__)

# ✅ Keys come from Render environment variables — never hardcoded
API_KEYS = [
    os.environ.get("GROQ_KEY_1", ""),
    os.environ.get("GROQ_KEY_2", ""),
    os.environ.get("GROQ_KEY_3", ""),
]
# Remove empty keys in case some are not set
API_KEYS = [k for k in API_KEYS if k]

# Storage for all PDF chunks and chat history
all_pdf_chunks = {}
history = []

# ========================
# HELPER FUNCTIONS
# ========================

def clean(text):
    # Removes extra spaces and weird whitespace
    return re.sub(r'\s+', ' ', text).strip()

def split_into_chunks(text, chunk_size=300):
    # Cuts long text into 300-word pieces
    # Like cutting a long rope into equal smaller pieces
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def find_best_chunk(question, all_chunks_dict):
    # TF-IDF Search — smarter than simple word matching
    # Rare important words score higher than common words

    stopwords = {
        'the','a','an','is','it','in','on','at','to','for','of','and','or',
        'what','how','when','where','who','which','does','do','are','was',
        'were','will','can','could','should','would','have','has','had',
        'be','been','being','me','my','your','i','tell','about','please'
    }

    # Get only the important words from the question
    question_words = set(question.lower().split()) - stopwords

    # Collect ALL chunks from ALL PDFs into one flat list
    # Needed so IDF knows total number of chunks
    all_chunks_flat = []
    for chunks in all_chunks_dict.values():
        all_chunks_flat.extend(chunks)

    total_chunks = len(all_chunks_flat)

    if total_chunks == 0:
        return "", ""

    best_chunk = ""
    best_score = 0
    best_pdf = ""

    # Go through every chunk in every PDF
    for pdf_name, chunks in all_chunks_dict.items():
        for chunk in chunks:

            chunk_words = chunk.lower().split()
            score = 0

            for word in question_words:

                # TF = how often this word appears in THIS chunk
                # Example: "biryani" appears 3 times in 300 words = 0.01
                tf = chunk_words.count(word) / len(chunk_words) if chunk_words else 0

                # IDF = how RARE this word is across ALL chunks
                # Rare words get higher score, common words get lower score
                chunks_with_word = sum(
                    1 for c in all_chunks_flat if word in c.lower().split()
                )
                idf = math.log(total_chunks / (chunks_with_word + 1)) + 1

                # Final TF-IDF score for this word
                score += tf * idf

            if score > best_score:
                best_score = score
                best_chunk = chunk
                best_pdf = pdf_name

    return best_chunk, best_pdf

def ask_groq(api_key, messages):
    # Sends conversation to Groq and returns the reply
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7
    }
    result = requests.post(url, headers=headers, json=payload, timeout=15).json()
    return result["choices"][0]["message"]["content"]

# ========================
# ROUTES
# ========================

@app.route('/')
def home():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DocMind AI</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:#07080f;--surface:#0d0f1a;--surface2:#111320;--border:rgba(255,255,255,0.06);--border2:rgba(255,255,255,0.1);--accent:#7c5cfc;--accent2:#5eead4;--accent3:#f472b6;--text:#f1f5f9;--muted:#64748b;}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{height:100%;overflow:hidden;}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);display:flex;flex-direction:column;height:100vh;position:relative;overflow:hidden;}
.bg-orb{position:fixed;border-radius:50%;filter:blur(80px);opacity:0.12;pointer-events:none;z-index:0;animation:drift 8s ease-in-out infinite;}
.o1{width:400px;height:400px;background:#7c5cfc;top:-100px;left:-100px;}
.o2{width:300px;height:300px;background:#5eead4;bottom:-80px;right:-80px;animation-delay:-3s;}
.o3{width:200px;height:200px;background:#f472b6;top:50%;left:50%;animation-delay:-5s;}
@keyframes drift{0%,100%{transform:translate(0,0) scale(1);}33%{transform:translate(20px,-20px) scale(1.05);}66%{transform:translate(-15px,15px) scale(0.95);}}
.layout{position:relative;z-index:1;display:flex;flex-direction:column;height:100vh;max-width:520px;margin:0 auto;width:100%;}
header{padding:18px 20px 14px;background:rgba(7,8,15,0.85);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);flex-shrink:0;}
.header-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.brand{display:flex;align-items:center;gap:10px;}
.brand-icon{width:38px;height:38px;background:linear-gradient(135deg,#7c5cfc,#5eead4);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;box-shadow:0 0 20px rgba(124,92,252,0.4);}
.brand-name{font-size:16px;font-weight:700;letter-spacing:-0.5px;}
.brand-name span{color:var(--accent);}
.status-pill{display:flex;align-items:center;gap:5px;padding:4px 10px;background:rgba(94,234,212,0.08);border:1px solid rgba(94,234,212,0.2);border-radius:20px;font-size:11px;color:var(--accent2);font-family:'JetBrains Mono',monospace;}
.status-dot{width:6px;height:6px;background:var(--accent2);border-radius:50%;animation:pulse-dot 2s infinite;}
@keyframes pulse-dot{0%,100%{opacity:1;}50%{opacity:0.3;}}
.upload-zone{border:1.5px dashed rgba(124,92,252,0.3);border-radius:14px;padding:12px 16px;cursor:pointer;transition:all 0.3s;background:rgba(124,92,252,0.04);display:flex;align-items:center;gap:12px;position:relative;overflow:hidden;}
.upload-zone::before{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(124,92,252,0.08),transparent);opacity:0;transition:opacity 0.3s;}
.upload-zone:hover::before{opacity:1;}
.upload-zone:hover{border-color:rgba(124,92,252,0.6);transform:translateY(-1px);box-shadow:0 8px 24px rgba(124,92,252,0.15);}
.upload-icon{width:36px;height:36px;background:rgba(124,92,252,0.15);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0;}
.upload-text{flex:1;}
.upload-text strong{display:block;font-size:13px;font-weight:600;}
.upload-text span{font-size:11px;color:var(--muted);}
.upload-btn-sm{background:var(--accent);color:#fff;border:none;padding:7px 14px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;flex-shrink:0;transition:all 0.2s;}
.upload-btn-sm:hover{background:#6b4de8;}
.pdf-chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px;}
.chip{display:flex;align-items:center;gap:4px;padding:3px 10px;background:rgba(124,92,252,0.12);border:1px solid rgba(124,92,252,0.25);border-radius:20px;font-size:11px;color:#a78bfa;animation:chip-in 0.3s ease;}
@keyframes chip-in{from{opacity:0;transform:scale(0.8);}to{opacity:1;transform:scale(1);}}
.chat{flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:14px;scrollbar-width:thin;scrollbar-color:rgba(124,92,252,0.2) transparent;}
.chat::-webkit-scrollbar{width:4px;}
.chat::-webkit-scrollbar-thumb{background:rgba(124,92,252,0.3);border-radius:4px;}
.msg{display:flex;flex-direction:column;max-width:84%;animation:msg-in 0.35s cubic-bezier(0.34,1.56,0.64,1);}
@keyframes msg-in{from{opacity:0;transform:translateY(10px) scale(0.96);}to{opacity:1;transform:translateY(0) scale(1);}}
.msg.user{align-self:flex-end;align-items:flex-end;}
.msg.ai{align-self:flex-start;align-items:flex-start;}
.msg-header{display:flex;align-items:center;gap:6px;margin-bottom:5px;}
.avatar{width:22px;height:22px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;}
.ai-av{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;}
.user-av{background:rgba(124,92,252,0.2);color:var(--accent);}
.sender-name{font-size:11px;font-weight:600;color:var(--muted);letter-spacing:0.3px;}
.bubble{padding:12px 16px;border-radius:16px;font-size:14px;line-height:1.65;position:relative;}
.msg.user .bubble{background:linear-gradient(135deg,#7c5cfc,#5b3fd4);color:#fff;border-bottom-right-radius:4px;box-shadow:0 4px 16px rgba(124,92,252,0.3);}
.msg.ai .bubble{background:var(--surface2);border:1px solid var(--border2);border-bottom-left-radius:4px;box-shadow:0 4px 16px rgba(0,0,0,0.3);}
.source-tag{display:inline-flex;align-items:center;gap:4px;margin-top:6px;padding:3px 8px;background:rgba(94,234,212,0.08);border:1px solid rgba(94,234,212,0.15);border-radius:10px;font-size:10px;color:var(--accent2);font-family:'JetBrains Mono',monospace;}
.typing-msg{display:none;padding:0 20px;}
.typing-header{display:flex;align-items:center;gap:6px;margin-bottom:5px;}
.typing-bubble{padding:14px 18px;background:var(--surface2);border:1px solid var(--border2);border-radius:16px;border-bottom-left-radius:4px;display:inline-flex;align-items:center;gap:5px;}
.dot{width:7px;height:7px;background:var(--accent);border-radius:50%;animation:bounce 1.2s infinite;}
.dot:nth-child(2){animation-delay:0.15s;background:var(--accent2);}
.dot:nth-child(3){animation-delay:0.3s;background:var(--accent3);}
@keyframes bounce{0%,60%,100%{transform:translateY(0);opacity:0.4;}30%{transform:translateY(-6px);opacity:1;}}
.suggestions{padding:0 20px 10px;display:flex;flex-wrap:wrap;gap:6px;flex-shrink:0;}
.sug{padding:7px 14px;background:rgba(124,92,252,0.06);border:1px solid rgba(124,92,252,0.2);border-radius:20px;font-size:12px;color:#a78bfa;cursor:pointer;font-family:'Inter',sans-serif;transition:all 0.2s;}
.sug:hover{background:rgba(124,92,252,0.15);border-color:rgba(124,92,252,0.5);color:#fff;transform:translateY(-1px);}
.input-wrap{padding:10px 20px 18px;background:rgba(7,8,15,0.9);backdrop-filter:blur(20px);border-top:1px solid var(--border);flex-shrink:0;}
.input-box{display:flex;align-items:center;gap:8px;background:var(--surface2);border:1.5px solid var(--border2);border-radius:16px;padding:6px 6px 6px 16px;transition:border-color 0.2s,box-shadow 0.2s;}
.input-box:focus-within{border-color:rgba(124,92,252,0.5);box-shadow:0 0 0 3px rgba(124,92,252,0.08);}
#msg{flex:1;background:none;border:none;outline:none;color:var(--text);font-family:'Inter',sans-serif;font-size:14px;padding:6px 0;}
#msg::placeholder{color:var(--muted);}
#send-btn{width:38px;height:38px;background:linear-gradient(135deg,#7c5cfc,#5b3fd4);border:none;border-radius:11px;color:#fff;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;flex-shrink:0;box-shadow:0 4px 12px rgba(124,92,252,0.4);}
#send-btn:hover{transform:scale(1.05);}
#send-btn:disabled{opacity:0.4;cursor:not-allowed;transform:none;}
.powered-by{text-align:center;font-size:10px;color:var(--muted);margin-top:8px;font-family:'JetBrains Mono',monospace;}
.powered-by span{color:var(--accent);}
</style>
</head>
<body>
<div class="bg-orb o1"></div>
<div class="bg-orb o2"></div>
<div class="bg-orb o3"></div>
<div class="layout">
  <header>
    <div class="header-top">
      <div class="brand">
        <div class="brand-icon">🧠</div>
        <div>
          <div class="brand-name">Doc<span>Mind</span> AI</div>
          <div style="font-size:10px;color:var(--muted);font-family:'JetBrains Mono',monospace;">by Piyush Sambhwani</div>
        </div>
      </div>
      <div class="status-pill"><div class="status-dot"></div>RAG LIVE</div>
    </div>
    <input type="file" id="pdffile" accept=".pdf" multiple style="display:none">
    <div class="upload-zone" onclick="document.getElementById('pdffile').click()">
      <div class="upload-icon">📂</div>
      <div class="upload-text">
        <strong>Upload your documents</strong>
        <span>PDF files · Multiple allowed · Instant processing</span>
      </div>
      <button class="upload-btn-sm" onclick="event.stopPropagation();document.getElementById('pdffile').click()">Browse</button>
    </div>
    <div class="pdf-chips" id="pdf-chips"></div>
  </header>
  <div class="chat" id="chat">
    <div class="msg ai">
      <div class="msg-header"><div class="avatar ai-av">AI</div><span class="sender-name">DocMind AI</span></div>
      <div class="bubble">👋 Hello! Upload your business documents and I will answer any question from them instantly.</div>
    </div>
  </div>
  <div class="typing-msg" id="typing">
    <div class="typing-header"><div class="avatar ai-av">AI</div><span class="sender-name">DocMind AI</span></div>
    <div class="typing-bubble"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
  </div>
  <div class="suggestions" id="sugs">
    <button class="sug" onclick="ask(this)">💰 Consultation fee?</button>
    <button class="sug" onclick="ask(this)">🕐 Opening hours?</button>
    <button class="sug" onclick="ask(this)">⭐ Premium package?</button>
    <button class="sug" onclick="ask(this)">💳 How to pay?</button>
  </div>
  <div class="input-wrap">
    <div class="input-box">
      <input type="text" id="msg" placeholder="Ask anything about your documents..." onkeypress="if(event.key==='Enter')send()">
      <button id="send-btn" onclick="send()">&#10148;</button>
    </div>
    <div class="powered-by">Powered by <span>RAG</span> · Built by <span>Piyush Sambhwani</span></div>
  </div>
</div>
<script>
document.getElementById('pdffile').onchange=function(){
  var files=this.files;
  if(!files.length)return;
  var chips=document.getElementById('pdf-chips');
  chips.innerHTML='';
  for(var i=0;i<files.length;i++){chips.innerHTML+='<div class="chip">&#128196; '+files[i].name+'</div>';}
  var fd=new FormData();
  for(var i=0;i<files.length;i++)fd.append('pdfs',files[i]);
  fetch('/upload',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{addMessage('ai','&#9989; '+d.message,null);});
};
function ask(btn){document.getElementById('msg').value=btn.textContent.slice(3);send();}
function send(){
  var msg=document.getElementById('msg').value.trim();
  if(!msg)return;
  document.getElementById('sugs').style.display='none';
  addMessage('user',msg,null);
  document.getElementById('msg').value='';
  document.getElementById('typing').style.display='block';
  document.getElementById('send-btn').disabled=true;
  document.getElementById('chat').scrollTop=document.getElementById('chat').scrollHeight;
  fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})}).then(r=>r.json()).then(d=>{
    document.getElementById('typing').style.display='none';
    addMessage('ai',d.reply,d.source);
    document.getElementById('send-btn').disabled=false;
  });
}
function addMessage(role,text,source){
  var chat=document.getElementById('chat');
  var div=document.createElement('div');
  div.className='msg '+role;
  var av=role==='ai'?'<div class="avatar ai-av">AI</div>':'<div class="avatar user-av">Y</div>';
  var name=role==='ai'?'DocMind AI':'You';
  var src=source&&role==='ai'?'<div class="source-tag">&#128196; '+source+'</div>':'';
  div.innerHTML='<div class="msg-header">'+av+'<span class="sender-name">'+name+'</span></div><div class="bubble">'+text+'</div>'+src;
  chat.appendChild(div);
  chat.scrollTop=chat.scrollHeight;
}
</script>
</body>
</html>"""

@app.route('/upload', methods=['POST'])
def upload():
    global all_pdf_chunks
    try:
        files = request.files.getlist('pdfs')
        if not files:
            return jsonify({"message": "No files uploaded!", "files": []})
        uploaded_names = []
        for file in files:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            full_text = ""
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text
            full_text = clean(full_text)
            all_pdf_chunks[file.filename] = split_into_chunks(full_text, 300)
            uploaded_names.append(file.filename)
        total_chunks = sum(len(v) for v in all_pdf_chunks.values())
        return jsonify({
            "message": f"{len(uploaded_names)} PDF(s) loaded — {total_chunks} chunks ready!",
            "files": uploaded_names
        })
    except Exception as e:
        return jsonify({"message": f"Error reading PDF: {str(e)}", "files": []})

@app.route('/chat', methods=['POST'])
def chat():
    global all_pdf_chunks, history
    try:
        data = request.json
        msg = data.get('message', '')

        if not all_pdf_chunks:
            return jsonify({"reply": "Please upload a PDF first!", "source": ""})

        # Find the best matching chunk using TF-IDF
        best_chunk, source_pdf = find_best_chunk(msg, all_pdf_chunks)

        # System prompt — tells Groq to only answer from PDF content
        system = f"""You are a helpful AI assistant built by Piyush Sambhwani.
Answer questions based ONLY on this content:

{best_chunk}

Rules:
- Be helpful and precise
- Plain text only, no ** or markdown symbols
- If answer is not in the content, say: I don't have that information in the uploaded documents."""

        # Build messages list — system + full history + new question
        messages = [{"role": "system", "content": system}]
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": msg})

        # Add user message to history
        history.append({"role": "user", "content": msg})

        # Try each API key randomly until one works
        keys = API_KEYS.copy()
        random.shuffle(keys)

        for key in keys:
            try:
                reply = ask_groq(key, messages)
                reply = clean(reply)

                # Add AI reply to history
                history.append({"role": "assistant", "content": reply})

                # Keep only last 10 messages to avoid overload
                if len(history) > 10:
                    history = history[-10:]

                return jsonify({"reply": reply, "source": source_pdf})

            except Exception:
                continue

        return jsonify({"reply": "All API keys failed. Please try again!", "source": ""})

    except Exception as e:
        return jsonify({"reply": f"Something went wrong: {str(e)}", "source": ""})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
