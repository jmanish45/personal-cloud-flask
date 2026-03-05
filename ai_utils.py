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
model = None  # Initialize as None

if not api_key:
    print("⚠️ WARNING: GEMINI_API_KEY not found. AI features will be disabled.")
else:
    print("✅ SUCCESS: Gemini API key loaded.")
    # Configure the Gemini API only if key exists
    try:
        genai.configure(api_key=api_key)
        # Use the stable, versioned model name
        model = genai.GenerativeModel('gemini-2.5-flash')
        print(f"✅ SUCCESS: Gemini model '{model.model_name}' initialized.")
    except Exception as e:
        print(f"⚠️ WARNING: Failed to configure Gemini. Error: {e}")
        model = None


def analyze_file(file_path):
    """Analyze file and return both tags and category in a single AI call."""
    if not model:
        print("🔴 ERROR in analyze_file: Model not initialized. Skipping analysis.")
        return {"tags": None, "category": "Uncategorized"}
    
    filename = os.path.basename(file_path)
    print(f"🔍 Analyzing file: {filename}...")
    
    try:
        # 1. HANDLE IMAGES
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            img = Image.open(file_path)
            img.load()  # Force load image data into memory
            prompt = f"""You are an expert AI file organizer for a personal cloud storage system. Your task is to analyze this image thoroughly and provide accurate tags and categorization.

FILENAME: {filename}

ANALYSIS INSTRUCTIONS:
1. Carefully examine the image content, objects, people, text, colors, and context
2. Identify what type of image this is (photo, screenshot, document scan, artwork, meme, etc.)
3. Extract meaningful keywords that would help the user find this image later
4. Determine the most appropriate category based on the image's purpose and content

TAG GUIDELINES:
- Provide 5-7 highly relevant, specific tags
- Include: main subjects, objects, actions, emotions, colors (if significant), text content (if readable)
- Use lowercase words, be specific (e.g., "golden retriever" not just "dog")
- Include context clues (e.g., "outdoor", "night", "celebration", "formal")
- If it's a screenshot, identify the app/website
- If it contains text, include key words from that text

CATEGORY OPTIONS (choose the MOST appropriate ONE):
- Photos: Personal photos, selfies, travel photos, family photos, nature shots, memories
- Screenshots: App screenshots, social media, conversations, error messages
- Documents: Scanned documents, ID cards, certificates, forms, official papers
- Study Materials: Notes, diagrams, educational content, textbook pages, formulas
- Receipts: Bills, invoices, payment confirmations, shopping receipts
- Memes & Entertainment: Funny images, memes, entertainment content
- Work: Professional content, presentations, business materials, work-related
- Art & Design: Artwork, designs, creative content, graphics
- Personal: Personal items, diary entries, private content
- Other: Anything that doesn't fit above categories

RESPOND IN THIS EXACT FORMAT (no extra text):
TAGS: tag1, tag2, tag3, tag4, tag5, tag6, tag7
CATEGORY: CategoryName"""
            response = model.generate_content([prompt, img])
            response.resolve()
            img.close()  # Close the image to release file handle
            return _parse_ai_response(response.text, "image")

        # 2. HANDLE PDFS
        elif file_path.lower().endswith('.pdf'):
            text_content = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = len(reader.pages)
                for page in reader.pages:
                    text_content += page.extract_text() or ""
            
            if text_content:
                prompt = f"""You are an expert AI file organizer for a personal cloud storage system. Your task is to analyze this PDF document thoroughly and provide accurate tags and categorization.

FILENAME: {filename}
PAGE COUNT: {num_pages}

DOCUMENT TEXT (first 4000 characters):
{text_content[:4000]}

ANALYSIS INSTRUCTIONS:
1. Read and understand the document's content, purpose, and context
2. Identify the document type (report, form, certificate, invoice, notes, etc.)
3. Extract key topics, entities, names, dates, and important terms
4. Determine who might have created this and for what purpose

TAG GUIDELINES:
- Provide 7-10 highly relevant, specific tags
- Include: document type, main topic, key entities (names, organizations, products)
- Include dates/time periods if mentioned (e.g., "2024", "Q3", "March")
- Include subject area (e.g., "finance", "medical", "legal", "academic")
- Include action words if applicable (e.g., "invoice", "agreement", "report")
- Be specific: "machine learning research" not just "research"

CATEGORY OPTIONS (choose the MOST appropriate ONE):
- Documents: General documents, letters, forms, agreements, contracts
- Study Materials: Lecture notes, research papers, textbooks, academic content, tutorials
- Receipts: Purchase receipts, bills, payment records
- Invoices: Business invoices, billing statements, payment requests
- Reports: Analysis reports, business reports, research reports, summaries
- Certificates: Certifications, achievements, degrees, licenses, awards
- Financial: Bank statements, tax documents, financial records, investments
- Medical: Health records, prescriptions, medical reports, test results
- Legal: Legal documents, contracts, agreements, court papers
- Personal: Personal letters, diaries, private documents
- Work: Work-related documents, presentations, meeting notes, proposals
- Other: Anything that doesn't fit above categories

RESPOND IN THIS EXACT FORMAT (no extra text):
TAGS: tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8
CATEGORY: CategoryName"""
                response = model.generate_content(prompt)
                response.resolve()
                return _parse_ai_response(response.text, "pdf")
            return {"tags": ['pdf', 'document', 'unreadable'], "category": "Documents"}

        # 3. HANDLE WORD DOCUMENTS
        elif file_path.lower().endswith('.docx'):
            doc = docx.Document(file_path)
            text_content = "\n".join([para.text for para in doc.paragraphs])
            
            if text_content:
                prompt = f"""You are an expert AI file organizer for a personal cloud storage system. Your task is to analyze this Word document thoroughly and provide accurate tags and categorization.

FILENAME: {filename}

DOCUMENT TEXT (first 4000 characters):
{text_content[:4000]}

ANALYSIS INSTRUCTIONS:
1. Read and understand the document's content, structure, and purpose
2. Identify the document type (essay, report, letter, resume, notes, etc.)
3. Extract key topics, themes, names, and important terminology
4. Consider the writing style and intended audience

TAG GUIDELINES:
- Provide 7-10 highly relevant, specific tags
- Include: document type, main topic/subject, key themes
- Include names of people, organizations, or products mentioned
- Include technical terms or domain-specific keywords
- Include format indicators if relevant (e.g., "formal letter", "bullet points", "outline")
- Be descriptive: "project proposal marketing" not just "proposal"

CATEGORY OPTIONS (choose the MOST appropriate ONE):
- Documents: General documents, letters, forms, miscellaneous writings
- Study Materials: Essays, assignments, lecture notes, research, academic writing
- Reports: Business reports, analysis, summaries, evaluations
- Work: Professional documents, proposals, meeting notes, business content
- Personal: Personal writings, journals, creative writing, private content
- Resume & CV: Resumes, CVs, cover letters, job applications
- Letters: Formal letters, correspondence, communications
- Contracts: Agreements, contracts, legal documents
- Other: Anything that doesn't fit above categories

RESPOND IN THIS EXACT FORMAT (no extra text):
TAGS: tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8
CATEGORY: CategoryName"""
                response = model.generate_content(prompt)
                response.resolve()
                return _parse_ai_response(response.text, "docx")
            return {"tags": ['docx', 'document', 'empty'], "category": "Documents"}

        # 4. HANDLE TEXT FILES
        elif file_path.lower().endswith(('.txt', '.md', '.json', '.csv', '.xml', '.html')):
            ext = os.path.splitext(file_path)[1].strip('.')
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = f.read()[:4000]
                
                if text_content.strip():
                    prompt = f"""You are an expert AI file organizer. Analyze this {ext.upper()} file and provide tags and categorization.

FILENAME: {filename}
FILE TYPE: {ext.upper()}

CONTENT (first 4000 characters):
{text_content}

Provide specific, relevant tags based on the content and determine the appropriate category.

CATEGORY OPTIONS: Code, Data, Notes, Configuration, Documents, Study Materials, Work, Personal, Other

RESPOND IN THIS EXACT FORMAT:
TAGS: tag1, tag2, tag3, tag4, tag5
CATEGORY: CategoryName"""
                    response = model.generate_content(prompt)
                    response.resolve()
                    return _parse_ai_response(response.text, ext)
            except Exception as e:
                print(f"⚠️ Could not read text file: {e}")
            return {"tags": [ext, 'text', 'file'], "category": "Documents"}

        # 5. HANDLE CODE FILES
        elif file_path.lower().endswith(('.py', '.js', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.ts', '.jsx', '.tsx')):
            ext = os.path.splitext(file_path)[1].strip('.')
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code_content = f.read()[:3000]
                
                prompt = f"""You are an expert AI file organizer. Analyze this code file and provide tags and categorization.

FILENAME: {filename}
LANGUAGE: {ext.upper()}

CODE (first 3000 characters):
{code_content}

Identify: programming language, frameworks/libraries used, purpose of the code, key functions/classes.

RESPOND IN THIS EXACT FORMAT:
TAGS: tag1, tag2, tag3, tag4, tag5, tag6
CATEGORY: Code"""
                response = model.generate_content(prompt)
                response.resolve()
                return _parse_ai_response(response.text, ext)
            except Exception as e:
                print(f"⚠️ Could not read code file: {e}")
            return {"tags": [ext, 'code', 'programming'], "category": "Code"}

        # 6. HANDLE OTHER FILES (fallback)
        else:
            ext = os.path.splitext(file_path)[1].strip('.').lower()
            
            # Map common extensions to categories
            extension_categories = {
                # Audio
                'mp3': ('audio', 'Music'),
                'wav': ('audio', 'Music'),
                'flac': ('audio', 'Music'),
                'm4a': ('audio', 'Music'),
                'aac': ('audio', 'Music'),
                # Video
                'mp4': ('video', 'Videos'),
                'avi': ('video', 'Videos'),
                'mkv': ('video', 'Videos'),
                'mov': ('video', 'Videos'),
                'wmv': ('video', 'Videos'),
                # Archives
                'zip': ('archive', 'Archives'),
                'rar': ('archive', 'Archives'),
                '7z': ('archive', 'Archives'),
                'tar': ('archive', 'Archives'),
                'gz': ('archive', 'Archives'),
                # Spreadsheets
                'xlsx': ('spreadsheet', 'Documents'),
                'xls': ('spreadsheet', 'Documents'),
                # Presentations
                'pptx': ('presentation', 'Work'),
                'ppt': ('presentation', 'Work'),
                # Executables
                'exe': ('executable', 'Software'),
                'msi': ('installer', 'Software'),
                'dmg': ('installer', 'Software'),
            }
            
            if ext in extension_categories:
                tag_type, category = extension_categories[ext]
                return {"tags": [ext, tag_type, filename.split('.')[0].lower()[:20]], "category": category}
            
            return {"tags": [ext] if ext else ['file', 'unknown'], "category": "Other"}

    except Exception as e:
        print(f"🔴 ERROR during file analysis for {filename}: {e}")
        return {"tags": None, "category": "Uncategorized"}


def _parse_ai_response(response_text, file_type):
    """Parse AI response to extract tags and category."""
    tags = []
    category = "Other"
    
    print(f"📝 Raw AI response:\n{response_text}\n---")
    
    try:
        # Try to find TAGS and CATEGORY in the response
        lines = response_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            # Handle TAGS line (case-insensitive, handle ** markdown formatting)
            if 'TAGS' in line.upper() and ':' in line:
                tags_part = line.split(':', 1)[1].strip()
                # Remove markdown formatting like **
                tags_part = tags_part.replace('**', '').strip()
                tags = [tag.strip() for tag in tags_part.split(',') if tag.strip()]
            # Handle CATEGORY line
            elif 'CATEGORY' in line.upper() and ':' in line:
                cat_part = line.split(':', 1)[1].strip()
                # Remove markdown formatting and brackets
                category = cat_part.replace('**', '').strip('[]').strip()
        
        if not tags:
            # Fallback: try to parse as comma-separated tags
            tags = [tag.strip() for tag in response_text.split(',') if tag.strip()][:7]
        
        # Comprehensive list of valid categories
        valid_categories = [
            # Image categories
            "Photos", "Screenshots", "Memes & Entertainment", "Art & Design",
            # Document categories  
            "Documents", "Study Materials", "Receipts", "Invoices", "Reports",
            "Certificates", "Financial", "Medical", "Legal", "Resume & CV", 
            "Letters", "Contracts",
            # Work & Personal
            "Personal", "Work",
            # Media
            "Music", "Videos", "Archives", "Software",
            # Code & Data
            "Code", "Data", "Notes", "Configuration",
            # Fallback
            "Other", "Uncategorized"
        ]
        
        # Check if category is valid
        if category not in valid_categories:
            # Try to match partial (case-insensitive)
            category_lower = category.lower()
            matched = False
            for valid_cat in valid_categories:
                if valid_cat.lower() in category_lower or category_lower in valid_cat.lower():
                    category = valid_cat
                    matched = True
                    break
            
            if not matched:
                # Smart fallback based on common keywords
                if any(word in category_lower for word in ['photo', 'image', 'picture', 'selfie']):
                    category = "Photos"
                elif any(word in category_lower for word in ['screenshot', 'screen']):
                    category = "Screenshots"
                elif any(word in category_lower for word in ['meme', 'funny', 'entertainment']):
                    category = "Memes & Entertainment"
                elif any(word in category_lower for word in ['study', 'academic', 'education', 'school', 'university', 'lecture']):
                    category = "Study Materials"
                elif any(word in category_lower for word in ['receipt', 'bill', 'purchase']):
                    category = "Receipts"
                elif any(word in category_lower for word in ['invoice', 'billing']):
                    category = "Invoices"
                elif any(word in category_lower for word in ['certificate', 'award', 'degree']):
                    category = "Certificates"
                elif any(word in category_lower for word in ['resume', 'cv', 'cover letter', 'job']):
                    category = "Resume & CV"
                elif any(word in category_lower for word in ['code', 'programming', 'script']):
                    category = "Code"
                elif any(word in category_lower for word in ['work', 'business', 'professional', 'office']):
                    category = "Work"
                elif any(word in category_lower for word in ['personal', 'private', 'diary']):
                    category = "Personal"
                else:
                    category = "Other"
        
        print(f"✅ SUCCESS: {file_type} analysis complete. Tags: {tags}, Category: {category}")
        return {"tags": tags, "category": category}
    except Exception as e:
        print(f"⚠️ Warning: Could not parse AI response: {e}")
        return {"tags": [file_type], "category": "Other"}

def find_semantic_matches(query, files_metadata):
    """Find files that semantically match the user's search query."""
    if not model:
        print("🔴 ERROR in find_semantic_matches: Model not initialized.")
        return []
    
    if not files_metadata:
        return []
    
    file_info_list = [f"- Filename: {meta.filename}, Tags: {meta.tags}, Category: {meta.category or 'Unknown'}" for meta in files_metadata]
    file_info_string = "\n".join(file_info_list)
    
    prompt = f"""You are a smart file search assistant. A user is searching their personal cloud storage.

USER'S SEARCH QUERY: "{query}"

AVAILABLE FILES:
{file_info_string}

INSTRUCTIONS:
1. Understand the user's intent - what are they looking for?
2. Match files based on:
   - Direct keyword matches in filename or tags
   - Semantic similarity (e.g., "homework" matches "assignment", "pic" matches "photo")
   - Category relevance
   - Partial matches and related concepts
3. Include files that would reasonably satisfy the user's search
4. Order by relevance (most relevant first)

RESPOND WITH ONLY:
- A comma-separated list of exact filenames that match
- If no matches found, respond with exactly: NONE

Example response: vacation_photo.jpg, trip_2024.png, beach_sunset.jpg"""

    try:
        response = model.generate_content(prompt)
        response.resolve()
        result = response.text.strip()
        
        if result.upper() == "NONE" or not result:
            return []
        
        return [name.strip() for name in result.split(',') if name.strip()]
    except Exception as e:
        print(f"🔴 ERROR during semantic search: {e}")
        return []


def categorize_by_tags_simple(tags_string):
    """
    Determine category from tags using comprehensive keyword matching (no AI call).
    Used for migrating existing files that have tags but no category.
    """
    if not tags_string:
        return "Uncategorized"
    
    tags_lower = tags_string.lower()
    
    # Define category keywords (ordered by priority - more specific first)
    category_keywords = {
        # Specific categories first
        "Screenshots": ["screenshot", "screen capture", "screen shot", "snip", "printscreen"],
        "Memes & Entertainment": ["meme", "funny", "joke", "entertainment", "viral", "humor"],
        "Receipts": ["receipt", "purchase receipt", "shopping", "transaction", "order confirmation"],
        "Invoices": ["invoice", "billing", "bill", "payment due", "amount due"],
        "Certificates": ["certificate", "certification", "degree", "diploma", "award", "achievement", "license"],
        "Resume & CV": ["resume", "cv", "curriculum vitae", "cover letter", "job application", "career"],
        "Financial": ["bank", "statement", "tax", "financial", "investment", "salary", "income", "expense"],
        "Medical": ["medical", "health", "prescription", "doctor", "hospital", "diagnosis", "patient", "medicine"],
        "Legal": ["legal", "contract", "agreement", "court", "law", "attorney", "lawyer"],
        "Code": ["code", "programming", "python", "javascript", "java", "function", "class", "api", "github", "repository"],
        "Art & Design": ["art", "design", "illustration", "graphic", "creative", "artwork", "drawing", "sketch"],
        
        # Broader categories
        "Study Materials": ["study", "notes", "lecture", "course", "class", "exam", "homework", "assignment", 
                          "textbook", "education", "school", "university", "college", "research", "academic",
                          "thesis", "essay", "tutorial", "learning", "student"],
        "Reports": ["report", "analysis", "summary", "evaluation", "assessment", "review", "findings"],
        "Photos": ["photo", "image", "picture", "selfie", "portrait", "landscape", "camera", "jpg", "jpeg", 
                  "png", "gif", "photography", "snapshot", "shot", "pic", "sunset", "sunrise", "nature",
                  "travel", "vacation", "family", "friends", "memories", "outdoor", "indoor"],
        "Documents": ["document", "form", "id card", "passport", "official", "paper", "file", "pdf", "docx"],
        "Work": ["work", "project", "meeting", "presentation", "business", "client", "company", "office",
                "professional", "corporate", "proposal", "strategy", "plan"],
        "Personal": ["personal", "diary", "journal", "private", "birthday", "anniversary", "gift"],
        "Music": ["music", "song", "audio", "mp3", "wav", "album", "artist", "playlist"],
        "Videos": ["video", "movie", "clip", "mp4", "recording", "footage"],
    }
    
    # Check each category (priority order matters)
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in tags_lower:
                return category
    
    return "Other"


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