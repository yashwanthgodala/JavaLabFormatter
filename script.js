const generateButton = document.getElementById("generateBtn");

generateButton.addEventListener("click", function () {

    const file = document.getElementById("pdfFile").files[0];

    if (!file) {
        alert("Please select a PDF first.");
        return;
    }

    alert("PDF selected successfully!");
});