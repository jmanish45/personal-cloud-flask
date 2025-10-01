import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("Checking available models...")
try:
    models = list(genai.list_models())
    print(f"Found {len(models)} total models")
    
    print("\nModels that support generateContent:")
    content_models = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            content_models.append(model.name)
            print(f"✓ {model.name}")
            print(f"  Display name: {model.display_name}")
            print(f"  Description: {model.description[:100]}...")
            print()
    
    if content_models:
        print(f"\nTesting first available model: {content_models[0]}")
        test_model = genai.GenerativeModel(content_models[0])
        response = test_model.generate_content("Hello")
        print(f"✓ Test successful: {response.text}")
    else:
        print("❌ No models support generateContent")
        
except Exception as e:
    print(f"❌ Error listing models: {e}")
    print("This might be an API key issue or network problem")