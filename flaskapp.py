import io
import re
import random
import requests
from flask import Flask, request, jsonify
import PyPDF2

app = Flask(__name__)

# Your Gemini API keys
API_KEYS = [
    "YOUR_KEY_1",
    "YOUR_KEY_2",
    "YOUR_KEY_3",
]

# DAY 6 UPGRADE — dictionary instead of list
# Like labelled drawers — each drawer = one PDF
all_pdf_chunks = {}

def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

# Same chunking function from Day 5
def split_into_chunks(text, chunk_size=300):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# UPGRADED — now searches across ALL PDFs
def find_best_chunk(question, all_chunks_dict):
    stopwords = {
        'the','a','an','is','it','in','on','at','to','for','of','and','or',
        'what','how','when','where','who','which','does','do','are','was',
        'were','will','can','could','should','would','have','has','had',
        'be','been','being','me','my','your','i','tell','about','please'
    }

    question_words = set(question.lower().split()) - stopwords

    best_chunk = ""
    best_score = 0
    best_pdf = ""

    # Loop through EVERY PDF
    for pdf_name, chunks in all_chunks_dict.items():
        # Loop through every chunk in this PDF
        for chunk in chunks:
            chunk_words = set(chunk.lower().split())
            score = len(question_words & chunk_words)
            if score > best_score:
                best_score = score
                best_chunk = chunk
                best_pdf = pdf_name  # Remember WHICH PDF had the answer

    return best_chunk, best_pdf

@app.route('/')
def home():
    return '''<!DOCTYPE html><html><head><title>Business AI Assistant</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:arial;height:100vh;display:flex;flex-direction:column;background:#0a0a14;color:#fff;}
h1{color:#00d4aa;text-align:center;padding:15px;font-size:18px;background:#0f0f1a;border-bottom:2px solid #00d4aa;}
.upload-area{background:#0f0f1a;padding:12px 15px;border-bottom:1px solid #333;}
.upload-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
.upload-btn{background:#00d4aa;color:#000;padding:8px 14px;border:none;border-radius:8px;cursor:pointer;font-weight:bold;font-size:13px;}
#pdf-list{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;}
.pdf-tag{background:#1a1a2e;border:1px solid #00d4aa;color:#00d4aa;padding:3px 10px;border-radius:12px;font-size:12px;}
#status{color:#00d4aa;font-size:12px;margin-top:5px;}
.chat{flex:1;overflow-y:auto;padding:15px;display:flex;flex-direction:column;gap:12px;}
.msg{display:flex;flex-direction:column;max-width:80%;}
.msg.user{align-self:flex-end;align-items:flex-end;}
.msg.ai{align-self:flex-start;}
.bubble{padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.5;}
.msg.user .bubble{background:#00d4aa;color:#000;border-bottom-right-radius:4px;}
.msg.ai .bubble{background:#1a1a2e;border:1px solid #333;border-bottom-left-radius:4px;}
.source{font-size:11px;color:#555;margin-top:3px;}
.typing{display:none;color:#00d4aa;padding:5px 15px;font-size:13px;}
.input-area{background:#0f0f1a;padding:10px;display:flex;gap:8px;border-top:1px solid #333;}
input[type=text]{flex:1;background:#1a1a2e;border:1px solid #333;color:#fff;padding:10px;border-radius:25px;font-size:14px;outline:none;}
#btn{background:#00d4aa;color:#000;border:none;padding:10px 20px;border-radius:25px;font-weight:bold;cursor:pointer;}
#btn:disabled{opacity:0.4;}
</style></head>
<body>
<h1>🤖 Business AI Assistant<br><small style="font-size:12px;">Built by Piyush Sambhwani | Powered by RAG</small></h1>
<div class="upload-area">
  <div class="upload-row">
    <input type="file" id="pdffile" accept=".pdf" multiple style="display:none">
    <button class="upload-btn" onclick="document.getElementById(\'pdffile\').click()">📎 Upload PDFs</button>
    <span id="status">No PDFs uploaded yet</span>
  </div>
  <div id="pdf-list"></div>
</div>
<div class="chat" id="chat">
  <div class="msg ai"><div class="bubble">👋 Hello! Upload your business PDFs and I will answer questions from all of them!</div></div>
</div>
<div class="typing" id="typing">AI is thinking...</div>
<div class="input-area">
  <input type="text" id="msg" placeholder="Upload PDFs first then ask anything..." onkeypress="if(event.key===\'Enter\')send()">
  <button id="btn" onclick="send()">Send</button>
</div>
<script>
document.getElementById("pdffile").onchange=function(){
  var files=this.files;
  if(!files.length)return;
  document.getElementById("status").textContent="Uploading "+files.length+" file(s)...";
  var fd=new FormData();
  for(var i=0;i<files.length;i++){fd.append("pdfs",files[i]);}
  fetch("/upload",{method:"POST",body:fd}).then(r=>r.json()).then(d=>{
    document.getElementById("status").textContent=d.message;
    var list=document.getElementById("pdf-list");
    list.innerHTML="";
    d.files.forEach(function(f){
      var tag=document.createElement("span");
      tag.className="pdf-tag";
      tag.textContent="📄 "+f;
      list.appendChild(tag);
    });
  });
};
function send(){
  var msg=document.getElementById("msg").value.trim();
  if(!msg)return;
  var chat=document.getElementById("chat");
  var typing=document.getElementById("typing");
  var btn=document.getElementById("btn");
  chat.innerHTML+=\'<div class="msg user"><div class="bubble">\'+msg+\'</div></div>\';
  document.getElementById("msg").value="";
  typing.style.display="block";
  btn.disabled=true;
  chat.scrollTop=chat.scrollHeight;
  fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg})}).then(r=>r.json()).then(d=>{
    typing.style.display="none";
    chat.innerHTML+=\'<div class="msg ai"><div class="bubble">\'+d.reply+\'</div><div class="source">📄 \'+d.source+\'</div></div>\';
    chat.scrollTop=chat.scrollHeight;
    btn.disabled=false;
  });
}
</script>
</body></html>'''

