import io
import re
import os
import math
import random
import requests
from flask import Flask, request, jsonify
import PyPDF2

app = Flask(__name__)

API_KEYS = [
    os.environ.get("GROQ_KEY_1", ""),
    os.environ.get("GROQ_KEY_2", ""),
    os.environ.get("GROQ_KEY_3", ""),
]
API_KEYS = [k for k in API_KEYS if k]

all_pdf_chunks = {}
history = []

def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

def split_into_chunks(text, chunk_size=300):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def find_best_chunk(question, all_chunks_dict):
    stopwords = {
        'the','a','an','is','it','in','on','at','to','for','of','and','or',
        'what','how','when','where','who','which','does','do','are','was',
        'were','will','can','could','should','would','have','has','had',
        'be','been','being','me','my','your','i','tell','about','please'
    }
    question_words = set(question.lower().split()) - stopwords
    all_chunks_flat = []
    for chunks in all_chunks_dict.values():
        all_chunks_flat.extend(chunks)
    total_chunks = len(all_chunks_flat)
    if total_chunks == 0:
        return "", ""
    best_chunk = ""
    best_score = 0
    best_pdf = ""
    for pdf_name, chunks in all_chunks_dict.items():
        for chunk in chunks:
            chunk_words = chunk.lower().split()
            score = 0
            for word in question_words:
                tf = chunk_words.count(word) / len(chunk_words) if chunk_words else 0
                chunks_with_word = sum(1 for c in all_chunks_flat if word in c.lower().split())
                idf = math.log(total_chunks / (chunks_with_word + 1)) + 1
                score += tf * idf
            if score > best_score:
                best_score = score
                best_chunk = chunk
                best_pdf = pdf_name
    return best_chunk, best_pdf

def ask_groq(api_key, messages):
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


# ============================================================
# DEMO 1 — Original DocMind demo (already existed)
# This loads info about Piyush's own services
# ============================================================
@app.route('/load-demo', methods=['POST'])
def load_demo():
    global all_pdf_chunks, history
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
    return jsonify({"message": "DocMind demo loaded! Ask me about pricing, services, or how it works."})


# ============================================================
# DEMO 2 — Restaurant Demo (NEW)
# Imagine a real restaurant called Spice Garden
# A restaurant owner will see this and think "this is for ME"
# ============================================================
@app.route('/load-restaurant-demo', methods=['POST'])
def load_restaurant_demo():
    global all_pdf_chunks, history

    # Clear old data and history so fresh demo starts
    all_pdf_chunks = {}
    history = []

    # This is fake restaurant data — like a menu document
    # In real client work, the client sends their actual menu PDF
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

    # Store this text as chunks — same as uploading a PDF
    all_pdf_chunks["SpiceGarden_Menu.pdf"] = split_into_chunks(clean(restaurant_text), 300)

    return jsonify({
        "message": "🍽️ Spice Garden Restaurant demo loaded! Ask about menu items, prices, timings, or anything!"
    })


# ============================================================
# DEMO 3 — Clinic Demo (NEW)
# A fake clinic called CityHealth Clinic
# A doctor or clinic owner will see this and want to buy
# ============================================================
@app.route('/load-clinic-demo', methods=['POST'])
def load_clinic_demo():
    global all_pdf_chunks, history

    # Clear old data and start fresh
    all_pdf_chunks = {}
    history = []

    # Fake clinic document — like their brochure or services PDF
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

    # Store clinic text as chunks
    all_pdf_chunks["CityHealth_Clinic.pdf"] = split_into_chunks(clean(clinic_text), 300)

    return jsonify({
        "message": "🏥 CityHealth Clinic demo loaded! Ask about doctors, services, prices, or timings!"
    })


from flask import render_template

@app.route('/')
def home():
    return render_template('index.html')

