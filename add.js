"use strict";

const REPOSITORY = "https://github.com/The-Aries/question-of-the-day-in-ebs";
const grid = document.getElementById("option-grid");
const error = document.getElementById("form-error");
const editId = new URLSearchParams(window.location.search).get("edit");
let originalQuestion = null;
let editingLoaded = !editId;

function addOption(text = "", votes = "") {
  if (grid.children.length >= 50) return;
  const row = document.createElement("div");
  row.className = "option-row";
  const number = grid.children.length + 1;
  const choiceLabel = document.createElement("label");
  choiceLabel.textContent = "Option " + number;
  const choice = document.createElement("input");
  choice.type = "text";
  choice.className = "choice-text";
  choice.maxLength = 400;
  choice.placeholder = "Answer text";
  choice.value = text;
  choiceLabel.append(choice);
  const voteLabel = document.createElement("label");
  voteLabel.textContent = "Votes";
  const vote = document.createElement("input");
  vote.type = "number";
  vote.className = "choice-votes";
  vote.min = "0";
  vote.max = "1000000";
  vote.step = "1";
  vote.placeholder = "—";
  vote.value = votes;
  voteLabel.append(vote);
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "remove-option";
  remove.textContent = "×";
  remove.setAttribute("aria-label", "Remove option " + number);
  remove.addEventListener("click", () => {
    row.remove();
    [...grid.children].forEach((item, i) => {
      item.querySelector("label").firstChild.textContent = "Option " + (i + 1);
      item.querySelector(".remove-option").setAttribute("aria-label", "Remove option " + (i + 1));
    });
  });
  row.append(choiceLabel, voteLabel, remove);
  grid.append(row);
  return choice;
}

function optionsToLines() {
  const lines = [];
  const seen = new Set();
  for (const row of grid.children) {
    const choice = row.querySelector(".choice-text").value.trim();
    const raw = row.querySelector(".choice-votes").value.trim();
    if (!choice) {
      if (raw !== "") throw new Error("An option has a vote count but no answer text.");
      continue;
    }
    if (raw && (!/^\d+$/.test(raw) || Number(raw) > 1000000)) {
      throw new Error("Votes must be whole numbers from 0 to 1,000,000.");
    }
    if (seen.has(choice.toLowerCase())) throw new Error("Each answer option must be unique.");
    seen.add(choice.toLowerCase());
    lines.push(choice + " | " + (raw === "" ? "?" : raw));
  }
  return lines.join("\n");
}

function submissionUrl() {
  if (!editingLoaded) throw new Error("The selected question has not loaded.");
  const url = new URL(REPOSITORY + "/issues/new");
  url.searchParams.set("template", editId ? "edit.yml" : "qotd.yml");
  const question = document.getElementById("question").value.trim();
  if (!question) throw new Error("Enter the question.");
  const options = optionsToLines();
  url.searchParams.set("title", (editId ? "[Edit] " : "[QOTD] ") + question.slice(0, 90));
  if (editId) {
    url.searchParams.set("entry-id", editId);
    url.searchParams.set("current-question", originalQuestion);
    const reason = document.getElementById("edit-reason").value.trim();
    if (reason) url.searchParams.set("reason", reason);
  }
  url.searchParams.set("date", document.getElementById("date").value);
  url.searchParams.set("question", question);
  if (options) url.searchParams.set("choices", options);
  url.searchParams.set("voting", document.getElementById("voting").value);
  url.searchParams.set("anonymous", document.getElementById("anonymous").value);
  const time = document.getElementById("time").value;
  if (time) url.searchParams.set("time", time);
  if (url.toString().length > 7000) {
    throw new Error("This submission is too large for a prefilled URL. Use the original GitHub form.");
  }
  return url.toString();
}

const todayParts = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit"
}).formatToParts(new Date());
const today = Object.fromEntries(todayParts.map(part => [part.type, part.value]));
document.getElementById("date").max =
  today.year + "-" + today.month + "-" + today.day;
document.getElementById("add-option").addEventListener("click", () => {
  const input = addOption();
  if (input) input.focus();
});
addOption();
addOption();
if (editId) {
  document.getElementById("form-title").textContent = "Edit question";
  document.title = "Edit question — Question of the Day in EBS";
  document.getElementById("form-intro").textContent =
    "Review the existing question and votes, correct anything necessary, then submit the proposed change for approval on GitHub.";
  document.getElementById("edit-reason-field").hidden = false;
  document.getElementById("original-form-link").hidden = true;
  document.getElementById("continue-button").disabled = true;
  fetch("./data/qotd.json", {cache: "no-store"})
    .then(response => {
      if (!response.ok) throw new Error("Could not load archive data.");
      return response.json();
    })
    .then(data => {
      const record = data.questions?.find(entry => entry.id === editId);
      if (!record) throw new Error("This question does not exist. Refresh the archive.");
      originalQuestion = record.question;
      document.getElementById("date").value = record.date;
      document.getElementById("time").value = record.time || "";
      document.getElementById("question").value = record.question;
      document.getElementById("voting").value = record.multipleChoice === true ? "Yes" : "No";
      document.getElementById("anonymous").value = record.anonymous === true ? "Yes" : "No";
      grid.replaceChildren();
      for (const option of record.options) {
        addOption(option.text, option.votes === null ? "" : String(option.votes));
      }
      if (!record.options.length) addOption();
      editingLoaded = true;
      document.getElementById("continue-button").disabled = false;
    })
    .catch(reason => {
      error.textContent = reason.message;
      error.hidden = false;
    });
}
document.getElementById("question-form").addEventListener("submit", event => {
  event.preventDefault();
  error.hidden = true;
  if (!event.currentTarget.reportValidity()) return;
  try {
    window.location.assign(submissionUrl());
  } catch (reason) {
    error.textContent = reason.message;
    error.hidden = false;
  }
});
