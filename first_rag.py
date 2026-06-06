import google.generativeai as genai

# ============================================
# STEP 1: CONNECT TO GEMINI
# ============================================
# Put your Gemini API key here
genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")

# ============================================
# STEP 2: OUR KNOWLEDGE BASE
# ============================================
# This is all the information our RAG knows
# Each item in this list = one chunk
restaurant_info = [
    "Spice Garden restaurant is open 11 AM to 11 PM daily.",
    "We serve North Indian, South Indian and Chinese food.",
    "Our best dish is Butter Chicken which costs 280 rupees.",
    "We have gluten free pasta available for 320 rupees.",
    "We are located at FC Road Pune. Call us at 9876543210.",
    "We deliver within 5 km. Minimum order is 200 rupees.",
    "We have free parking for 50 cars.",
    "We accept cash, UPI and credit cards.",
]

# ============================================
# STEP 3: SEARCH FUNCTION
# ============================================
# This function finds relevant chunks
# for the question asked
# 
# How it works:
# Question = "Do you have pasta?"
# It checks each chunk for matching words
# Chunk with most matching words = most relevant

def find_relevant_chunks(question, chunks, top=2):
    
    # Convert question to lowercase words
    # "Do you have Pasta?" becomes ["do","you","have","pasta?"]
    question_words = question.lower().split()
    
    # This list will store (score, chunk) pairs
    scored = []
    
    # Check each chunk
    for chunk in chunks:
        
        # Convert chunk to lowercase too
        chunk_lower = chunk.lower()
        
        # Count how many question words appear in chunk
        # score = number of matching words found
        score = 0
        for word in question_words:
            if word in chunk_lower:
                score += 1
        
        # Save this chunk with its score
        scored.append((score, chunk))
    
    # Sort by score, highest first
    scored.sort(reverse=True)
    
    # Return only top 2 chunks
    # [0] means first item, [1] means second
    top_chunks = [chunk for score, chunk in scored[:top]]
    
    return top_chunks

# ============================================
# STEP 4: MAIN RAG FUNCTION
# ============================================
# This is where the magic happens

def ask_rag(question):
    
    # PART A: Find relevant chunks
    relevant = find_relevant_chunks(
        question, 
        restaurant_info
    )
    
    # Join chunks into one text
    context = "\n".join(relevant)
    
    # PART B: Ask Gemini using those chunks
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""
    You are a helpful restaurant assistant 
    for Spice Garden restaurant in Pune.
    
    Use only this information to answer:
    {context}
    
    Customer question: {question}
    
    Give a short helpful answer.
    """
    
    response = model.generate_content(prompt)
    return response.text

# ============================================
# STEP 5: TEST IT
# ============================================
print("Spice Garden RAG is Ready!\n")

questions = [
    "What time do you open?",
    "Do you have gluten free food?",
    "Can I pay by UPI?",
    "Where are you located?",
]

for q in questions:
    print("Customer:", q)
    print("Bot:", ask_rag(q))
    print("-" * 40)
