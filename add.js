"use strict";

const REPOSITORY = "https://github.com/The-Aries/question-of-the-day-in-ebs";
const grid = document.getElementById("option-grid");
const error = document.getElementById("form-error");

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
  const url = new URL(REPOSITORY + "/issues/new");
  url.searchParams.set("template", "qotd.yml");
  const question = document.getElementById("question").value.trim();
  if (!question) throw new Error("Enter the question.");
  const options = optionsToLines();
  const participants = document.getElementById("participants").value;
  url.searchParams.set("title", "[QOTD] " + question.slice(0, 90));
  url.searchParams.set("date", document.getElementById("date").value);
  url.searchParams.set("question", question);
  if (options) url.searchParams.set("choices", options);
  if (participants) url.searchParams.set("participants", participants);
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
