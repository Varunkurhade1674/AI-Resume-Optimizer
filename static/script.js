// ---------------------------------------------------------------------------
// AI Resume Optimizer & ATS Analyzer - frontend logic
// Handles: file selection/drag-drop, form submission, rendering results,
// copy-to-clipboard, and markdown report download.
// ---------------------------------------------------------------------------

const form = document.getElementById("analyze-form");
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("resume_file");
const fileNameEl = document.getElementById("file-name");
const analyzeBtn = document.getElementById("analyze-btn");
const btnText = document.getElementById("btn-text");
const btnSpinner = document.getElementById("btn-spinner");
const errorMessage = document.getElementById("error-message");

const emptyState = document.getElementById("empty-state");
const resultsContent = document.getElementById("results-content");
const resultsActions = document.getElementById("results-actions");

const copyBtn = document.getElementById("copy-btn");
const downloadBtn = document.getElementById("download-btn");

let lastReportUrl = null;
let lastResultText = "";

// ---------- Drag & drop / click-to-upload ----------
dropzone.addEventListener("click", () => fileInput.click());

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length) {
    fileInput.files = e.dataTransfer.files;
    updateFileName();
  }
});

fileInput.addEventListener("change", updateFileName);

function updateFileName() {
  if (fileInput.files.length) {
    fileNameEl.textContent = `Selected: ${fileInput.files[0].name}`;
  } else {
    fileNameEl.textContent = "";
  }
}

// ---------- Form submission ----------
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();

  if (!fileInput.files.length) {
    showError("Please upload a resume file (PDF or DOCX).");
    return;
  }

  const jobDescription = document.getElementById("job_description").value.trim();
  if (!jobDescription) {
    showError("Please paste a job description.");
    return;
  }

  const formData = new FormData();
  formData.append("resume_file", fileInput.files[0]);
  formData.append("job_description", jobDescription);
  formData.append(
    "candidate_name",
    document.getElementById("candidate_name").value.trim() || "Guest"
  );

  setLoading(true);

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong while analyzing the resume.");
    }

    renderResults(data);
  } catch (err) {
    showError(err.message || "Failed to analyze resume. Please try again.");
  } finally {
    setLoading(false);
  }
});

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  btnText.textContent = isLoading ? "Analyzing..." : "Analyze Resume";
  btnSpinner.classList.toggle("hidden", !isLoading);
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.classList.remove("hidden");
}

function hideError() {
  errorMessage.classList.add("hidden");
  errorMessage.textContent = "";
}

// ---------- Rendering ----------
function renderResults(data) {
  emptyState.classList.add("hidden");
  resultsContent.classList.remove("hidden");
  resultsActions.classList.remove("hidden");

  // ATS Score
  const scoreValue = document.getElementById("score-value");
  const scoreCircle = document.getElementById("score-circle");
  const scoreLabel = document.getElementById("score-label");
  scoreValue.textContent = `${data.ats_score}`;
  scoreLabel.textContent = scoreDescription(data.ats_score);
  scoreCircle.style.borderColor = scoreColor(data.ats_score);
  scoreValue.style.color = scoreColor(data.ats_score);

  // Summary
  document.getElementById("summary-text").textContent = data.summary || "No summary generated.";

  // Skills
  renderChips("matching-skills", data.matching_skills, "match");
  renderChips("missing-skills", data.missing_skills, "missing");

  // Suggestions
  const suggestionsList = document.getElementById("suggestions-list");
  suggestionsList.innerHTML = "";
  (data.suggestions || []).forEach((s) => {
    const li = document.createElement("li");
    li.textContent = s;
    suggestionsList.appendChild(li);
  });

  // Optimized summary
  document.getElementById("optimized-summary-text").textContent =
    data.optimized_summary || "No optimized summary generated.";

  // Cover letter
  document.getElementById("cover-letter-text").textContent =
    data.cover_letter || "No cover letter generated.";

  // Interview questions
  const questionsList = document.getElementById("interview-questions-list");
  questionsList.innerHTML = "";
  (data.interview_questions || []).forEach((q) => {
    const li = document.createElement("li");
    li.textContent = q;
    questionsList.appendChild(li);
  });

  lastReportUrl = data.report_url;
  lastResultText = buildPlainTextReport(data);
}

function renderChips(containerId, items, type) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  if (!items || !items.length) {
    const span = document.createElement("span");
    span.className = "score-label";
    span.textContent = "None found";
    container.appendChild(span);
    return;
  }
  items.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = `chip ${type}`;
    chip.textContent = item;
    container.appendChild(chip);
  });
}

function scoreDescription(score) {
  if (score >= 80) return "Excellent match for this role";
  if (score >= 60) return "Good match, some gaps to close";
  if (score >= 40) return "Moderate match, needs improvement";
  return "Weak match, significant revision recommended";
}

function scoreColor(score) {
  if (score >= 80) return "#16a34a";
  if (score >= 60) return "#2563eb";
  if (score >= 40) return "#d97706";
  return "#dc2626";
}

function buildPlainTextReport(data) {
  return [
    `ATS SCORE: ${data.ats_score}/100`,
    "",
    "RESUME SUMMARY:",
    data.summary,
    "",
    "MATCHING SKILLS:",
    (data.matching_skills || []).join(", "),
    "",
    "MISSING SKILLS:",
    (data.missing_skills || []).join(", "),
    "",
    "IMPROVEMENT SUGGESTIONS:",
    ...(data.suggestions || []).map((s) => `- ${s}`),
    "",
    "OPTIMIZED PROFESSIONAL SUMMARY:",
    data.optimized_summary,
    "",
    "COVER LETTER:",
    data.cover_letter,
    "",
    "INTERVIEW QUESTIONS:",
    ...(data.interview_questions || []).map((q, i) => `${i + 1}. ${q}`),
  ].join("\n");
}

// ---------- Copy & Download ----------
copyBtn.addEventListener("click", async () => {
  if (!lastResultText) return;
  try {
    await navigator.clipboard.writeText(lastResultText);
    copyBtn.textContent = "✅ Copied!";
    setTimeout(() => (copyBtn.textContent = "📋 Copy Results"), 2000);
  } catch (err) {
    showError("Could not copy to clipboard.");
  }
});

downloadBtn.addEventListener("click", () => {
  if (!lastReportUrl) return;
  window.location.href = lastReportUrl;
});
