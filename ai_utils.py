import google.generativeai as genai
import os
from PIL import Image

# Configure the Gemini API with the key from the .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_file(file_path):
    """
    Analyzes an image file using the Gemini API and returns descriptive tags.
    """
    try:
        # Check if the file is a supported image type
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            img = Image.open(file_path)
            prompt = "Analyze this image and provide a comma-separated list of 5-7 relevant keywords or tags that describe its content, objects, and any text present. For example: 'document, ID card, university, student photo'."
            
            # Generate content with the model
            response = model.generate_content([prompt, img])
            response.resolve() # Wait for the response to complete
            
            # Clean up the response to get a list of tags
            tags = [tag.strip() for tag in response.text.split(',')]
            return tags

        # Add more file type handlers here in the future (e.g., for PDFs, DOCX)
        else:
            # For non-image files, return the file extension as a basic tag for now
            return [os.path.splitext(file_path)[1].strip('.')]

    except Exception as e:
        print(f"Error analyzing file {file_path}: {e}")
        return None
