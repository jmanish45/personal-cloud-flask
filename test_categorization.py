# Let's create a simple test script to diagnose the categorization issue
# filepath: c:\Users\jdoll\OneDrive\Desktop\projects 2nd year\personal_cloud\test_categorization.py

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test if API key is loaded
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
print(f"API Key starts with: {api_key[:10] if api_key else 'None'}...")

# Test imports
try:
    import google.generativeai as genai
    print("✓ google.generativeai imported successfully")
except ImportError as e:
    print(f"✗ Failed to import google.generativeai: {e}")

try:
    from ai_utils import categorize_files_with_ai
    print("✓ categorize_files_with_ai imported successfully")
except ImportError as e:
    print(f"✗ Failed to import categorize_files_with_ai: {e}")
except Exception as e:
    print(f"✗ Error in ai_utils.py: {e}")

# Test Gemini configuration
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✓ Gemini model configured successfully")
    
    # Test basic AI call
    response = model.generate_content("Say 'Hello World'")
    response.resolve()
    print(f"✓ Basic AI test successful: {response.text}")
    
except Exception as e:
    print(f"✗ Gemini configuration failed: {e}")

# Test with mock file data
class MockFileMetadata:
    def __init__(self, filename, tags):
        self.filename = filename
        self.tags = tags

mock_files = [
    MockFileMetadata("document.pdf", "document, official, important"),
    MockFileMetadata("vacation.jpg", "photo, travel, beach, summer"),
    MockFileMetadata("receipt.pdf", "receipt, purchase, store")
]

try:
    from ai_utils import categorize_files_with_ai
    result = categorize_files_with_ai(mock_files)
    print(f"✓ Categorization test successful: {result}")
except Exception as e:
    print(f"✗ Categorization test failed: {e}")
    import traceback
    traceback.print_exc()