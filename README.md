# 📂 **Personal Cloud Storage with AI Optimizations**

A lightweight, self-hosted alternative to Google Drive or Dropbox — built with **Python + Flask** and enhanced with **AI-powered features** like Smart Search and Auto-Categorization.  


🚀 Designed as a mini-project today, with a roadmap to evolve into a major AI-powered personal cloud storage in the future.

📝 Project Overview
This project is a personal cloud storage system built with Python and Flask. It provides a simple web interface for users to upload, manage, and access their files, simulating a lightweight, self-hosted version of services like Google Drive. The long-term goal is to integrate AI for smart search and automatic file organization.

✨ Features
✅ Current Features (Mini Project)

📤 File Upload – Upload files directly from the browser.

📂 File Listing – View all uploaded files in a clean list.

👁️ View & Download – Open files in a new tab or download them.

🗑️ File Deletion – Delete files with one click.

✅ User Feedback – Success messages for uploads & deletions.

🚧 Planned Features (Major Project)

🔑 User Accounts – Secure login & personal storage.

🤖 AI Smart Search – Search for files by content, plain English queries, or upload date.

🧠 Auto-Categorization – AI auto-tags files (e.g., Invoices, Photos, IDs).

🔗 File Sharing – Generate shareable file links.

🛠️ Tech Stack
<p align="center"> <!-- Backend --> <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/> <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/> <!-- Database --> <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/> <!-- Frontend --> <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5"/> <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3"/> <img src="https://img.shields.io/badge/Jinja2-B41717?style=for-the-badge&logo=jinja&logoColor=white" alt="Jinja2"/> <!-- Deployment --> <img src="https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white" alt="Gunicorn"/> <img src="https://img.shields.io/badge/Heroku-430098?style=for-the-badge&logo=heroku&logoColor=white" alt="Heroku"/> </p>

This section will display in GitHub README with stickers/logos of each tool.
It’s grouped into:

Backend 🐍 (Python, Flask)

Database 🗄️ (SQLite)

Frontend 🎨 (HTML, CSS, Jinja2)

⚙️ Installation & Setup
🔧 Prerequisites

Python 3.x

pip (Python package manager)

📥 Steps

Clone the repository

git clone  https://github.com/jmanish45/personal-cloud-flask.git

cd personal-cloud-flask

Live Link of the app : https://personal-cloud-flask.onrender.com/


Create a virtual environment & activate it

# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

Install dependencies

pip install -r requirements.txt

Run the application

python app.py

Open browser at 👉 http://127.0.0.1:5000

Deployment ☁️ (Gunicorn, Heroku)
