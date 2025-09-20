import google.generativeai as genai
import os
from PIL import Image
import PyPDF2
import docx

# Configure the Gemini API with the key from the .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_file(file_path):
    """
    Analyzes various file types (images, PDFs, DOCX) using the Gemini API 
    and returns descriptive tags.
    """
    try:
        # 1. HANDLE IMAGES
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            img = Image.open(file_path)
            prompt = "Analyze this image and provide a comma-separated list of 5-7 relevant keywords or tags that describe its content, objects, and any text present. For example: 'document, ID card, university, student photo'."
            response = model.generate_content([prompt, img])
            response.resolve()
            tags = [tag.strip() for tag in response.text.split(',')]
            return tags

        # 2. HANDLE PDFS
        elif file_path.lower().endswith('.pdf'):
            text_content = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text_content += page.extract_text() or ""
            if text_content:
                prompt = f"""
                You are an AI assistant that analyzes documents. Your only job is to extract key topics, entities, and concepts from the following text and present them as a comma-separated list of 7 to 10 relevant tags. 
                Do not add any summary or introductory text. Only return the comma-separated list.
                For example: 'project report, quarterly results, financial data'.
                Text to analyze: '{text_content[:4000]}'
                """
                response = model.generate_content(prompt)
                response.resolve()
                tags = [tag.strip() for tag in response.text.split(',')]
                return tags
            return ['pdf', 'document']

        # 3. HANDLE WORD DOCUMENTS
        elif file_path.lower().endswith('.docx'):
            doc = docx.Document(file_path)
            text_content = "\n".join([para.text for para in doc.paragraphs])
            if text_content:
                prompt = f"""
                You are an AI assistant that analyzes documents. Your only job is to extract key topics, entities, and concepts from the following text and present them as a comma-separated list of 7 to 10 relevant tags. 
                Do not add any summary or introductory text. Only return the comma-separated list.
                For example: 'project report, quarterly results, financial data'.
                Text to analyze: '{text_content[:4000]}'
                """
                response = model.generate_content(prompt)
                response.resolve()
                tags = [tag.strip() for tag in response.text.split(',')]
                return tags
            return ['docx', 'document']

        # 4. HANDLE OTHER FILES
        else:
            return [os.path.splitext(file_path)[1].strip('.')]

    except Exception as e:
        print(f"Error analyzing file {file_path}: {e}")
        return None

def find_semantic_matches(query, files_metadata):
    """
    Uses Gemini to find semantically relevant files based on a user's query.
    """
    if not files_metadata:
        return []
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
        matching_filenames = [name.strip() for name in response.text.split(',') if name.strip()]
        return matching_filenames
    except Exception as e:
        print(f"Error during semantic search: {e}")
        return []

def categorize_files_with_ai(files_metadata):
    """
    Uses Gemini to sort a list of files into meaningful categories.
    """
    if not files_metadata:
        return {}
    file_info_list = [f"Filename: {meta.filename}, Tags: {meta.tags}" for meta in files_metadata]
    file_info_string = "\n".join(file_info_list)
    prompt = f"""
    You are an expert file organizer for a personal cloud storage.
    Here is a list of a user's files and their AI-generated tags:
    {file_info_string}
    Your task is to group these files into precise, meaningful categories.
    Use intuitive categories like "Documents & IDs", "Study Materials", "Travel Photos", "College Memories", "Receipts & Invoices", etc.
    Do not create too many categories; group similar items together.
    Return your answer ONLY as a comma-separated list of key-value pairs, where the key is the category name and the value is the exact filename.
    For example:
    Category:Receipts & Invoices, Filename:receipt.pdf, Category:Receipts & Invoices, Filename:invoice.jpg, Category:Travel Photos, Filename:paris_trip.png
    """
    try:
        response = model.generate_content(prompt)
        response.resolve()
        categorized_files = {}
        parts = response.text.strip().split(',')
        for i in range(0, len(parts), 2):
            try:
                key_part = parts[i]
                value_part = parts[i+1]
                category = key_part.split(':')[1].strip()
                filename = value_part.split(':')[1].strip()
                if category not in categorized_files:
                    categorized_files[category] = []
                categorized_files[category].append(filename)
            except IndexError:
                continue
        # --- THIS IS THE FIX ---
        # Add any files the AI missed to an 'Other' category
        ai_categorized_filenames = {fname for sublist in categorized_files.values() for fname in sublist}
        all_filenames = {meta.filename for meta in files_metadata}
        uncategorized = all_filenames - ai_categorized_filenames
        if uncategorized:
            categorized_files['Other'] = list(uncategorized)
        return categorized_files
    except Exception as e:
        print(f"Error during AI categorization: {e}")
        return {"Uncategorized": [meta.filename for meta in files_metadata]}
    