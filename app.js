"use strict";
const state = {
  records: [], mode: "all", search: "", from: "", to: "",
  minDate: "", maxDate: ""
};
const get = (id) => document.getElementById(id);

function element(tag, className = "", value = null) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== null && value !== undefined) node.textContent = String(value);
  return node;
}

// Presentation only: retain original text in entries for review and search.
function questionTitle(value) {
  let text = value.replace(/[\u2028\u2029]/g, "\n").trim();
  text = text.replace(/^[\s*_]+/, "");
  text = text.replace(/^nice weather for a\s+question of the day!\s*/i, "");
  text = text.replace(/^(?:meta\s+)?question of the (?:day|night)(?=\b|[A-Z])/i, "");
  text = text.replace(/^(speaking of EBS traditions\.)\s+question of the day\s*:/i, "$1");
  text = text.replace(/^[\s*:_!.,\uFE0F\uFE0E\u2013\u2014-]+/, "");
  text = text.replace(/\p{Extended_Pictographic}/gu, "");
  text = text.replace(/[\u200D\uFE0E\uFE0F]/g, "");
  text = text.replace(/\s*\n\s*/g, " ").replace(/\s{2,}/g, " ").trim();
  return text.replace(/\*+$/g, "").trim() || value;
}

function labelForMode(entry) {
  if (entry.multipleChoice === true) return "Multiple choice";
  if (entry.multipleChoice === false) return "Single choice";
  return null;
}

function votesLabel(count) {
  return Number.isInteger(count) ? String(count) + " votes" : "Votes unknown";
}

function meta(entry, followupCount = 0) {
  const line = element("div", "meta");
  const dt = element("time", "", entry.date + (entry.time ? " · " + entry.time : ""));
  dt.dateTime = entry.date + (entry.time ? "T" + entry.time : "");
  line.append(dt);
  const choiceMode = entry.options.length ? labelForMode(entry) : null;
  if (choiceMode) line.append(element("span", "", choiceMode));
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
    body.append(element("div", "", item.text.replace(/\p{Extended_Pictographic}/gu, "").trim()));
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
  return container;
}

