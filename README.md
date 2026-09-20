# ☕ Java Lab Formatter

A web-based tool that converts Java Programming Lab question PDFs into a clean, structured TXT format.

Instead of manually copying and formatting questions from a PDF, simply upload the PDF and let the formatter extract and organize the questions automatically.

## 🌐 Live Website

**https://jlf.onrender.com**

> The application is hosted on Render's free tier, so the first request after a period of inactivity may take a little longer while the service wakes up.

---

## ✨ Features

- 📄 Upload Java Lab question PDFs
- 🤖 AI-powered question extraction using Gemini
- 📝 Automatically formats questions into a structured TXT file
- 📌 Preserves question details and subsections
- 📂 Detects program filenames from the source PDF
- ⬇️ Download the formatted TXT file
- 🎨 Interactive machine-style user interface
- 🌐 Accessible directly from a web browser
- 🔐 Gemini API key is stored securely as an environment variable

---

## 📌 What PDF Should I Upload?

> **Note:** Upload a PDF containing questions.  
> For best results, use **Java Programming Lab question PDFs**.

The formatter works best when the PDF contains clearly structured questions, filenames, subsections, and requirements.

### Recommended

- Java Programming Lab question papers
- Java lab assignment PDFs
- Java practical/lab question sheets
- PDFs containing programming questions

### Avoid

- Scanned PDFs with no selectable text
- Image-only PDFs
- PDFs containing only handwritten content
- PDFs unrelated to programming/lab questions

---

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
