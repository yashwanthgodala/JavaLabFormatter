# Used to convert JSON text into Python objects
import json
import os
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
def analyze_with_gemini(text):

    prompt = """
You are a Java Programming Lab question extractor.

Read the provided Java lab PDF text and extract the questions.

IMPORTANT RULES:

1. Preserve the original wording of the questions exactly.
   Do NOT rewrite, summarize, simplify, combine, or paraphrase
   the main question.

2. Preserve the original wording of every bullet/detail exactly
   as much as possible.

3. Do NOT guess or invent filenames.

4. Do NOT guess or invent subsection titles.

5. Keep each bullet/detail associated with the correct question
   and program.
6. Detect FileName/File Name information from the PDF.
   The filename must be copied exactly from the source text.
7. If a question contains MULTIPLE different filenames, create a
   separate program object for each filename.
8. If a question contains ONLY ONE filename, still store it internally,
   but the formatter will not display the filename separately.
9. Do not create separate programs merely because a question has
   a), b), c) subparts. Create separate programs when they represent
   different filenames/programs.
10. For questions involving errors, use section_type = "Errors".
11. Otherwise use section_type = "Output".
12. Do not invent filenames, programs, subparts, or information.
13. If a filename belongs to a subsection such as
    "Static Fields (Class Variables)", preserve that subsection title
    in section_title.

14. Preserve the original subsection title exactly.
    Do not replace it with the program name.

15. The section_title and filename must remain separate pieces of information.
16. Preserve subsection headings exactly as they appear in the PDF.

17. A subsection heading is text such as:
    "Static Fields (Class Variables)"
    "Static Methods"
    "Static Initialization Block"
    "Single / Simple Inheritance"
    "Hierarchical Inheritance"
    "Multi-level Inheritance"

18. If a subsection heading appears before a FileName/File Name,
    store that heading in section_title.

19. Do NOT use the program name as section_title.

20. Do NOT duplicate the same detail in both the question-level
    details array and a program's details array.

21. If a requirement is specifically associated with a filename,
    put it only inside that program's details array.

22. Preserve FileName/File Name information exactly as it appears
    in the source.

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

If there is only one filename for a question, still put it inside
the programs array.

PDF TEXT:
""" + text

    # Send the PDF text and instructions to Gemini
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    # Return Gemini's response
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

    # Get the uploaded PDF
    file = request.files["pdf"]

    # Read the PDF
    reader = PdfReader(file)

    text = ""

    # Extract text from every page
    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    # Send PDF text to Gemini
    ai_result = analyze_with_gemini(text)

    questions = clean_json_response(ai_result)

    # Correct filenames and subsection titles using
    # the original PDF text.
    questions = apply_source_metadata(
        questions,
        text
    )

    formatted_text = format_questions(questions)

    # Send the formatted result to frontend
    return jsonify({
        "questions": questions,
        "formatted_text": formatted_text
    })
# Start the Flask development server
if __name__ == "__main__":
    app.run(debug=True)