def home_old():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DocMind AI — by Piyush Sambhwani</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:#07080f;--surface:#0d0f1a;--surface2:#111320;--border:rgba(255,255,255,0.06);--border2:rgba(255,255,255,0.1);--accent:#7c5cfc;--accent2:#5eead4;--accent3:#f472b6;--text:#f1f5f9;--muted:#64748b;}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{height:100%;overflow:hidden;}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);display:flex;flex-direction:column;height:100vh;overflow:hidden;}
.bg-orb{position:fixed;border-radius:50%;filter:blur(80px);opacity:0.12;pointer-events:none;z-index:0;animation:drift 8s ease-in-out infinite;}
.o1{width:400px;height:400px;background:#7c5cfc;top:-100px;left:-100px;}
.o2{width:300px;height:300px;background:#5eead4;bottom:-80px;right:-80px;animation-delay:-3s;}
.o3{width:200px;height:200px;background:#f472b6;top:50%;left:50%;animation-delay:-5s;}
@keyframes drift{0%,100%{transform:translate(0,0) scale(1);}33%{transform:translate(20px,-20px) scale(1.05);}66%{transform:translate(-15px,15px) scale(0.95);}}
.layout{position:relative;z-index:1;display:flex;flex-direction:column;height:100vh;max-width:520px;margin:0 auto;width:100%;}
header{padding:14px 20px 12px;background:rgba(7,8,15,0.9);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);flex-shrink:0;}
.header-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;}
.brand{display:flex;align-items:center;gap:10px;}
.brand-icon{width:36px;height:36px;background:linear-gradient(135deg,#7c5cfc,#5eead4);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:17px;box-shadow:0 0 20px rgba(124,92,252,0.4);}
.brand-name{font-size:15px;font-weight:700;letter-spacing:-0.5px;}
.brand-name span{color:var(--accent);}
.brand-sub{font-size:10px;color:var(--muted);font-family:'JetBrains Mono',monospace;}
.header-right{display:flex;align-items:center;gap:8px;}
.status-pill{display:flex;align-items:center;gap:5px;padding:4px 10px;background:rgba(94,234,212,0.08);border:1px solid rgba(94,234,212,0.2);border-radius:20px;font-size:10px;color:var(--accent2);font-family:'JetBrains Mono',monospace;}
.status-dot{width:5px;height:5px;background:var(--accent2);border-radius:50%;animation:pulse-dot 2s infinite;}
@keyframes pulse-dot{0%,100%{opacity:1;}50%{opacity:0.3;}}
.fiverr-btn{display:flex;align-items:center;gap:5px;padding:6px 12px;background:linear-gradient(135deg,#1dbf73,#19a463);border:none;border-radius:8px;color:#fff;font-size:11px;font-weight:700;cursor:pointer;text-decoration:none;font-family:'Inter',sans-serif;transition:all 0.2s;box-shadow:0 4px 12px rgba(29,191,115,0.3);}
.fiverr-btn:hover{transform:translateY(-1px);box-shadow:0 6px 16px rgba(29,191,115,0.4);}
.use-cases{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:10px;}
.uc{padding:3px 10px;background:rgba(124,92,252,0.08);border:1px solid rgba(124,92,252,0.2);border-radius:20px;font-size:10px;color:#a78bfa;}
.upload-row{display:flex;gap:8px;align-items:stretch;}
.upload-zone{flex:1;border:1.5px dashed rgba(124,92,252,0.3);border-radius:12px;padding:10px 14px;cursor:pointer;transition:all 0.3s;background:rgba(124,92,252,0.04);display:flex;align-items:center;gap:10px;}
.upload-zone:hover{border-color:rgba(124,92,252,0.6);background:rgba(124,92,252,0.08);}
.upload-icon{font-size:18px;}
.upload-text strong{display:block;font-size:12px;font-weight:600;}
.upload-text span{font-size:10px;color:var(--muted);}

/* NEW — demo buttons row, 3 buttons side by side */
.demo-row{display:flex;gap:6px;margin-top:8px;}

/* Each demo button style */
.demo-btn{flex:1;padding:8px 6px;border-radius:12px;font-size:10px;font-weight:700;cursor:pointer;font-family:'Inter',sans-serif;transition:all 0.2s;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;border:1.5px solid;}

/* DocMind demo button — purple/teal color */
.demo-btn.docmind{background:linear-gradient(135deg,rgba(94,234,212,0.15),rgba(124,92,252,0.15));border-color:rgba(94,234,212,0.3);color:var(--accent2);}
.demo-btn.docmind:hover{background:rgba(94,234,212,0.2);transform:translateY(-1px);}

/* Restaurant demo button — orange/warm color */
.demo-btn.restaurant{background:linear-gradient(135deg,rgba(251,146,60,0.15),rgba(239,68,68,0.1));border-color:rgba(251,146,60,0.4);color:#fb923c;}
.demo-btn.restaurant:hover{background:rgba(251,146,60,0.2);transform:translateY(-1px);}

/* Clinic demo button — green/health color */
.demo-btn.clinic{background:linear-gradient(135deg,rgba(34,197,94,0.15),rgba(16,185,129,0.1));border-color:rgba(34,197,94,0.4);color:#22c55e;}
.demo-btn.clinic:hover{background:rgba(34,197,94,0.2);transform:translateY(-1px);}

.demo-btn span{font-size:16px;}
.pdf-chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px;}
.chip{display:flex;align-items:center;gap:4px;padding:3px 10px;background:rgba(124,92,252,0.12);border:1px solid rgba(124,92,252,0.25);border-radius:20px;font-size:11px;color:#a78bfa;animation:chip-in 0.3s ease;}
@keyframes chip-in{from{opacity:0;transform:scale(0.8);}to{opacity:1;transform:scale(1);}}
.stats-bar{display:flex;justify-content:space-around;padding:8px 0 0;border-top:1px solid var(--border);margin-top:8px;}
.stat{text-align:center;}
.stat-num{font-size:13px;font-weight:700;color:var(--accent);}
.stat-label{font-size:9px;color:var(--muted);font-family:'JetBrains Mono',monospace;}
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
.sender-name{font-size:11px;font-weight:600;color:var(--muted);}
.bubble{padding:11px 15px;border-radius:16px;font-size:13.5px;line-height:1.65;}
.msg.user .bubble{background:linear-gradient(135deg,#7c5cfc,#5b3fd4);color:#fff;border-bottom-right-radius:4px;box-shadow:0 4px 16px rgba(124,92,252,0.3);}
.msg.ai .bubble{background:var(--surface2);border:1px solid var(--border2);border-bottom-left-radius:4px;box-shadow:0 4px 16px rgba(0,0,0,0.3);}
.source-tag{display:inline-flex;align-items:center;gap:4px;margin-top:6px;padding:3px 8px;background:rgba(94,234,212,0.08);border:1px solid rgba(94,234,212,0.15);border-radius:10px;font-size:10px;color:var(--accent2);font-family:'JetBrains Mono',monospace;}
.typing-msg{display:none;padding:0 20px;}
.typing-header{display:flex;align-items:center;gap:6px;margin-bottom:5px;}
.typing-bubble{padding:12px 16px;background:var(--surface2);border:1px solid var(--border2);border-radius:16px;border-bottom-left-radius:4px;display:inline-flex;align-items:center;gap:5px;}
.dot{width:7px;height:7px;background:var(--accent);border-radius:50%;animation:bounce 1.2s infinite;}
.dot:nth-child(2){animation-delay:0.15s;background:var(--accent2);}
.dot:nth-child(3){animation-delay:0.3s;background:var(--accent3);}
@keyframes bounce{0%,60%,100%{transform:translateY(0);opacity:0.4;}30%{transform:translateY(-6px);opacity:1;}}
.suggestions{padding:0 20px 8px;display:flex;flex-wrap:wrap;gap:6px;flex-shrink:0;}
.sug{padding:6px 13px;background:rgba(124,92,252,0.06);border:1px solid rgba(124,92,252,0.2);border-radius:20px;font-size:11.5px;color:#a78bfa;cursor:pointer;font-family:'Inter',sans-serif;transition:all 0.2s;}
.sug:hover{background:rgba(124,92,252,0.15);border-color:rgba(124,92,252,0.5);color:#fff;transform:translateY(-1px);}
.input-wrap{padding:10px 20px 16px;background:rgba(7,8,15,0.9);backdrop-filter:blur(20px);border-top:1px solid var(--border);flex-shrink:0;}
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
          <div class="brand-sub">by Piyush Sambhwani</div>
        </div>
      </div>
      <div class="header-right">
        <div class="status-pill"><div class="status-dot"></div>RAG LIVE</div>
        <a href="https://www.fiverr.com/piyushsam" target="_blank" class="fiverr-btn">🚀 Hire Me</a>
      </div>
    </div>
    <div class="use-cases">
      <div class="uc">🍽️ Restaurant</div>
      <div class="uc">🏥 Clinic</div>
      <div class="uc">⚖️ Legal</div>
      <div class="uc">👔 HR</div>
      <div class="uc">🛒 E-commerce</div>
      <div class="uc">🎓 Education</div>
    </div>
    <div class="upload-row">
      <input type="file" id="pdffile" accept=".pdf" multiple style="display:none">
      <div class="upload-zone" onclick="document.getElementById('pdffile').click()">
        <div class="upload-icon">📂</div>
        <div class="upload-text">
          <strong>Upload your documents</strong>
          <span>PDF files · Multiple allowed · Instant AI processing</span>
        </div>
      </div>
    </div>

    <!-- NEW: 3 demo buttons side by side -->
    <div class="demo-row">
      <button class="demo-btn docmind" onclick="loadDemo('docmind')">
        <span>🧠</span>DocMind
      </button>
      <button class="demo-btn restaurant" onclick="loadDemo('restaurant')">
        <span>🍽️</span>Restaurant
      </button>
      <button class="demo-btn clinic" onclick="loadDemo('clinic')">
        <span>🏥</span>Clinic
      </button>
    </div>

    <div class="pdf-chips" id="pdf-chips"></div>
    <div class="stats-bar">
      <div class="stat"><div class="stat-num">TF-IDF</div><div class="stat-label">Smart Search</div></div>
      <div class="stat"><div class="stat-num">Multi-PDF</div><div class="stat-label">All Docs</div></div>
      <div class="stat"><div class="stat-num">Memory</div><div class="stat-label">Remembers</div></div>
      <div class="stat"><div class="stat-num">Instant</div><div class="stat-label">Answers</div></div>
    </div>
  </header>
  <div class="chat" id="chat">
    <div class="msg ai">
      <div class="msg-header"><div class="avatar ai-av">AI</div><span class="sender-name">DocMind AI</span></div>
      <div class="bubble">👋 Welcome! Upload any business document and I will answer questions from it instantly.<br><br>⚡ Try a live demo — <strong>🧠 DocMind</strong> for AI services, <strong>🍽️ Restaurant</strong> for a menu demo, or <strong>🏥 Clinic</strong> for a medical demo!</div>
    </div>
  </div>
  <div class="typing-msg" id="typing">
    <div class="typing-header"><div class="avatar ai-av">AI</div><span class="sender-name">DocMind AI</span></div>
    <div class="typing-bubble"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
  </div>
  <div class="suggestions" id="sugs" style="display:none">
    <button class="sug" onclick="ask(this)">💰 What are your prices?</button>
    <button class="sug" onclick="ask(this)">⚡ How does it work?</button>
    <button class="sug" onclick="ask(this)">🏢 Which industries?</button>
    <button class="sug" onclick="ask(this)">📦 What is included?</button>
  </div>
  <div class="input-wrap">
    <div class="input-box">
      <input type="text" id="msg" placeholder="Ask anything about your documents..." onkeypress="if(event.key==='Enter')send()">
      <button id="send-btn" onclick="send()">&#10148;</button>
    </div>
    <div class="powered-by">Powered by <span>RAG + TF-IDF</span> · Built by <span>Piyush Sambhwani</span></div>
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
  fetch('/upload',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
    addMessage('ai','&#9989; '+d.message,null);
    document.getElementById('sugs').style.display='none';
  });
};

// This function now handles all 3 demo types
// type = 'docmind' or 'restaurant' or 'clinic'
function loadDemo(type) {
  // Pick the right URL based on which button was clicked
  var url = '/load-demo';
  var chipLabel = '⚡ DocMind_Demo.pdf';
  var suggestions = [
    '💰 What are your prices?',
    '⚡ How does it work?',
    '🏢 Which industries?',
    '📦 What is included?'
  ];

  // If restaurant button clicked, use restaurant URL
  if (type === 'restaurant') {
    url = '/load-restaurant-demo';
    chipLabel = '🍽️ SpiceGarden_Menu.pdf';
    suggestions = [
      '🍗 Do you have butter chicken?',
      '🕐 What are your timings?',
      '💰 How much is paneer tikka?',
      '🥗 Show me vegetarian options'
    ];
  }

  // If clinic button clicked, use clinic URL
  if (type === 'clinic') {
    url = '/load-clinic-demo';
    chipLabel = '🏥 CityHealth_Clinic.pdf';
    suggestions = [
      '🩺 Which doctors are available?',
      '💰 What is consultation fee?',
      '🦷 Do you have dental services?',
      '🕐 What are clinic timings?'
    ];
  }

  // Call the backend route
  fetch(url, {method:'POST'}).then(r=>r.json()).then(d=>{
    // Show which file is loaded
    document.getElementById('pdf-chips').innerHTML =
      '<div class="chip">' + chipLabel + '</div>';

    // Show the welcome message
    addMessage('ai', d.message, null);

    // Show relevant suggestion buttons
    var sugsDiv = document.getElementById('sugs');
    sugsDiv.innerHTML = '';
    suggestions.forEach(function(s) {
      var btn = document.createElement('button');
      btn.className = 'sug';
      btn.textContent = s;
      btn.onclick = function(){ ask(this); };
      sugsDiv.appendChild(btn);
    });
    sugsDiv.style.display = 'flex';
  });
}

function ask(btn){
  // Remove emoji from start when sending as question
  var text = btn.textContent.trim();
  // Remove first 2 chars if they are emoji + space
  document.getElementById('msg').value = text.slice(2).trim();
  send();
}

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
            return jsonify({"reply": "Please upload a PDF or click a demo button first!", "source": ""})
        best_chunk, source_pdf = find_best_chunk(msg, all_pdf_chunks)
        system = f"""You are DocMind AI, a helpful assistant built by Piyush Sambhwani.
Answer questions based ONLY on this content:

{best_chunk}

Rules:
- Be helpful, friendly and precise
- Plain text only, no ** or markdown symbols
- Keep answers concise and clear
- If answer is not in the content, say: I don't have that information in the uploaded documents."""
        messages = [{"role": "system", "content": system}]
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": msg})
        history.append({"role": "user", "content": msg})
        keys = API_KEYS.copy()
        random.shuffle(keys)
        for key in keys:
            try:
                reply = ask_groq(key, messages)
                reply = clean(reply)
                history.append({"role": "assistant", "content": reply})
                if len(history) > 10:
                    history = history[-10:]
                return jsonify({"reply": reply, "source": source_pdf})
            except Exception:
                continue
        return jsonify({"reply": "All API keys busy. Please try again!", "source": ""})
    except Exception as e:
        return jsonify({"reply": f"Something went wrong: {str(e)}", "source": ""})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