# UPGRADED — accepts multiple PDFs at once
@app.route('/upload', methods=['POST'])
def upload():
    global all_pdf_chunks
    try:
        files = request.files.getlist('pdfs')  # Get ALL uploaded files

        if not files:
            return jsonify({"message": "No files uploaded!", "files": []})

        uploaded_names = []

        # Process each PDF one by one
        for file in files:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))

            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text()

            full_text = clean(full_text)

            # Store chunks with PDF name as key
            # Like labelling a drawer with the file name
            all_pdf_chunks[file.filename] = split_into_chunks(full_text, 300)
            uploaded_names.append(file.filename)

        total_chunks = sum(len(v) for v in all_pdf_chunks.values())

        return jsonify({
            "message": f"✅ {len(uploaded_names)} PDFs uploaded → {total_chunks} total chunks ready!",
            "files": uploaded_names
        })

    except Exception as e:
        return jsonify({"message": "❌ Error reading PDFs!", "files": []})

# UPGRADED — searches across all PDFs
@app.route('/chat', methods=['POST'])
def chat():
    global all_pdf_chunks
    try:
        data = request.json
        msg = data.get('message', '')

        if not all_pdf_chunks:
            return jsonify({
                "reply": "Please upload PDFs first!",
                "source": ""
            })

        # Find best chunk AND which PDF it came from
        best_chunk, source_pdf = find_best_chunk(msg, all_pdf_chunks)

        if not best_chunk:
            return jsonify({
                "reply": "I could not find relevant information.",
                "source": ""
            })

        system = f"""You are a helpful business AI assistant built by Piyush Sambhwani.
Answer questions based on this content only:

{best_chunk}

Be helpful and precise. Plain text only, no ** symbols."""

        keys = API_KEYS.copy()
        random.shuffle(keys)

        for key in keys:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": system + "\n\nQuestion: " + msg}]}]}
            result = requests.post(url, json=payload, timeout=15).json()

            if "candidates" in result:
                reply = clean(result["candidates"][0]["content"]["parts"][0]["text"])
                return jsonify({
                    "reply": reply,
                    "source": source_pdf  # Tell user WHICH PDF had the answer
                })

        return jsonify({"reply": "Please try again!", "source": ""})

    except Exception as e:
        return jsonify({"reply": "Something went wrong!", "source": ""})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
