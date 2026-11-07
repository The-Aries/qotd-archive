"use strict";
const state = {records: [], topic: "all", mode: "all", search: "", from: "", to: ""};
const get = (id) => document.getElementById(id);

function element(tag, className = "", value = null) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== null && value !== undefined) node.textContent = String(value);
  return node;
}

function labelForMode(entry) {
  if (entry.options.length === 0) return "Text question";
  if (entry.multipleChoice === true) return "Multiple choice";
  if (entry.multipleChoice === false) return "Single choice";
  return "Choice type unknown";
}

function votesLabel(count) {
  return Number.isInteger(count) ? String(count) + " votes" : "Votes unknown";
}

function meta(entry, followupCount = 0) {
  const line = element("div", "meta");
  const dt = element("time", "", entry.date + (entry.time ? " · " + entry.time : ""));
  dt.dateTime = entry.date + (entry.time ? "T" + entry.time : "");
  line.append(dt);
  line.append(element("span", "", "Participants: " +
    (entry.participants === null ? "unknown" : entry.participants)));
  line.append(element("span", "", labelForMode(entry)));
  if (followupCount > 0) line.append(element("span", "", followupCount + " follow-up" +
    (followupCount === 1 ? "" : "s")));
  return line;
}

function optionsView(entry) {
  const container = element("div", "results");
  if (!entry.options.length) {
    container.append(element("p", "description", "Open-ended question; no poll options."));
    return container;
  }
  const list = element("ol", "options");
  const available = entry.options.map(o => o.votes).filter(Number.isInteger);
  const max = Math.max(1, ...available);
  for (const item of entry.options) {
    const row = element("li", "option");
    const body = element("div", "option-body");
    body.append(element("div", "", item.text));
    if (Number.isInteger(item.votes)) {
      const bar = element("div", "bar");
      const fill = element("span");
      fill.style.width = Math.round(item.votes * 100 / max) + "%";
      bar.append(fill);
      body.append(bar);
    }
    row.append(body, element("span", "votes", votesLabel(item.votes)));
    list.append(row);
  }
  container.append(list);
  if (entry.notes) container.append(element("p", "footnote", entry.notes));
  if (entry.participationSource === "single-choice-total") {
    container.append(element("p", "footnote",
      "Participant count inferred from total votes in a single-choice poll."));
  } else if (entry.multipleChoice === true) {
    container.append(element("p", "footnote",
      "Multiple selections allowed; option vote totals are not unique participants."));
  }
  return container;
}

function card(entry) {
  const card = element("details", "question");
  card.id = entry.id;
  const summary = element("summary", "question-summary");
  const heading = element("span", "question-title", entry.question);
  const small = meta(entry, entry.followups.length);
  summary.append(heading, small);
  card.append(summary);
  const interior = element("div", "question-expanded");
  interior.append(optionsView(entry));
  const identity = element("div", "topic-id");
  const code = element("code", "", entry.id);
  const copy = element("button", "copy-id", "Copy topic ID");
  copy.type = "button";
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(entry.id);
      copy.textContent = "Copied";
    } catch {
      copy.textContent = "Select the ID to copy";
    }
  });
  identity.append(element("span", "", "Topic ID: "), code, copy);
  interior.append(identity);
  for (let index = 0; index < entry.followups.length; index++) {
    const child = entry.followups[index];
    const section = element("section", "followup");
    section.append(element("h3", "", "Follow-up " + (index + 1) + ": " + child.question));
    section.append(meta(child), optionsView(child));
    interior.append(section);
  }
  card.append(interior);
  return card;
}

function validEntry(entry, hasFollowups = false) {
  return entry && typeof entry.id === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(entry.date) &&
    typeof entry.question === "string" &&
    typeof entry.category === "string" &&
    (entry.multipleChoice === null || typeof entry.multipleChoice === "boolean") &&
    (entry.participants === null || (Number.isInteger(entry.participants) && entry.participants >= 0)) &&
    Array.isArray(entry.options) &&
    entry.options.every(o => typeof o.text === "string" &&
      (o.votes === null || (Number.isInteger(o.votes) && o.votes >= 0))) &&
    (!hasFollowups || (Array.isArray(entry.followups) &&
      entry.followups.every(x => validEntry(x, false))));
}

function matches(entry) {
  if (state.topic !== "all" && entry.category !== state.topic) return false;
  if (state.from && entry.date < state.from) return false;
  if (state.to && entry.date > state.to) return false;
  if (state.mode !== "all") {
    const mode = entry.options.length === 0 ? "open" :
      entry.multipleChoice === true ? "multiple" :
      entry.multipleChoice === false ? "single" : "unknown";
    if (mode !== state.mode) return false;
  }
  const haystack = [entry.question, entry.category,
    ...entry.options.map(o => o.text),
    ...entry.followups.flatMap(f => [f.question, ...f.options.map(o => o.text)])
  ].join(" ").toLocaleLowerCase();
  return haystack.includes(state.search.trim().toLocaleLowerCase());
}

function render() {
  const filtered = state.records.filter(matches);
  get("questions").replaceChildren(...filtered.map(card));
  get("empty").hidden = filtered.length !== 0;
  get("result-count").textContent = filtered.length + " shown";
}

async function start() {
  try {
    const response = await fetch("./data/qotd.json", {cache: "no-store"});
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    if (!Array.isArray(data.questions) || !data.questions.every(q => validEntry(q, true)))
      throw new Error("Invalid archive data");
    state.records = data.questions;
    const topics = [...new Set(state.records.map(r => r.category))].sort();
    get("published-count").textContent = state.records.length;
    get("poll-count").textContent = data.meta.pollCount ?? "—";
    get("topic-count").textContent = topics.length;
    get("coverage-note").textContent = data.meta.coverageNote || "";
    for (const topic of topics) {
      const option = element("option", "", topic);
      option.value = topic;
      get("topic-select").append(option);
    }
    render();
    if (window.location.hash) {
      const selected = document.getElementById(window.location.hash.slice(1));
      if (selected && selected.tagName === "DETAILS") {
        selected.open = true;
        selected.scrollIntoView({block: "start"});
      }
    }
  } catch (error) {
    get("load-error").hidden = false;
    get("result-count").textContent = "Archive unavailable";
    console.error(error);
  }
}

get("search").addEventListener("input", e => {state.search = e.target.value; render();});
get("topic-select").addEventListener("change", e => {state.topic = e.target.value; render();});
get("mode-select").addEventListener("change", e => {state.mode = e.target.value; render();});
get("date-from").addEventListener("change", e => {state.from = e.target.value; render();});
get("date-to").addEventListener("change", e => {state.to = e.target.value; render();});
start();
