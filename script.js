// Get the output area from HTML
const output = document.getElementById("output");
// Get the PDF input element from our HTML
const pdfFile = document.getElementById("pdfFile");

// Get the text element where we show the selected filename
const fileName = document.getElementById("fileName");

// Get the Generate TXT button
const generateButton = document.getElementById("generateBtn");


// This runs whenever the user selects a file
pdfFile.addEventListener("change", function () {

    // Get the first selected file
    const file = pdfFile.files[0];

    // If a file was selected, show its name
    if (file) {
        fileName.textContent = file.name;
    } 
    else {
        fileName.textContent = "No file selected";
    }
});


// This runs when the user clicks "Generate TXT"
generateButton.addEventListener("click", async function () {

    // Get the selected PDF
    const file = pdfFile.files[0];

    // Check whether the user selected a file
    if (!file) {
        alert("Please select a PDF first.");
        return;
    }


    // FormData allows us to send a file to the backend
    const formData = new FormData();

    // Add our PDF to the FormData
    // "pdf" must match request.files["pdf"] in Python
    formData.append("pdf", file);


    try {

        // Send the PDF to our Flask backend
        const response = await fetch("http://127.0.0.1:5000/upload", {
            method: "POST",
            body: formData
        });


        // Convert Flask's response from JSON into JavaScript
        const data = await response.json();


        // Display the extracted PDF text on the webpage
        output.textContent = data.text;

        alert("PDF processed successfully! Check the browser console.");

    } 
    catch (error) {

        // This runs if something goes wrong
        console.error("Error:", error);

        alert("Something went wrong while processing the PDF.");
    }

});