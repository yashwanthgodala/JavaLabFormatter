from flask_cors import CORS
# Flask is used to create our web server/backend
from flask import Flask, request, jsonify

# PdfReader is used to read text from PDF files
from matplotlib import text
from pypdf import PdfReader


# Create our Flask application
app = Flask(__name__)
CORS(app)  # This allows our frontend to communicate with our backend
# This function separates the extracted PDF text into questions
def extract_questions(text):

    # Split the entire text into individual lines
    lines = text.splitlines()

    # This list will store all the questions
    questions = []

    # Store the question currently being processed
    current_question = None

    # Go through every line in the PDF
    for line in lines:

        # Remove unnecessary spaces
        line = line.strip()

        # Ignore completely empty lines
        if not line:
            continue

        # Check whether the line starts with a number
        # Example: "1. Write a Java program..."
        if line[0].isdigit() and "." in line[:4]:

            # If we were already processing a question,
            # save that question before starting the next one
            if current_question:
                questions.append(current_question)

            # Start a new question
            current_question = {
                "number": line.split(".")[0],
                "question": line
            }

        # If this isn't a new question,
        # add the line to the current question
        elif current_question:
            current_question["question"] += "\n" + line

    # Add the final question
    if current_question:
        questions.append(current_question)

    return questions
# This creates an API endpoint called "/upload"
# The frontend will send the PDF file to this endpoint
@app.route("/upload", methods=["POST"])
def upload():

    # Get the PDF file sent by the frontend
    # "pdf" is the name we will give the uploaded file
    file = request.files["pdf"]

    # Create a PDF reader using the uploaded file
    reader = PdfReader(file)

    # Create an empty string
    # We will store all the PDF text here
    text = ""

    # Go through every page in the PDF
    for page in reader.pages:

        # Extract the text from the current page
        # and add it to our text variable
        text += page.extract_text() + "\n"

    # Separate the extracted text into individual questions
    questions = extract_questions(text)

    # Send both the raw text and questions to the frontend
    return jsonify({
        "text": text,
        "questions": questions
    })


# This checks whether we are running this Python file directly
if __name__ == "__main__":

    # Start the Flask development server
    # debug=True automatically reloads the server when we change code
    app.run(debug=True)