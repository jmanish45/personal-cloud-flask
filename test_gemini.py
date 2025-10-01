import google.generativeai as genai
import os
from dotenv import load_dotenv

print("--- Starting Gemini Connection Test ---")

# 1. Load the .env file
load_dotenv()
print("🔍 Step 1: Attempting to load .env file...")

# 2. Get the API key from the environment
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("🔴 CRITICAL FAILURE: Could not find GEMINI_API_KEY in your .env file.")
    print("--- Test Failed ---")
else:
    print("✅ SUCCESS: Found API key in .env file.")
    
    # 3. Configure the Gemini client
    print("🔍 Step 2: Attempting to configure Gemini with the key...")
    try:
        genai.configure(api_key=api_key)
        
        # 4. Initialize the model with the correct format
        # --- THIS IS THE FIX ---
        print("🔍 Step 3: Attempting to initialize the 'models/gemini-pro' model...")
        model = genai.GenerativeModel('models/gemini-pro')
        print("✅ SUCCESS: Model initialized successfully.")

        # 5. Send a test prompt
        print("🔍 Step 4: Sending a test prompt to the AI...")
        response = model.generate_content("What is the capital of India?")
        
        print("\n--- TEST RESULT ---")
        print(f"✅ AI Response: {response.text}")
        print("--- Test Passed ---")

    except Exception as e:
        print("\n--- TEST RESULT ---")
        print(f"🔴 CRITICAL FAILURE: An error occurred during the test.")
        print(f"Error Details: {e}")
        print("--- Test Failed ---")