function card(entry) {
  const card = element("details", "question");
  card.id = entry.id;
  card.name = "qotd";
  card.addEventListener("toggle", () => {
    if (card.open) {
      for (const other of document.querySelectorAll("details.question[open]")) {
        if (other !== card) other.open = false;
      }
      selectQuestion(card.id);
    }
  });
  const summary = element("summary", "question-summary");
  const heading = element("span", "question-title", questionTitle(entry.question));
  const small = meta(entry, entry.followups.length);
  summary.append(heading, small);
  card.append(summary);
  const interior = element("div", "question-expanded");
  interior.append(optionsView(entry));
  for (let index = 0; index < entry.followups.length; index++) {
    const child = entry.followups[index];
    const section = element("section", "followup");
    section.append(element("h3", "", "Follow-up " + (index + 1) + ": " + questionTitle(child.question)));
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
    (entry.multipleChoice === null || typeof entry.multipleChoice === "boolean") &&
    (entry.participants === null || (Number.isInteger(entry.participants) && entry.participants >= 0)) &&
    Array.isArray(entry.options) &&
    entry.options.every(o => typeof o.text === "string" &&
      (o.votes === null || (Number.isInteger(o.votes) && o.votes >= 0))) &&
    (!hasFollowups || (Array.isArray(entry.followups) &&
      entry.followups.every(x => validEntry(x, false))));
}

function matches(entry) {
  if (state.from && entry.date < state.from) return false;
  if (state.to && entry.date > state.to) return false;
  if (state.mode !== "all") {
    const mode = entry.options.length === 0 ? "open" :
      entry.multipleChoice === true ? "multiple" :
      entry.multipleChoice === false ? "single" : "unknown";
    if (mode !== state.mode) return false;
  }
  const haystack = [entry.question,
    ...entry.options.map(o => o.text),
    ...entry.followups.flatMap(f => [f.question, ...f.options.map(o => o.text)])
  ].join(" ").toLocaleLowerCase();
  return haystack.includes(state.search.trim().toLocaleLowerCase());
}

function renderNavigation(filtered) {
  const items = [];
  let currentMonth = "";
  for (const entry of filtered) {
    const month = new Intl.DateTimeFormat("en", {
      year: "numeric", month: "long", timeZone: "UTC"
    }).format(new Date(entry.date + "T12:00:00Z"));
    if (month !== currentMonth) {
      currentMonth = month;
      items.push(element("div", "quick-month", month));
    }
    const link = element("a", "quick-link");
    link.href = "#" + entry.id;
    link.title = questionTitle(entry.question);
    link.append(element("span", "quick-date", entry.date));
    link.append(element("span", "quick-label", questionTitle(entry.question)));
    link.addEventListener("click", event => {
      event.preventDefault();
      const target = document.getElementById(entry.id);
      if (target) {
        target.open = true;
        selectQuestion(entry.id);
        // An explicit jump avoids smooth-scroll and collapsing-card races.
        target.scrollIntoView({behavior: "instant", block: "start"});
        history.replaceState(null, "", "#" + entry.id);
      }
      syncNavigationScroll();
    });
    items.push(link);
  }
  get("quick-links").replaceChildren(...items);
  get("quick-empty").hidden = filtered.length > 0;
}

function firstVisibleQuestionId() {
  const cards = document.querySelectorAll("details.question");
  const cutoff = get("site-header").getBoundingClientRect().bottom + 20;
  for (const card of cards) {
    if (card.getBoundingClientRect().bottom > cutoff) return card.id;
  }
  return cards.length ? cards[cards.length - 1].id : null;
}

let selectedQuestionId = null;
function selectQuestion(id) {
  selectedQuestionId = id;
  const links = get("quick-links");
  for (const link of links.querySelectorAll(".quick-link")) {
    const active = link.getAttribute("href") === "#" + selectedQuestionId;
    link.classList.toggle("is-active", active);
    if (active) {
      link.setAttribute("aria-current", "location");
    }
    else link.removeAttribute("aria-current");
  }
}

let visibleNavigationId = null;
function syncNavigationScroll() {
  // Scrolling the main page moves the sidebar only. It does not change
  // which question the user explicitly selected.
  const visibleId = firstVisibleQuestionId();
  if (visibleId === visibleNavigationId) return;
  visibleNavigationId = visibleId;
  const links = get("quick-links");
  const visibleLink = [...links.querySelectorAll(".quick-link")].find(
    link => link.getAttribute("href") === "#" + visibleId
  );
  if (visibleLink) {
    const container = links.getBoundingClientRect();
    const item = visibleLink.getBoundingClientRect();
    // Keep the current main question near the top of the sidebar as both move.
    // Only scroll this list: moving the viewport must not change the highlight.
    const offset = item.top - container.top - 12;
    if (Math.abs(offset) > 7) links.scrollTop += offset;
  }
}

function render() {
  visibleNavigationId = null;
  const filtered = state.records.filter(matches);
  if (!filtered.some(entry => entry.id === selectedQuestionId)) {
    selectedQuestionId = filtered[0]?.id || null;
  }
  get("questions").replaceChildren(...filtered.map(card));
  renderNavigation(filtered);
  selectQuestion(selectedQuestionId);
  syncNavigationScroll();
  get("empty").hidden = filtered.length !== 0;
  get("result-count").textContent = filtered.length + " shown";
}

function syncHeaderHeight() {
  const height = get("site-header").getBoundingClientRect().height;
  document.documentElement.style.setProperty("--header-height", height + "px");
}

function onPageScroll() {
  // The small static archive can update immediately, including in background tabs.
  syncNavigationScroll();
}

async function start() {
  try {
    const response = await fetch("./data/qotd.json", {cache: "no-store"});
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    if (!Array.isArray(data.questions) || !data.questions.every(q => validEntry(q, true)))
      throw new Error("Invalid archive data");
    state.records = data.questions;
    state.minDate = state.records.reduce(
      (min, entry) => entry.date < min ? entry.date : min,
      state.records[0]?.date || ""
    );
    syncDateLimits();
    get("poll-count").textContent = data.meta.pollCount ?? "—";
    render();
    syncHeaderHeight();
    onPageScroll();
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

window.addEventListener("scroll", onPageScroll, {passive:true});
window.addEventListener("resize", () => {
  syncHeaderHeight();
  onPageScroll();
});
if (typeof ResizeObserver !== "undefined") {
  new ResizeObserver(syncHeaderHeight).observe(get("site-header"));
}
syncHeaderHeight();

get("search").addEventListener("input", e => {state.search = e.target.value; render();});
get("mode-select").addEventListener("change", e => {state.mode = e.target.value; render();});

function isoDateOrNull(value) {
  if (!value) return "";
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const date = new Date(value + "T00:00:00Z");
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value
    ? value : null;
}

function todayInBerlin() {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit"
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return values.year + "-" + values.month + "-" + values.day;
}

function syncDateLimits() {
  state.maxDate = todayInBerlin();
  for (const field of ["from", "to"]) {
    const picker = get("date-" + field + "-picker");
    picker.min = state.minDate;
    picker.max = state.maxDate;
    get("date-" + field).title =
      "Available dates: " + state.minDate + " to " + state.maxDate;
  }
}

function bindDateFilter(field) {
  const text = get("date-" + field);
  const picker = get("date-" + field + "-picker");
  const update = (finalize = false) => {
    syncDateLimits();
    let value = isoDateOrNull(text.value.trim());
    if (finalize) {
      if (value === null) value = "";
      if (value && state.minDate && value < state.minDate) value = state.minDate;
      if (value && value > state.maxDate) value = state.maxDate;
      text.value = value;
    }
    const allowed = value !== null && (
      !value || ((!state.minDate || value >= state.minDate) && value <= state.maxDate)
    );
    text.setAttribute("aria-invalid", String(!allowed));
    state[field] = allowed ? value : "";
    picker.value = allowed ? value : "";
    render();
  };
  text.addEventListener("input", () => update());
  text.addEventListener("change", () => update(true));
  text.addEventListener("blur", () => update(true));
  picker.addEventListener("change", () => {
    text.value = picker.value;
    update(true);
  });
  get("date-" + field + "-calendar").addEventListener("click", () => {
    syncDateLimits();
    if (typeof picker.showPicker === "function") picker.showPicker();
    else { picker.focus(); picker.click(); }
  });
}

bindDateFilter("from");
bindDateFilter("to");
start();
