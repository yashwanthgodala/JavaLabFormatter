# Used to convert JSON text into Python objects
import json
import os
import tempfile
from flask_cors import CORS
# Flask is used to create our web server/backend
from flask import Flask, request, jsonify,send_from_directory

# PdfReader is used to read text from PDF files
from pypdf import PdfReader

from dotenv import load_dotenv
from google import genai

# Load variables from the .env file
load_dotenv()

# Get the Gemini API key from .env
api_key = os.getenv("GEMINI_API_KEY")

# Create Gemini client using our API key
client = genai.Client(api_key=api_key)


# Create our Flask application
app = Flask(__name__)
CORS(app)  # This allows our frontend to communicate with our backend
# Get the main project folder
# app.py is inside Backend/, so we go one folder up
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Serve the main website
@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


# Serve CSS
@app.route("/style.css")
def style():
    return send_from_directory(BASE_DIR, "style.css")


# Serve JavaScript
@app.route("/script.js")
def script():
    return send_from_directory(BASE_DIR, "script.js")
# This function sends the extracted PDF text to Gemini
# This function sends the PDF text to Gemini
# and asks Gemini to identify the structure of the lab questions.
def analyze_with_gemini(pdf_path, extracted_text=""):
    """
    Sends the actual PDF to Gemini so it can read both normal PDF text
    and text that appears inside images/scanned pages.
    """

    prompt = """
You are a Java Programming Lab question extractor.

Read the ENTIRE attached PDF visually and extract the Java lab questions.
The PDF may contain a mixture of selectable text, scanned text, screenshots,
and images containing questions or Java code. You MUST read text inside
images as well as normal PDF text.

IMPORTANT CUTOFF:
- Extract questions only from Question 1 through Question 13.
- STOP after Question 13.
- Do NOT extract examples, reference material, explanations, code samples,
  or other content that appears after Question 13.
- If Question 13 continues across pages, include all content that belongs
  to Question 13 before stopping.

IMPORTANT RULES:

1. Preserve the original wording of the questions exactly as it appears.
   Do NOT rewrite, summarize, simplify, combine, or paraphrase the main
   question.

2. Preserve the original wording of every bullet/detail as much as possible.

3. Read text from images and screenshots. Do not ignore a question merely
   because it is embedded as an image.

4. Do NOT guess or invent filenames.

5. Do NOT guess or invent subsection titles.

6. Keep each bullet/detail associated with the correct question and program.

7. Detect FileName, File Name, Program Name, and filenames shown inside
   images. Copy the filename exactly from the PDF.

8. If a question contains MULTIPLE different filenames, create a separate
   program object for each filename.

9. If a question contains ONLY ONE filename, still store it inside the
   programs array.

10. Do not create separate programs merely because a question has a), b),
    c) subparts. Create separate programs when they represent different
    filenames/programs.

11. For questions involving errors, use section_type = "Errors".

12. Otherwise use section_type = "Output".

13. Do not invent filenames, programs, subparts, or information.

14. If a filename belongs to a subsection, preserve that subsection title
    in section_title.

15. Preserve the original subsection title exactly.
    Do not replace it with the program name.

16. Keep section_title and filename as separate pieces of information.

17. Do NOT duplicate the same detail in both the question-level details
    array and a program's details array.

18. If a requirement is specifically associated with a filename, put it
    only inside that program's details array.

19. The attached PDF is the primary source of truth. The extracted text
    supplied below is only supplemental because image-only content may be
    missing from it.

20. Ignore code/example material that is not part of Questions 1-13.

Return ONLY valid JSON.
Do NOT use markdown code fences such as ```json.

Use exactly this structure:

{
    "questions": [
        {
            "number": 1,
            "question": "Main question text",
            "details": [
                "Important subpart or requirement"
            ],
            "programs": [
                {
                    "name": "ProgramName",
                    "file_name": "ProgramName.java",
                    "section_title": "Original subsection title",
                    "details": [
                        "Requirement belonging to this program"
                    ],
                    "section_type": "Output"
                }
            ]
        }
    ]
}

SUPPLEMENTAL TEXT EXTRACTED BY PYPDF:
"""

    prompt += extracted_text

    # Upload the actual PDF so Gemini can inspect visual/image content.
    uploaded_pdf = client.files.upload(file=pdf_path)

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[prompt, uploaded_pdf]
    )

    return response.text


