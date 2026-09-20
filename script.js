const output = document.getElementById("output");
const pdfFile = document.getElementById("pdfFile");
const fileName = document.getElementById("fileName");
const generateButton = document.getElementById("generateBtn");
const downloadButton = document.getElementById("downloadBtn");
const outputFile = document.getElementById("outputFile");
const outputCaption = document.getElementById("outputCaption");
const previewPanel = document.getElementById("previewPanel");
const closePreview = document.getElementById("closePreview");
const previewBackdrop = document.getElementById("previewBackdrop");
const modalDownload = document.getElementById("modalDownload");
const resetButton = document.getElementById("resetBtn");
const inputStation = document.getElementById("inputStation");
const machine = document.getElementById("machine");
const statusLight = document.getElementById("statusLight");
const statusTitle = document.getElementById("statusTitle");
const progressBar = document.getElementById("progressBar");
const hint = document.getElementById("hint");
const steps = [1, 2, 3, 4].map((index) =>
  document.getElementById(`step${index}`)
);

let generatedText = "";
let generatedBlobUrl = null;
let processing = false;

function setMachineState(state, message = "") {
  statusLight.className = "status-light";
  machine.classList.remove("processing");

  if (state === "processing") {
    statusLight.classList.add("processing");
    machine.classList.add("processing");
    statusTitle.textContent = message || "PROCESSING...";
    return;
  }

  if (state === "success") {
    statusLight.classList.add("success");
    statusTitle.textContent = "DONE";
    return;
  }

  if (state === "error") {
    statusLight.classList.add("error");
    statusTitle.textContent = "ERROR";
    return;
  }

  statusTitle.textContent = "READY";
}

function updateSteps(active = -1, done = 0, failed = -1) {
  steps.forEach((step, index) => {
    const label = step.textContent.replace(/^[○✓✕●]\s*/, "");

    step.className = "";

    if (index < done) {
      step.classList.add("done");
      step.textContent = `✓ ${label}`;
      return;
    }

    if (index === failed) {
      step.classList.add("failed");
      step.textContent = `✕ ${label}`;
      return;
    }

    if (index === active) {
      step.classList.add("active");
      step.textContent = `● ${label}`;
      return;
    }

    step.textContent = `○ ${label}`;
  });
}

function resetMachine() {
  setMachineState("idle");
  progressBar.style.width = "0%";
  updateSteps();
}

function clearGenerated() {
  generatedText = "";

  if (generatedBlobUrl) {
    URL.revokeObjectURL(generatedBlobUrl);
    generatedBlobUrl = null;
  }

  output.textContent = "";
  outputFile.disabled = true;
  downloadButton.disabled = true;
  outputCaption.textContent = "Your finished file will appear here";
}

function setSelectedFile(file) {
  clearGenerated();
  resetMachine();

  if (!file) {
    fileName.textContent = "No file selected";
    generateButton.disabled = true;
    hint.textContent = "Select a PDF to activate the machine.";
    return;
  }

  const isPdf =
    file.type === "application/pdf" ||
    file.name.toLowerCase().endsWith(".pdf");

  if (!isPdf) {
    pdfFile.value = "";
    fileName.textContent = "No file selected";
    generateButton.disabled = true;
    setMachineState("error");
    hint.textContent = "Only PDF files can enter the tray.";
    return;
  }

  fileName.textContent = file.name;
  generateButton.disabled = false;
  hint.textContent =
    "Ready. Press START PROCESSING to run the machine.";
}

pdfFile.addEventListener("change", () => {
  setSelectedFile(pdfFile.files[0]);
});

inputStation.addEventListener("dragover", (event) => {
  event.preventDefault();
  inputStation.classList.add("dragover");
});

inputStation.addEventListener("dragleave", () => {
  inputStation.classList.remove("dragover");
});

