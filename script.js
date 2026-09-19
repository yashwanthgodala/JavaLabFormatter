const pdfFile = document.getElementById("pdfFile");
const fileName = document.getElementById("fileName");
const generateButton = document.getElementById("generateBtn");


pdfFile.addEventListener("change", function () {

    const file = pdfFile.files[0];

    if (file) {
        fileName.textContent = file.name;
    } else {
        fileName.textContent = "No file selected";
    }

});


generateButton.addEventListener("click", function () {

    const file = pdfFile.files[0];

    if (!file) {
        alert("Please select a PDF first.");
        return;
    }

    alert("PDF selected: " + file.name);

});