# This function cleans Gemini's response
# and converts it into a Python dictionary.
def clean_json_response(response_text):

    # Remove unnecessary spaces from the beginning/end
    response_text = response_text.strip()

    # Remove markdown code fences if Gemini accidentally adds them
    if response_text.startswith("```json"):
        response_text = response_text[7:]

    if response_text.endswith("```"):
        response_text = response_text[:-3]

    # Convert the JSON text into a Python dictionary
    return json.loads(response_text.strip())
def wrap_point(text, prefix="-> ", indent="   ", width=95):
    """
    Wraps text so continuation lines remain
    properly aligned.
    """

    import textwrap

    # Width available for the first line
    first_width = width - len(prefix)

    # Width available for continuation lines
    subsequent_width = width - len(indent)

    # Wrap the text
    first_lines = textwrap.wrap(
        text,
        width=first_width
    )

    if not first_lines:
        return prefix.rstrip()

    result = prefix + first_lines[0]

    # If the first line was already wrapped,
    # wrap the remaining text using the continuation width.
    remaining_text = text[len(first_lines[0]):].strip()

    if remaining_text:

        continuation_lines = textwrap.wrap(
            remaining_text,
            width=subsequent_width
        )

        for line in continuation_lines:
            result += "\n" + indent + line

    return result
def extract_program_metadata(text):
    """
    Extracts exact subsection titles and filenames directly
    from the original PDF text.

    This prevents Gemini from changing filenames or
    subsection names.
    """

    import re

    metadata = []

    # Split the PDF into question blocks using the long separators
    blocks = re.split(r"={80,}", text)

    for block in blocks:

        block = block.strip()

        if not block:
            continue

        # Find question number
        question_match = re.search(
            r"^\s*(\d+)\.\s*",
            block
        )

        if not question_match:
            continue

        question_number = int(question_match.group(1))

        lines = block.splitlines()

        programs = []

        current_section = None

        for line in lines:

            clean_line = line.strip()

            # Ignore empty lines
            if not clean_line:
                continue

            # ---------------------------------------------
            # Detect subsection headings
            # ---------------------------------------------

            if clean_line.startswith("-> "):

                # Remove the arrow
                possible_section = clean_line[3:].strip()

                # Ignore ordinary bullet/details
                # because these usually come after a filename.
                if (
                    "FileName:" not in possible_section
                    and "File Name:" not in possible_section
                ):
                    current_section = possible_section

            # ---------------------------------------------
            # Detect FileName / File Name
            # ---------------------------------------------

            filename_match = re.search(
                r"File\s*Name\s*:\s*(.+)",
                clean_line,
                re.IGNORECASE
            )

            if filename_match:

                filename = filename_match.group(1).strip()

                programs.append({
                    "file_name": filename,
                    "section_title": current_section
                })

                current_section = None

            # ---------------------------------------------
            # Detect filenames without FileName label
            # Example:
            # MethodOverloadingShapes.demo
            # ---------------------------------------------

            elif re.fullmatch(
                r"[\w.-]+\.(?:java|demo)",
                clean_line,
                re.IGNORECASE
            ):

                programs.append({
                    "file_name": clean_line,
                    "section_title": current_section
                })

                current_section = None

        if programs:
            metadata.append({
                "number": question_number,
                "programs": programs
            })

    return metadata
def apply_source_metadata(data, source_text):
    """
    Replaces Gemini's filenames and subsection titles with
    the exact values extracted directly from the PDF.
    """

    metadata = extract_program_metadata(source_text)

    # Process every question
    for question in data["questions"]:

        question_number = question["number"]

        # Find matching question metadata
        matching_question = None

        for item in metadata:

            if item["number"] == question_number:
                matching_question = item
                break

        if not matching_question:
            continue

        source_programs = matching_question["programs"]
        ai_programs = question.get("programs", [])

        # Match programs by their order in the question
        for i in range(
            min(len(source_programs), len(ai_programs))
        ):

            source_program = source_programs[i]
            ai_program = ai_programs[i]

            # -----------------------------------------
            # Use EXACT filename from PDF
            # -----------------------------------------

            ai_program["file_name"] = (
                source_program["file_name"]
            )

            # -----------------------------------------
            # Use EXACT subsection title from PDF
            # -----------------------------------------

            section_title = source_program.get(
                "section_title"
            )

            if section_title:
                ai_program["section_title"] = section_title
            else:
                # No subsection exists for this program
                ai_program["section_title"] = ""

            # -----------------------------------------
            # Generate program name from exact filename
            # -----------------------------------------

            filename = source_program["file_name"]

            # Remove extension
            program_name = filename.rsplit(".", 1)[0]

            ai_program["name"] = program_name

    return data
