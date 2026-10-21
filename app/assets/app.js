"use strict";
const $ = (selector) => document.querySelector(selector);
const state = {data: null, page: 0, busy: false};
const pageSize = 15;
const labels = {
  "Marital status": "Estado civil", "Application mode": "Modalidad de ingreso",
  "Application order": "Orden de solicitud", "Course": "Carrera (código)",
  "Daytime/evening attendance": "Jornada", "Previous qualification": "Formación previa",
  "Previous qualification (grade)": "Nota previa", "Nacionality": "Nacionalidad (código)",
  "Mother's qualification": "Formación de la madre", "Father's qualification": "Formación del padre",
  "Mother's occupation": "Ocupación de la madre", "Father's occupation": "Ocupación del padre",
  "Admission grade": "Nota de admisión", "Displaced": "Desplazamiento",
  "Educational special needs": "Necesidades educativas especiales",
  "Gender": "Género (código)", "Age at enrollment": "Edad al matricularse",
  "International": "Estudiante internacional"
};
const classLabels = {Dropout: "Abandono", Enrolled: "Matriculado/a", Graduate: "Graduación"};
function icons() { if (window.lucide) lucide.createIcons(); }
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function icon(name) {
  const element = document.createElement("i");
  element.dataset.lucide = name;
  return element;
}
function number(value, digits = 3) {
  return new Intl.NumberFormat("es-EC", {minimumFractionDigits: digits, maximumFractionDigits: digits}).format(value);
}
function message(text, error = false) {
  $("#message").textContent = text;
  $("#message").hidden = !text;
  $("#message").className = error ? "message error" : "message";
}
function busy(value) {
  state.busy = value;
  for (const id of ["#demo", "#analyze", "#clear", "#csv-file"]) $(id).disabled = value;
  $("#cohort").setAttribute("aria-busy", String(value));
  $("#export").disabled = value || !state.data;
}
async function request(url, options = {}) {
  const response = await fetch(url, {...options, cache: "no-store"});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "No se pudo completar la solicitud.");
  return data;
}
async function load(url, options = {}) {
  if (state.busy) return;
  state.data = null;
  state.page = 0;
  render();
  busy(true);
  message("Analizando el lote…");
  try {
    state.data = await request(url, options);
    $("#search").value = "";
    $("#only-selected").checked = false;
    message("");
    render();
  } catch (error) {
    message(error.message, true);
  } finally {
    busy(false);
  }
}
function filtered() {
  if (!state.data) return [];
  const query = $("#search").value.trim().toUpperCase();
  return state.data.rows.filter(row =>
    (!$("#only-selected").checked || row.selected) && (!query || row.id.includes(query)));
}
function render() {
  const data = state.data;
  $("#total").textContent = data ? data.count : "—";
  $("#selected").textContent = data ? data.selected : "—";
  $("#missing").textContent = data ? data.missing_cells : "—";
  $("#source").textContent = data ? data.source : "Sin lote activo";
  $("#quality").textContent = !data ? "Sin evaluación de calidad" :
    data.warnings.length ? "Revisar advertencias de calidad" : "Sin faltantes; controles de entrada superados";
  $("#list-caption").textContent = data ? "Orden descendente de puntuación · desempate por orden del archivo" : "Sin resultados";
  $("#warnings").replaceChildren();
  $("#warnings").hidden = !data || !data.warnings.length;
  if (data && data.warnings.length) {
    const list = node("ul");
    for (const warning of data.warnings) list.append(node("li", warning));
    $("#warnings").append(list);
  }
  const items = filtered();
  const pages = Math.max(1, Math.ceil(items.length / pageSize));
  state.page = Math.min(state.page, pages - 1);
  $("#rows").replaceChildren();
  for (const row of items.slice(state.page * pageSize, (state.page + 1) * pageSize)) {
    const tr = node("tr", undefined, row.selected ? "priority" : "");
    tr.append(node("td", String(row.rank).padStart(2, "0"), "rank"));
    const id = node("td");
    id.append(node("span", row.id, "case-id"), node("small", "Fila " + row.source_row));
    tr.append(id);
    const score = node("td"), scoreBox = node("div", undefined, "score");
    const progress = node("progress");
    progress.max = 1; progress.value = row.score;
    progress.setAttribute("aria-label", "Puntuación " + number(row.score));
    scoreBox.append(node("span", number(row.score)), progress); score.append(scoreBox); tr.append(score);
    const selected = node("td");
    selected.append(node("span", row.selected ? "Priorizado" : "Fuera del cupo", row.selected ? "badge" : "badge neutral"));
    tr.append(selected, node("td", String(row.missing)));
    const action = node("td"), button = node("button", undefined, "icon-button");
    button.title = "Ver " + row.id; button.setAttribute("aria-label", button.title);
    button.append(icon("arrow-up-right")); button.addEventListener("click", () => showDetail(row));
    action.append(button); tr.append(action); $("#rows").append(tr);
  }
  $("#empty").hidden = !!items.length;
  $("#visible-count").textContent = items.length + " casos";
  $("#page-label").textContent = items.length ? "Página " + (state.page + 1) + " de " + pages : "0 resultados";
  $("#prev").disabled = state.page === 0;
  $("#next").disabled = state.page >= pages - 1;
  $("#export").disabled = !data || state.busy;
  icons();
}
function showDetail(row) {
  $("#detail-title").textContent = row.id + " · fila " + row.source_row;
  $("#detail-predicted").textContent = classLabels[row.predicted];
  $("#detail-priority").textContent = row.selected ? "Priorizado" : "Fuera del cupo";
  $("#detail-scores").replaceChildren();
  for (const [label, score] of Object.entries(row.scores)) {
    const item = node("div");
    item.append(node("span", classLabels[label]), node("strong", number(score)));
    $("#detail-scores").append(item);
  }
  $("#detail-features").replaceChildren();
  for (const [key, value] of Object.entries(row.features)) {
    $("#detail-features").append(node("dt", labels[key] || key), node("dd", value === null ? "Vacío · imputado" : Number.isInteger(value) ? String(value) : number(value, 2)));
  }
  $("#detail").showModal();
}
function downloadResults() {
  if (!state.data) return;
  const header = "caso,fila_csv,orden,puntuacion_abandono,priorizado,clase_predicha,celdas_faltantes";
  const lines = state.data.rows.map(r => [r.id, r.source_row, r.rank, r.score, r.selected ? 1 : 0, r.predicted, r.missing].join(","));
  const url = URL.createObjectURL(new Blob([header + "\n" + lines.join("\n") + "\n"], {type: "text/csv;charset=utf-8"}));
  const link = node("a"); link.href = url; link.download = "priorizacion_lote.csv"; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => {
  document.querySelectorAll(".view").forEach(view => {view.hidden = view.id !== button.dataset.view;});
  document.querySelectorAll("[data-view]").forEach(nav => {
    const active = nav === button; nav.classList.toggle("active", active);
    if (active) nav.setAttribute("aria-current", "page"); else nav.removeAttribute("aria-current");
  });
}));
$("#demo").addEventListener("click", () => { $("#csv-file").value = ""; load("/api/demo"); });
$("#upload-form").addEventListener("submit", event => {
  event.preventDefault();
  const file = $("#csv-file").files[0];
  if (!file) return;
  if (file.size > 200000) {
    state.data = null; render(); message("El archivo supera el límite de 200 KB.", true); return;
  }
  const body = new FormData(); body.append("file", file);
  load("/api/analyze", {method: "POST", body, headers: {"X-Requested-With": "local-demo"}});
});
$("#clear").addEventListener("click", () => {
  state.data = null; state.page = 0; $("#csv-file").value = ""; $("#search").value = "";
  $("#only-selected").checked = false; message(""); render();
});
$("#export").addEventListener("click", downloadResults);
for (const selector of ["#search", "#only-selected"]) $(selector).addEventListener("input", () => {state.page = 0; render();});
$("#prev").addEventListener("click", () => {state.page--; render();});
$("#next").addEventListener("click", () => {state.page++; render();});
$("#close-detail").addEventListener("click", () => $("#detail").close());
async function evidence() {
  try {
    const data = await request("/api/evidence");
    $("#final-f1").textContent = number(data.metrics.f1_macro, 5);
    $("#final-coverage").textContent = number(100 * data.metrics.recall20, 2) + " %";
    const schema = await request("/api/schema");
    for (const item of schema) {
      const tr = node("tr");
      const range = item.column === "Age at enrollment" ? "Entero de 1 a 100; advertencia fuera del rango de desarrollo" :
        item.column === "Application order" ? "Entero de 0 a 9" : "0 a 200";
      tr.append(node("td", labels[item.column]), node("td", item.column), node("td", item.values ? item.values.join(", ") : range));
      $("#schema").append(tr);
    }
  } catch (error) { message("No se pudo cargar la evidencia: " + error.message, true); }
}
icons(); render(); evidence(); load("/api/demo");
