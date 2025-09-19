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
# ... existing analyze_file function ...

def find_semantic_matches(query, files_metadata):
    """
    Uses Gemini to find semantically relevant files based on a user's query.
    """
    if not files_metadata:
        return []

    # Create a simplified list of files and their tags for the prompt
    file_info_list = [f"Filename: {meta.filename}, Tags: {meta.tags}" for meta in files_metadata]
    file_info_string = "\n".join(file_info_list)

    prompt = f"""
    You are a smart search engine for a personal cloud storage.
    A user is searching for: "{query}"

    Here is a list of their files and associated tags:
    {file_info_string}

    Analyze the user's search query and the file tags. Return ONLY a comma-separated list of the exact filenames that are the most semantically relevant matches. If there are no good matches, return an empty string.
    """

    try:
        response = model.generate_content(prompt)
        response.resolve()
        
        # The model should return a comma-separated string of filenames
        matching_filenames = [name.strip() for name in response.text.split(',') if name.strip()]
        return matching_filenames
    except Exception as e:
        print(f"Error during semantic search: {e}")
        return []