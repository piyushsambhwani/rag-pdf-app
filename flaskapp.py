import io
import re
import os
import math
import random
import requests
from flask import Flask, request, jsonify, send_from_directory
import PyPDF2

app = Flask(__name__)

# ============================================================
# CONFIG — Load API keys from environment variables
# Add as many keys as you have: GROQ_KEY_1, GROQ_KEY_2, etc.
# ============================================================
API_KEYS = [
    os.environ.get("GROQ_KEY_1", ""),
    os.environ.get("GROQ_KEY_2", ""),
    os.environ.get("GROQ_KEY_3", ""),
]
API_KEYS = [k for k in API_KEYS if k]  # Remove empty keys

# Global storage — holds all PDF chunks and chat history
all_pdf_chunks = {}
history = []


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean(text):
    """Remove extra spaces and clean up text."""
    return re.sub(r'\s+', ' ', text).strip()


def split_into_chunks(text, chunk_size=300):
    """
    Split big text into smaller pieces (chunks).
    Like cutting a long book into pages.
    chunk_size=300 means each chunk has ~300 words.
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def find_best_chunk(question, all_chunks_dict):
    """
    TF-IDF Search — finds the most relevant chunk for a question.

    TF  = how often a word appears in this chunk (Term Frequency)
    IDF = how rare that word is across all chunks (Inverse Document Frequency)
    Score = TF * IDF — higher score means more relevant chunk.

    This is RAG retrieval — find the right piece of info before asking AI.
    """
    # Common words that don't help find the right chunk
    stopwords = {
        'the', 'a', 'an', 'is', 'it', 'in', 'on', 'at', 'to', 'for',
        'of', 'and', 'or', 'what', 'how', 'when', 'where', 'who', 'which',
        'does', 'do', 'are', 'was', 'were', 'will', 'can', 'could',
        'should', 'would', 'have', 'has', 'had', 'be', 'been', 'being',
        'me', 'my', 'your', 'i', 'tell', 'about', 'please', 'give', 'show'
    }

    # Get only meaningful words from the question
    question_words = set(question.lower().split()) - stopwords

    # Flatten all chunks from all PDFs into one list (for IDF calculation)
    all_chunks_flat = []
    for chunks in all_chunks_dict.values():
        all_chunks_flat.extend(chunks)

    total_chunks = len(all_chunks_flat)
    if total_chunks == 0:
        return "", ""

    best_chunk = ""
    best_score = 0
    best_pdf = ""

    # Score every chunk from every PDF
    for pdf_name, chunks in all_chunks_dict.items():
        for chunk in chunks:
            chunk_words = chunk.lower().split()
            score = 0
            for word in question_words:
                # TF: how many times does this word appear in this chunk?
                tf = chunk_words.count(word) / len(chunk_words) if chunk_words else 0
                # IDF: how rare is this word across all chunks?
                chunks_with_word = sum(1 for c in all_chunks_flat if word in c.lower().split())
                idf = math.log(total_chunks / (chunks_with_word + 1)) + 1
                score += tf * idf
            # Keep track of the highest scoring chunk
            if score > best_score:
                best_score = score
                best_chunk = chunk
                best_pdf = pdf_name

    return best_chunk, best_pdf


def ask_groq(api_key, messages):
    """
    Call the Groq API with the conversation messages.
    Uses llama-3.1-8b-instant — fast and free model.
    """
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
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    result = response.json()
    return result["choices"][0]["message"]["content"]


# ============================================================
# SERVE THE FRONTEND HTML
# ============================================================

@app.route('/')
def home():
    """Serve the main landing page HTML file."""
    return send_from_directory('.', 'docmind_improved.html')


# ============================================================
# DEMO 1 — DocMind AI Services Demo
# Shows Piyush's own AI service packages and pricing
# ============================================================

@app.route('/load-demo', methods=['POST'])
def load_demo():
    global all_pdf_chunks, history

    # Reset everything for fresh demo
    all_pdf_chunks = {}
    history = []

    demo_text = """
    DocMind AI is a RAG powered document intelligence system built by Piyush Sambhwani.
    It allows any business to upload their documents and instantly get answers from them using AI.

    Services offered by Piyush Sambhwani include custom AI document assistants, WhatsApp AI bots,
    clinic and hospital AI assistants, restaurant menu AI systems, legal document analyzers,
    HR policy assistants, e-commerce product assistants, and educational AI tutors.

    Pricing packages are as follows.
    Basic package costs 35 dollars and includes a single document AI assistant with
    standard question answering, delivered in 3 days.
    Standard package costs 75 dollars and includes multi-document support, conversation memory,
    custom branding, and cloud deployment, delivered in 5 days.
    Premium package costs 150 dollars and includes everything in standard plus priority support,
    unlimited revisions, WhatsApp integration, and 30 days of free maintenance, delivered in 7 days.

    Technology used includes Python, Flask, Groq AI with Llama 3, RAG retrieval augmented generation,
    TF-IDF smart search, and cloud deployment on Render. All apps are mobile friendly and work on any device.

    Industries served include restaurants, clinics, law firms, schools and colleges, HR departments,
    real estate agencies, e-commerce stores, and any business with documents they want to make searchable.

    How it works in 3 steps. Step one, you share your business documents like menus, policies,
    price lists, or FAQs. Step two, Piyush builds a custom AI system trained on your documents.
    Step three, your customers or staff can ask questions and get instant accurate answers 24 hours a day.

    Contact and ordering. Available on Fiverr at fiverr.com/piyushsam. Response guaranteed within 24 hours.
    Free consultation available before ordering. 100 percent satisfaction guarantee with unlimited revisions.
    """

    all_pdf_chunks["DocMind_Demo.pdf"] = split_into_chunks(clean(demo_text), 300)

    return jsonify({
        "message": "🧠 DocMind AI demo loaded! Ask me about pricing, services, or how it works."
    })


# ============================================================
# DEMO 2 — Restaurant Demo (Spice Garden)
# Shows a restaurant owner exactly what their AI would look like
# ============================================================

@app.route('/load-restaurant-demo', methods=['POST'])
def load_restaurant_demo():
    global all_pdf_chunks, history

    all_pdf_chunks = {}
    history = []

    restaurant_text = """
    Welcome to Spice Garden Restaurant. We are open every day from 11 AM to 11 PM.
    We are located at 42 MG Road, Pune, Maharashtra. Phone number is 9876543210.
    We accept cash, UPI, credit cards and debit cards.
    Home delivery is available through Swiggy and Zomato.
    Table reservations can be made by calling us or through our website.

    Starters and Appetizers.
    Paneer Tikka costs 180 rupees. It is vegetarian. Soft paneer cubes marinated in spices and grilled.
    Chicken Tikka costs 220 rupees. It is non-vegetarian. Tender chicken pieces grilled in tandoor.
    Veg Spring Rolls cost 150 rupees. Crispy rolls filled with mixed vegetables.
    Chicken Wings cost 250 rupees. Spicy fried chicken wings served with dipping sauce.
    Mushroom Crispy costs 160 rupees. It is vegetarian. Deep fried mushrooms with chilli sauce.
    Hara Bhara Kabab costs 170 rupees. It is vegetarian. Spinach and peas kabab pan fried.

    Main Course Vegetarian.
    Butter Paneer Masala costs 280 rupees. Paneer in rich tomato and butter gravy.
    Palak Paneer costs 260 rupees. Paneer cooked in fresh spinach gravy.
    Dal Makhani costs 220 rupees. Black lentils slow cooked overnight in butter and cream.
    Chole Bhature costs 180 rupees. Spiced chickpeas served with two fluffy bhature.
    Veg Biryani costs 200 rupees. Fragrant basmati rice cooked with mixed vegetables and spices.
    Paneer Biryani costs 240 rupees. Basmati rice cooked with paneer and aromatic spices.
    Aloo Jeera costs 180 rupees. Simple potatoes cooked with cumin seeds.
    Mix Veg costs 200 rupees. Seasonal vegetables cooked in onion tomato gravy.

    Main Course Non Vegetarian.
    Butter Chicken costs 320 rupees. Tender chicken in creamy tomato butter sauce. Our bestseller.
    Chicken Biryani costs 280 rupees. Aromatic basmati rice cooked with spiced chicken.
    Mutton Rogan Josh costs 380 rupees. Slow cooked mutton in Kashmiri spices.
    Chicken Korma costs 300 rupees. Chicken in mild creamy yogurt and nut gravy.
    Fish Curry costs 340 rupees. Fresh fish in coastal style spicy curry.
    Egg Curry costs 220 rupees. Boiled eggs in spiced onion tomato gravy.

    Breads.
    Tandoori Roti costs 30 rupees. Whole wheat bread baked in tandoor.
    Butter Naan costs 50 rupees. Soft leavened bread baked in tandoor with butter.
    Garlic Naan costs 60 rupees. Naan topped with garlic and coriander.
    Paratha costs 60 rupees. Flaky whole wheat bread cooked on tawa.
    Puri costs 30 rupees per piece. Deep fried puffed bread.

    Rice.
    Steamed Basmati Rice costs 120 rupees. Plain steamed basmati rice.
    Jeera Rice costs 140 rupees. Steamed rice tempered with cumin seeds.

    Desserts.
    Gulab Jamun costs 120 rupees. Two pieces. Soft milk dumplings in sugar syrup.
    Kulfi costs 130 rupees. Traditional Indian ice cream in pista or mango flavor.
    Rasgulla costs 110 rupees. Two pieces. Soft cheese balls in light sugar syrup.
    Gajar Halwa costs 150 rupees. Carrot pudding cooked in ghee and milk with dry fruits.
    Ice Cream costs 100 rupees. Two scoops. Available in vanilla, chocolate, and strawberry.

    Beverages.
    Sweet Lassi costs 80 rupees. Chilled yogurt based sweet drink.
    Salted Lassi costs 80 rupees. Chilled yogurt drink with cumin and salt.
    Mango Lassi costs 100 rupees. Yogurt blended with fresh mango pulp.
    Masala Chai costs 50 rupees. Spiced Indian tea with ginger and cardamom.
    Cold Coffee costs 120 rupees. Chilled blended coffee with milk.
    Fresh Lime Soda costs 80 rupees. Available sweet, salted, or mixed.
    Soft Drinks costs 60 rupees. Pepsi, 7UP, Mirinda available.
    Mineral Water costs 30 rupees.

    Combo Meals.
    Family Pack A costs 999 rupees. Serves 4 people. Includes 2 main course, 4 naan, rice, dal, and 2 desserts.
    Lunch Thali costs 220 rupees. Dal, sabzi, rice, 2 roti, salad, and dessert. Available 11 AM to 3 PM only.
    Business Lunch costs 180 rupees. Quick meal for office goers. Ready in 15 minutes.

    Allergy and dietary information.
    All vegetarian items are marked green on the menu. We use separate utensils for veg and non veg cooking.
    We do not use MSG in any of our dishes. All our food is prepared fresh daily.
    Please inform our staff about any allergies before ordering.

    Special services.
    We offer catering for events, weddings, and corporate functions.
    Minimum order for catering is 50 persons. Contact us 3 days in advance for catering bookings.
    We offer a 10 percent discount for orders above 2000 rupees.
    Senior citizens get 5 percent discount on all orders.
    """

    all_pdf_chunks["SpiceGarden_Menu.pdf"] = split_into_chunks(clean(restaurant_text), 300)

    return jsonify({
        "message": "🍽️ Spice Garden Restaurant demo loaded! Ask about menu items, prices, timings, or anything!"
    })


# ============================================================
# DEMO 3 — Clinic Demo (CityHealth Clinic)
# Shows a doctor or clinic owner exactly what their AI would look like
# ============================================================

@app.route('/load-clinic-demo', methods=['POST'])
def load_clinic_demo():
    global all_pdf_chunks, history

    all_pdf_chunks = {}
    history = []

    clinic_text = """
    Welcome to CityHealth Clinic. We are a multi-specialty clinic located at 15 FC Road, Pune.
    Our phone number is 020-4567890 and mobile is 9988776655.
    We are open Monday to Saturday from 9 AM to 8 PM. Sunday timing is 10 AM to 2 PM.
    We accept cash, UPI, all insurance cards, and corporate health cards.
    We have ambulance service available 24 hours. Call 108 for emergency.

    Doctors and Specialties.
    Dr. Priya Sharma is our General Physician. MBBS MD. Available Monday Wednesday Friday 10 AM to 1 PM.
    Dr. Rajesh Patel is our Cardiologist. MBBS MD DM Cardiology. Available Tuesday Thursday 11 AM to 2 PM.
    Dr. Meena Joshi is our Gynecologist. MBBS MS Gynecology. Available Monday to Friday 9 AM to 12 PM.
    Dr. Suresh Kumar is our Orthopedic Surgeon. MBBS MS Orthopedics. Available Wednesday Saturday 10 AM to 1 PM.
    Dr. Anita Desai is our Pediatrician for children. MBBS MD Pediatrics. Available Daily 10 AM to 12 PM.
    Dr. Vijay Singh is our Dermatologist for skin. MBBS MD Dermatology. Available Tuesday Friday 3 PM to 6 PM.
    Dr. Ritu Agarwal is our Eye Specialist. MBBS MS Ophthalmology. Available Monday Thursday 11 AM to 2 PM.
    Dr. Arun Mehta is our Dentist. BDS MDS. Available Monday to Saturday 10 AM to 7 PM.

    Services and Treatments.
    General consultation fee is 300 rupees. Specialist consultation fee is 500 rupees.
    Follow-up consultation within 7 days is free of charge.
    We provide complete annual health checkup packages.

    Diagnostic Services.
    Blood tests are available. Basic CBC blood test costs 200 rupees. Reports in 4 hours.
    Complete blood count and sugar and thyroid package costs 800 rupees.
    Urine test costs 150 rupees. Reports in 2 hours.
    X-Ray is available for chest, hand, leg and spine. Chest X-ray costs 400 rupees.
    ECG for heart test costs 300 rupees. Report given immediately.
    Ultrasound costs 600 rupees. Abdominal and obstetric ultrasound available.
    Echocardiography costs 1200 rupees. Done by cardiologist only.

    Dental Services.
    Dental cleaning costs 500 rupees.
    Tooth filling costs 800 rupees per tooth.
    Root canal treatment costs 3500 rupees per tooth.
    Tooth extraction costs 600 rupees. Wisdom tooth extraction costs 1500 rupees.
    Dental crown costs 4000 rupees per tooth.
    Braces consultation is free. Braces treatment starts from 25000 rupees.
    Teeth whitening costs 3000 rupees.

    Eye Care Services.
    Eye checkup and vision test costs 300 rupees.
    Spectacle prescription is given after eye test.
    Cataract surgery consultation is free.
    Contact lens fitting and consultation costs 400 rupees.

    Physiotherapy.
    Physiotherapy sessions are available. First session costs 500 rupees.
    Package of 10 sessions costs 4000 rupees.
    Back pain, neck pain, knee pain treatment available.
    Sports injury rehabilitation also available.

    Vaccinations.
    We provide all standard vaccinations for children and adults.
    COVID booster, flu vaccine, typhoid vaccine, hepatitis vaccine available.
    Travel vaccination package available for international travelers.

    Health Packages.
    Basic Health Package costs 1500 rupees. Includes blood test, urine test, ECG, and general consultation.
    Comprehensive Health Package costs 3500 rupees. Includes all basic tests plus ultrasound, chest X-ray, and specialist consultation.
    Senior Citizen Package costs 2500 rupees. Complete checkup for age 60 and above with diet counseling.
    Women Health Package costs 2000 rupees. Includes gynecology consultation, blood tests, and bone density check.
    Corporate Health Package available for companies. Minimum 20 employees. Contact us for pricing.

    Appointments and Booking.
    You can book appointment by calling 9988776655.
    Online booking available on our website cityhealth.in.
    WhatsApp booking available on same number 9988776655.
    Walk-in patients accepted but appointment patients are given priority.
    Waiting time for appointment is usually 10 to 15 minutes.
    Waiting time for walk-in patients is 30 to 45 minutes.

    Insurance and Payments.
    We accept Star Health, New India, HDFC Ergo, Bajaj Allianz, and all major insurance.
    Cashless treatment available for networked insurance.
    For reimbursement, we provide all documents and bills.
    EMI facility available for treatments above 10000 rupees.

    Home Services.
    Doctor home visit available for senior citizens and bedridden patients. Fee is 800 rupees.
    Home blood sample collection available. Fee is 200 rupees plus test charges.
    Nursing care at home also available. Contact us for details.

    Emergency Services.
    24 hour emergency helpline is 9988776655.
    First aid and emergency care available during clinic hours.
    We have tie-up with City Hospital for major emergency referrals.
    Ambulance service can be arranged. Call 108 for free ambulance.
    """

    all_pdf_chunks["CityHealth_Clinic.pdf"] = split_into_chunks(clean(clinic_text), 300)

    return jsonify({
        "message": "🏥 CityHealth Clinic demo loaded! Ask about doctors, services, prices, or timings!"
    })


# ============================================================
# PDF UPLOAD — Real client documents
# Client sends their actual PDF, we extract text and chunk it
# ============================================================

@app.route('/upload', methods=['POST'])
def upload():
    global all_pdf_chunks
    try:
        files = request.files.getlist('pdfs')
        if not files:
            return jsonify({"message": "No files uploaded!", "files": []})

        uploaded_names = []
        for file in files:
            # Read PDF bytes and extract all text
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            full_text = ""
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + " "  # Space between pages

            full_text = clean(full_text)

            if not full_text.strip():
                # PDF had no extractable text (maybe scanned image)
                return jsonify({
                    "message": f"Could not read text from {file.filename}. Make sure it is not a scanned image PDF.",
                    "files": []
                })

            # Split into chunks and store by filename
            all_pdf_chunks[file.filename] = split_into_chunks(full_text, 300)
            uploaded_names.append(file.filename)

        total_chunks = sum(len(v) for v in all_pdf_chunks.values())
        return jsonify({
            "message": f"✅ {len(uploaded_names)} PDF(s) loaded — {total_chunks} chunks ready! Now ask me anything.",
            "files": uploaded_names
        })

    except Exception as e:
        return jsonify({
            "message": f"Error reading PDF: {str(e)}",
            "files": []
        })


# ============================================================
# CHAT — The main RAG pipeline
# 1. Find best chunk (retrieval)
# 2. Build prompt with that chunk (augmentation)
# 3. Send to Groq AI (generation)
# ============================================================

@app.route('/chat', methods=['POST'])
def chat():
    global all_pdf_chunks, history
    try:
        data = request.json
        msg = data.get('message', '').strip()

        if not msg:
            return jsonify({"reply": "Please type a question!", "source": ""})

        # No documents loaded yet
        if not all_pdf_chunks:
            return jsonify({
                "reply": "Please upload a PDF or click a demo button first! 👆",
                "source": ""
            })

        # Step 1 — RETRIEVAL: Find the most relevant chunk using TF-IDF
        best_chunk, source_pdf = find_best_chunk(msg, all_pdf_chunks)

        if not best_chunk:
            return jsonify({
                "reply": "I could not find relevant information. Please try a different question.",
                "source": ""
            })

        # Step 2 — AUGMENTATION: Build the system prompt with the retrieved chunk
        # This is where RAG magic happens — AI only knows what's in the chunk
        system_prompt = f"""You are DocMind AI, a helpful assistant built by Piyush Sambhwani.
