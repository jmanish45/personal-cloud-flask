import google.generativeai as genai
import os
from PIL import Image
import PyPDF2
import docx
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

# --- DIAGNOSTIC: Check if the key is loaded ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("🔴 CRITICAL ERROR: GEMINI_API_KEY not found in .env file.")
else:
    print("✅ SUCCESS: Gemini API key loaded.")

# Configure the Gemini API
try:
    genai.configure(api_key=api_key)
    # Use the stable, versioned model name
    model = genai.GenerativeModel('gemini-2.5-flash')
    print(f"✅ SUCCESS: Gemini model '{model.model_name}' initialized.")
except Exception as e:
    print(f"🔴 CRITICAL ERROR: Failed to configure Gemini. Error: {e}")
    model = None


def analyze_file(file_path):
    if not model:
        print("🔴 ERROR in analyze_file: Model not initialized. Skipping analysis.")
        return None
    
    print(f"🔍 Analyzing file: {os.path.basename(file_path)}...")
    try:
        # 1. HANDLE IMAGES
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            img = Image.open(file_path)
            prompt = "Analyze this image and provide a comma-separated list of 5-7 relevant keywords or tags that describe its content, objects, and any text present. For example: 'document, ID card, university, student photo'."
            response = model.generate_content([prompt, img])
            response.resolve()
            tags = [tag.strip() for tag in response.text.split(',')]
            print(f"✅ SUCCESS: Image analysis complete. Tags: {tags}")
            return tags

        # 2. HANDLE PDFS
        elif file_path.lower().endswith('.pdf'):
            text_content = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text_content += page.extract_text() or ""
            if text_content:
                prompt = f"""You are an AI assistant analyzing a document. Extract key topics, entities, and concepts from the following text and return ONLY a comma-separated list of 7-10 relevant tags. Text: '{text_content[:4000]}'"""
                response = model.generate_content(prompt)
                response.resolve()
                tags = [tag.strip() for tag in response.text.split(',')]
                print(f"✅ SUCCESS: PDF analysis complete. Tags: {tags}")
                return tags
            return ['pdf', 'document']

        # 3. HANDLE WORD DOCUMENTS
        elif file_path.lower().endswith('.docx'):
            doc = docx.Document(file_path)
            text_content = "\n".join([para.text for para in doc.paragraphs])
            if text_content:
                prompt = f"""You are an AI assistant analyzing a document. Extract key topics, entities, and concepts from the following text and return ONLY a comma-separated list of 7-10 relevant tags. Text: '{text_content[:4000]}'"""
                response = model.generate_content(prompt)
                response.resolve()
                tags = [tag.strip() for tag in response.text.split(',')]
                print(f"✅ SUCCESS: DOCX analysis complete. Tags: {tags}")
                return tags
            return ['docx', 'document']

        # 4. HANDLE OTHER FILES
        else:
            return [os.path.splitext(file_path)[1].strip('.')]

    except Exception as e:
        print(f"🔴 ERROR during file analysis for {os.path.basename(file_path)}: {e}")
        return None

def find_semantic_matches(query, files_metadata):
    if not model:
        print("🔴 ERROR in find_semantic_matches: Model not initialized.")
        return []
    #...(rest of function is correct)
    file_info_list = [f"Filename: {meta.filename}, Tags: {meta.tags}" for meta in files_metadata]
    file_info_string = "\n".join(file_info_list)
    prompt = f"""A user is searching for: "{query}". Here is a list of their files and tags:\n{file_info_string}\nReturn ONLY a comma-separated list of the exact filenames that are the most semantically relevant matches. If none, return an empty string."""
    try:
        response = model.generate_content(prompt)
        response.resolve()
        return [name.strip() for name in response.text.split(',') if name.strip()]
    except Exception as e:
        print(f"🔴 ERROR during semantic search: {e}")
        return []

def categorize_files_with_ai(files_metadata):
    if not model:
        print("🔴 ERROR in categorize_files_with_ai: Model not initialized.")
        return {"Uncategorized": [meta.filename for meta in files_metadata]}
    if not files_metadata:
        return {}
    #...(rest of function is correct)
    file_info_list = [f"Filename: {meta.filename}, Tags: {meta.tags}" for meta in files_metadata]
    file_info_string = "\n".join(file_info_list)
    prompt = f"""You are an expert file organizer. Group these files into precise, meaningful categories based on their tags. Use categories like "Documents & IDs", "Study Materials", "Photos & Memories", "Receipts & Invoices", etc. Return ONLY a comma-separated list of key-value pairs. Example: Category:Receipts, Filename:receipt.pdf, Category:Photos, Filename:trip.jpg\n\nFiles:\n{file_info_string}"""
    try:
        response = model.generate_content(prompt)
        response.resolve()
        categorized_files = {}
        parts = response.text.strip().split(',')
        for i in range(0, len(parts), 2):
            try:
                category = parts[i].split(':')[1].strip()
                filename = parts[i+1].split(':')[1].strip()
                if category not in categorized_files:
                    categorized_files[category] = []
                categorized_files[category].append(filename)
            except IndexError:
                continue
        ai_categorized_filenames = {fname for sublist in categorized_files.values() for fname in sublist}
        all_filenames = {meta.filename for meta in files_metadata}
        uncategorized = all_filenames - ai_categorized_filenames
        if uncategorized:
            categorized_files['Other'] = list(uncategorized)
        print(f"✅ SUCCESS: Files categorized into: {list(categorized_files.keys())}")
        return categorized_files
    except Exception as e:
        print(f"🔴 ERROR during AI categorization: {e}")
        return {"Uncategorized": [meta.filename for meta in files_metadata]}