def format_questions(data):
    """
    Converts Gemini's structured JSON into the required
    Java Lab TXT format.
    """

    output = ""

    # Process every question
    for question in data["questions"]:

        # -------------------------------------------------
        # QUESTION
        # -------------------------------------------------

        output += "=" * 95 + "\n"

        # Wrap the question itself if it is too long
        question_text = wrap_point(
            question["question"],
            prefix=f'{question["number"]}. ',
            indent="   "
        )

        output += question_text + "\n\n"

        programs = question.get("programs", [])

        # -------------------------------------------------
        # QUESTION DETAILS
        # -------------------------------------------------

        for detail in question.get("details", []):

            output += wrap_point(
                detail,
                prefix="-> ",
                indent="   "
            ) + "\n"

        # -------------------------------------------------
        # PROGRAM DETAILS
        # -------------------------------------------------

        for program in programs:

            program_details = program.get("details", [])

            # Details already present at question level
            question_details = question.get("details", [])

            # Remove duplicate details
            unique_details = []

            for detail in program_details:

                if detail not in question_details:
                    unique_details.append(detail)

            # -------------------------------------------------
            # MULTIPLE PROGRAMS
            # -------------------------------------------------

            if len(programs) > 1:

                output += "\n"

                # Show subsection title
                section_title = program.get("section_title", "")

                if section_title:

                    output += wrap_point(
                        section_title,
                        prefix="-> ",
                        indent="   "
                    ) + "\n"

                # Show filename under subsection
                if program.get("file_name"):

                    output += (
                        f'   FileName: '
                        f'{program["file_name"]}\n'
                    )

                # Show program-specific details
                for detail in unique_details:

                    output += wrap_point(
                        detail,
                        prefix="   -> ",
                        indent="      "
                    ) + "\n"

            # -------------------------------------------------
            # SINGLE PROGRAM
            # -------------------------------------------------

            else:

                # Show filename at the normal left margin
                if program.get("file_name"):

                    output += "\n"
                    output += (
                        f'FileName: '
                        f'{program["file_name"]}\n'
                    )

                # Show program details normally
                for detail in unique_details:

                    output += wrap_point(
                        detail,
                        prefix="-> ",
                        indent="   "
                    ) + "\n"

        # -------------------------------------------------
        # SEPARATOR BEFORE PROGRAM
        # -------------------------------------------------

        output += "=" * 95 + "\n"

        # -------------------------------------------------
        # PROGRAM SECTIONS
        # -------------------------------------------------

        for program in programs:

            # Multiple programs get their own heading
            if len(programs) > 1:

                output += (
                    f'----------  '
                    f'{program["name"]}'
                    f'  ----------\n'
                )

            output += "----- Program -----\n"

            # Java program will be inserted later
            output += "\n"

            # Output or Errors
            section_type = program.get(
                "section_type",
                "Output"
            )

            output += f"----- {section_type} -----\n"

            # Output/errors will be inserted later
            output += "\n"

            # Space between multiple programs
            if len(programs) > 1:
                output += "\n"

        output += "\n"

    return output
# This creates an API endpoint called "/upload"
# The frontend will send the PDF file to this endpoint
@app.route("/upload", methods=["POST"])
def upload():

    # Get the uploaded PDF from the browser.
    file = request.files.get("pdf")

    if not file:
        return jsonify({"error": "No PDF file was uploaded."}), 400

    # Save the uploaded PDF temporarily because the Gemini Files API
    # accepts a local file path.
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp_file:
            file.save(temp_file)
            temp_path = temp_file.name

        # Extract normal/selectable PDF text as supplemental information.
        # Gemini will also inspect the actual PDF for image-based content.
        reader = PdfReader(temp_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        # Send both the actual PDF and its extracted text to Gemini.
        ai_result = analyze_with_gemini(
            temp_path,
            text
        )

        questions = clean_json_response(ai_result)

        # Safety cutoff: this formatter currently stops at Question 13.
        questions["questions"] = [
            question
            for question in questions.get("questions", [])
            if isinstance(question.get("number"), int)
            and question["number"] <= 13
        ]

        formatted_text = format_questions(questions)

        return jsonify({
            "questions": questions,
            "formatted_text": formatted_text
        })

    except Exception as error:
        print("UPLOAD ERROR:", error)
        return jsonify({
            "error": "Failed to process the PDF.",
            "details": str(error)
        }), 500

    finally:
        # Remove the temporary local copy after processing.
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# Start the Flask development server
if __name__ == "__main__":
    app.run(debug=True)