Answer questions based ONLY on this content from the document:

---
{best_chunk}
---

Rules:
- Be helpful, friendly and precise
- Use plain text only — no stars, no markdown symbols, no bullet dashes
- Keep answers concise and clear
- If the answer is not in the content above, say: I don't have that information in the uploaded documents.
- Do not make up any information that is not in the content above."""

        # Build messages: system + conversation history + new question
        messages = [{"role": "system", "content": system_prompt}]

        # Add last 10 messages from history (so AI remembers the conversation)
        for h in history[-10:]:
            messages.append({"role": h["role"], "content": h["content"]})

        # Add the current question
        messages.append({"role": "user", "content": msg})

        # Save user message to history
        history.append({"role": "user", "content": msg})

        # Step 3 — GENERATION: Try each API key (shuffle for load balancing)
        keys = API_KEYS.copy()
        random.shuffle(keys)

        if not keys:
            return jsonify({
                "reply": "No API keys configured. Please set GROQ_KEY_1 in your environment variables.",
                "source": ""
            })

        for key in keys:
            try:
                reply = ask_groq(key, messages)
                reply = clean(reply)

                # Save AI reply to history
                history.append({"role": "assistant", "content": reply})

                # Keep history trimmed to last 20 messages (10 exchanges)
                if len(history) > 20:
                    history = history[-20:]

                return jsonify({"reply": reply, "source": source_pdf})

            except Exception as api_error:
                # This key failed, try the next one
                print(f"API key failed: {str(api_error)}")
                continue

        # All keys failed
        return jsonify({
            "reply": "All API keys are busy right now. Please try again in a moment!",
            "source": ""
        })

    except Exception as e:
        return jsonify({
            "reply": f"Something went wrong: {str(e)}",
            "source": ""
        })


# ============================================================
# HEALTH CHECK — Useful for Render deployment monitoring
# Visit /health to see if the server is running
# ============================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "running",
        "chunks_loaded": sum(len(v) for v in all_pdf_chunks.values()),
        "pdfs_loaded": list(all_pdf_chunks.keys()),
        "history_length": len(history),
        "api_keys_configured": len(API_KEYS)
    })


# ============================================================
# CLEAR — Reset everything (optional utility route)
# POST to /clear to wipe all loaded documents and history
# ============================================================

@app.route('/clear', methods=['POST'])
def clear():
    global all_pdf_chunks, history
    all_pdf_chunks = {}
    history = []
    return jsonify({"message": "All documents and history cleared."})


# ============================================================
# RUN THE APP
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