inputStation.addEventListener("drop", (event) => {
  event.preventDefault();
  inputStation.classList.remove("dragover");

  const file = event.dataTransfer.files[0];
  const isPdf =
    file &&
    (file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf"));

  if (!isPdf) {
    setMachineState("error");
    hint.textContent = "Only PDF files can enter the tray.";
    return;
  }

  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  pdfFile.files = dataTransfer.files;
  pdfFile.dispatchEvent(new Event("change"));
});

async function runStep(index, done, progress, label) {
  setMachineState("processing", label);
  updateSteps(index, done);
  progressBar.style.width = `${progress}%`;

  await new Promise((resolve) => setTimeout(resolve, 450));
}

generateButton.addEventListener("click", async () => {
  if (processing) {
    return;
  }

  const file = pdfFile.files[0];

  if (!file) {
    hint.textContent = "Please select a PDF first.";
    return;
  }

  processing = true;
  generateButton.disabled = true;
  clearGenerated();
  hint.textContent = "The machine is working...";

  try {
    const formData = new FormData();
    formData.append("pdf", file);

    await runStep(0, 0, 12, "READING PDF...");
    await runStep(1, 1, 35, "ANALYZING CONTENT...");
    await runStep(2, 2, 65, "FORMATTING WITH AI...");

    const response = await fetch("http://127.0.0.1:5000/upload", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();

    if (!data.formatted_text) {
      throw new Error("No formatted text returned.");
    }

    await runStep(3, 3, 90, "GENERATING TXT...");

    generatedText = data.formatted_text;
    generatedBlobUrl = URL.createObjectURL(
      new Blob([generatedText], {
        type: "text/plain;charset=utf-8"
      })
    );

    progressBar.style.width = "100%";
    updateSteps(-1, 4);
    setMachineState("success");

    outputFile.disabled = false;
    downloadButton.disabled = false;
    outputCaption.textContent =
      "Click the TXT to preview · use the download button to save";
    hint.textContent =
      "Processing complete. Your TXT file is ready.";
  } catch (error) {
    console.error(error);

    setMachineState("error");
    progressBar.style.width = "0%";

    const activeIndex = steps.findIndex((step) =>
      step.classList.contains("active")
    );

    const failedIndex = activeIndex >= 0 ? activeIndex : 0;
    const completedCount = Math.max(0, failedIndex);

    updateSteps(-1, completedCount, failedIndex);

    hint.textContent =
      "Processing failed. Check that Flask and Gemini are running.";
    outputCaption.textContent = "No finished file was created.";
  } finally {
    processing = false;
    generateButton.disabled = !pdfFile.files[0];
  }
});

function downloadTxt() {
  if (!generatedBlobUrl) {
    return;
  }

  const link = document.createElement("a");
  link.href = generatedBlobUrl;
  link.download = "Java_Lab_Questions.txt";
  document.body.appendChild(link);
  link.click();
  link.remove();
}

function openPreview() {
  if (!generatedText) {
    return;
  }

  output.textContent = generatedText;
  previewPanel.hidden = false;
  document.body.classList.add("preview-open");
  closePreview.focus();
}

function hidePreview() {
  previewPanel.hidden = true;
  document.body.classList.remove("preview-open");
}

outputFile.addEventListener("click", openPreview);

downloadButton.addEventListener("click", (event) => {
  event.stopPropagation();
  downloadTxt();
});

modalDownload.addEventListener("click", downloadTxt);
closePreview.addEventListener("click", hidePreview);
previewBackdrop.addEventListener("click", hidePreview);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !previewPanel.hidden) {
    hidePreview();
  }
});

resetButton.addEventListener("click", () => {
  if (processing) {
    return;
  }

  pdfFile.value = "";
  fileName.textContent = "No file selected";
  generateButton.disabled = true;
  clearGenerated();
  resetMachine();
  hint.textContent = "Select a PDF to activate the machine.";
});

generateButton.disabled = true;
resetMachine();
