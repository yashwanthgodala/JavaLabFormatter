# ☕ Java Lab Formatter

A web-based tool that automatically extracts and formats Java Programming Lab content from PDF files into a clean and structured `.txt` format.

The project is designed to simplify the process of converting unstructured lab PDFs into an organized format that is easier to read, use, and maintain.


## 🌐 Live Website

**https://jlf.onrender.com**

> The application is hosted on Render's free tier, so the first request after a period of inactivity may take a little longer while the service wakes up.

---

## 🚀 Features

- 📄 Upload PDF files
- 🔍 Intelligent PDF content extraction
- 🖼️ Support for text-based and image-based PDF content
- 🤖 AI-powered content analysis using Google Gemini
- ✨ Automatic formatting and structuring
- 📁 Detects Java program/file names
- 📚 Handles multiple programs within a document
- ⬇️ Download formatted content as a `.txt` file
- 🌐 Fully web-based
- 💻 No installation required for end users

---

## 🛠️ Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- Flask
- Flask-CORS

### PDF Processing
- PyPDF

### AI
- Google Gemini API
- Gemini Files API

### Deployment
- Render
- Gunicorn

### Version Control
- Git
- GitHub

---

## 📂 Project Structure

```text
JavaLabFormatter/
│
├── index.html
├── style.css
├── script.js
├── requirements.txt
├── .gitignore
│
└── Backend/
    └── app.py
```
## Recommended

- Java Programming Lab question papers
- Java lab assignment PDFs
- Java practical/lab question sheets
- PDFs containing programming questions


## ⚙️ How It Works

```text
PDF Question Paper
       ↓
   PDF Upload
       ↓
   Text Extraction
       ↓
   Gemini AI Analysis
       ↓
 Question Structuring
       ↓
   TXT Formatting
       ↓
 Preview / Download
