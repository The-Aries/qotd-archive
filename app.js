"use strict";
const state = {records: [], topic: "all", search: ""};
const get = (id) => document.getElementById(id);
function element(tag, klass, content) {
  const el = document.createElement(tag);
  if (klass) el.className = klass;
  if (content !== undefined && content !== null) el.textContent = String(content);
  return el;
}
function valid(r) {
  return r && typeof r.id === "string" && /^\d{4}-\d{2}-\d{2}$/.test(r.date) &&
    typeof r.question === "string" && typeof r.category === "string" &&
    Array.isArray(r.options) && r.options.every((o) => typeof o.text === "string" &&
    (o.votes === null || (Number.isInteger(o.votes) && o.votes >= 0)));
}
function card(r) {
  const article = element("article", "question");
  article.id = r.id;
  const main = element("div", "question-main");
  const meta = element("div", "meta");
  const date = element("time", "", r.date);
  date.dateTime = r.date;
  meta.append(element("span", "pill", r.category), date);
  if (r.anonymous) meta.append(element("span", "", "Anonymous voting"));
  main.append(meta, element("h3", "", r.question));
  if (r.description) main.append(element("p", "description", r.description));
  article.append(main);
  if (r.options.length === 0) return article;
  const details = element("details", "detail");
  const verified = r.options.length > 0 && r.options.every((o) => Number.isInteger(o.votes));
  details.append(element("summary", "", verified ? "View verified results" : "View answer choices"));
  const list = element("ol", "options");
  const max = verified ? Math.max(1, ...r.options.map((o) => o.votes)) : 1;
  for (const o of r.options) {
    const item = element("li", "option");
    const body = element("div", "option-body");
    body.append(element("div", "", o.text));
    if (verified) {
      const bar = element("div", "bar");
      const fill = element("span");
      fill.style.width = String(100 * o.votes / max) + "%";
      bar.append(fill);
      body.append(bar);
    }
    item.append(body, element("span", "votes", verified ? o.votes + " votes" : "Pending verification"));
    list.append(item);
  }
  details.append(list, element("p", "footnote", verified
    ? "Aggregated votes only. Multiple-choice vote totals can exceed participant counts."
    : "No unverified counts or percentages are displayed."));
  article.append(details);
  return article;
}
function render() {
  const term = state.search.trim().toLocaleLowerCase();
  const records = state.records.filter((r) =>
    (state.topic === "all" || r.category === state.topic) &&
    [r.question, r.description || "", ...r.options.map((o) => o.text)].join(" ").toLocaleLowerCase().includes(term));
  get("questions").replaceChildren(...records.map(card));
  get("empty").hidden = records.length !== 0;
  get("result-count").textContent = records.length + " shown";
}
async function start() {
  try {
    const response = await fetch("./data/qotd.json", {cache: "no-store"});
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    if (!Array.isArray(data.questions) || !data.questions.every(valid)) throw new Error("Invalid data");
    state.records = data.questions.sort((a,b) => b.date.localeCompare(a.date));
    const topics = [...new Set(state.records.map((r) => r.category))].sort();
    get("published-count").textContent = state.records.length;
    get("poll-count").textContent = data.meta.identifiedGroupPollMessages ?? "—";
    get("topic-count").textContent = topics.length;
    get("coverage-note").textContent = data.meta.coverageNote;
    for (const topic of topics) {
      const option = element("option", "", topic);
      option.value = topic;
      get("topic-select").append(option);
    }
    render();
  } catch (error) {
    get("load-error").hidden = false;
    get("result-count").textContent = "Archive unavailable";
    console.error(error);
  }
}
get("search").addEventListener("input", (event) => {state.search = event.target.value; render()});
get("topic-select").addEventListener("change", (event) => {state.topic = event.target.value; render()});
start();

