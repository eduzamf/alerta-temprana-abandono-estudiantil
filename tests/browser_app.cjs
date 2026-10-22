/* Run with Playwright installed and the local server already listening. */
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const path = require("node:path");

(async () => {
  const browser = await chromium.launch({headless: true, channel: process.env.BROWSER_CHANNEL || "chrome"});
  const page = await browser.newPage({viewport: {width: 1440, height: 1100}});
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(process.env.APP_URL || "http://127.0.0.1:5057");
  await page.waitForFunction(() => document.querySelector("#total").textContent === "40");
  assert.equal(await page.locator("#selected").textContent(), "8");
  assert.equal(await page.locator("#rows tr").count(), 15);
  assert.ok(await page.locator(".brand svg").count());
  assert.match(await page.locator("#score-explanation").textContent(), /0,700 no significa/);
  assert.equal(await page.locator("#cohort table").getAttribute("aria-describedby"), "score-explanation");
  await page.screenshot({path: path.resolve("docs/images/app_desktop.png"), fullPage: true});
  await page.evaluate(() => {
    const targets = ["#upload-form", ".metrics", ".table-tools", "#score-explanation", "#rows button"];
    targets.forEach((selector, index) => {
      const bounds = document.querySelector(selector).getBoundingClientRect();
      const marker = document.createElement("span");
      marker.dataset.manualAnnotation = "true";
      marker.textContent = String(index + 1);
      Object.assign(marker.style, {
        position: "absolute", left: (bounds.left + window.scrollX - 12) + "px",
        top: (bounds.top + window.scrollY - 12) + "px", zIndex: "20",
        background: "#763e48", color: "#fff", border: "2px solid #fff",
        borderRadius: "50%", width: "25px", height: "25px", textAlign: "center",
        lineHeight: "21px", font: "bold 13px/21px Arial",
      });
      document.body.append(marker);
    });
  });
  await page.screenshot({path: path.resolve("docs/images/app_annotated.png"), fullPage: true});
  await page.evaluate(() => document.querySelectorAll("[data-manual-annotation]").forEach(e => e.remove()));
  await page.locator("#only-selected").check();
  assert.equal(await page.locator("#rows tr").count(), 8);
  await page.locator("#search").fill("ZZZ");
  assert.equal(await page.locator("#rows tr").count(), 0);
  await page.locator("#search").fill("");
  await page.locator("#rows button").first().click();
  assert.ok(await page.locator("#detail").isVisible());
  assert.equal(await page.locator("#detail-features dt").count(), 18);
  const demoData = await (await page.request.get(new URL("/api/demo", page.url()).href)).json();
  const classLabels = {Dropout: "Abandono", Enrolled: "Continuidad en estudios", Graduate: "Graduación"};
  assert.equal(await page.locator("#detail-predicted").textContent(), classLabels[demoData.rows[0].predicted]);
  assert.equal(await page.locator("#detail-priority").textContent(), "Priorizado");
  assert.match(await page.locator("#detail-scores").textContent(), /Continuidad en estudios/);
  assert.match(await page.locator(".detail-definition").textContent(), /cierre del seguimiento/);
  assert.match(await page.locator(".detail-disclaimer").textContent(), /no es un porcentaje comprobado/);
  await page.screenshot({path: path.resolve("docs/images/app_detail.png"), fullPage: false});
  await page.keyboard.press("Escape");
  await page.locator("#only-selected").uncheck();
  await page.locator("#next").click();
  assert.match(await page.locator("#page-label").textContent(), /2 de 3/);
  const download = page.waitForEvent("download");
  await page.locator("#export").click();
  assert.equal((await download).suggestedFilename(), "priorizacion_lote.csv");
  const sample = await (await page.request.get(new URL("/api/sample", page.url()).href)).body();
  await page.locator("#csv-file").setInputFiles({name: "sample.csv", mimeType: "text/csv", buffer: sample});
  await page.locator("#analyze").click();
  await page.waitForFunction(() => document.querySelector("#source").textContent.includes("CSV cargado"));
  const missingSample = await (await page.request.get(new URL("/api/sample/missing", page.url()).href)).body();
  await page.locator("#csv-file").setInputFiles({name: "02_nota_vacia.csv", mimeType: "text/csv", buffer: missingSample});
  await page.locator("#analyze").click();
  await page.waitForFunction(() => document.querySelector("#missing").textContent === "1");
  assert.ok(await page.locator("#warnings").isVisible());
  await page.screenshot({path: path.resolve("docs/images/app_warning.png"), fullPage: true});
  const invalidSample = await (await page.request.get(new URL("/api/sample/invalid", page.url()).href)).body();
  await page.locator("#csv-file").setInputFiles({name: "03_carrera_invalida.csv", mimeType: "text/csv", buffer: invalidSample});
  await page.locator("#analyze").click();
  await page.waitForFunction(() => document.querySelector("#message").textContent.includes("Course"));
  assert.equal(await page.locator("#rows tr").count(), 0);
  await page.locator("#csv-file").setInputFiles({name: "bad.csv", mimeType: "text/csv", buffer: Buffer.from("name,email\nAna,a@b.c")});
  await page.locator("#analyze").click();
  await page.waitForFunction(() => document.querySelector("#message").classList.contains("error"));
  assert.equal(await page.locator("#rows tr").count(), 0);
  assert.ok(await page.locator("#export").isDisabled());
  await page.screenshot({path: path.resolve("docs/images/app_error.png"), fullPage: true});
  await page.locator("#demo").click();
  await page.waitForFunction(() => document.querySelector("#total").textContent === "40");
  await page.locator('[data-view="evidence"]').click();
  await page.waitForFunction(() => document.querySelector("#final-f1").textContent.includes("49366"));
  assert.match(await page.locator(".model-description").textContent(), /Regresión logística multiclase/);
  assert.ok(await page.locator("#evidence img").evaluate(img => img.complete && img.naturalWidth > 0));
  await page.screenshot({path: path.resolve("docs/images/app_evidence.png"), fullPage: true});
  await page.locator('[data-view="data"]').click();
  assert.equal(await page.locator("#schema tr").count(), 18);
  await page.setViewportSize({width: 390, height: 844});
  await page.locator('[data-view="cohort"]').click();
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  await page.screenshot({path: path.resolve("docs/images/app_mobile.png"), fullPage: true});
  await page.locator("#rows button").first().scrollIntoViewIfNeeded();
  await page.locator("#rows button").first().click();
  assert.ok(await page.locator("#detail-predicted").isVisible());
  assert.ok(await page.locator("#detail").evaluate(e => e.scrollWidth <= e.clientWidth));
  await page.screenshot({path: path.resolve("docs/images/app_detail_mobile.png"), fullPage: false});
  await page.keyboard.press("Escape");
  for (const width of [320, 768, 1280]) {
    await page.setViewportSize({width, height: 900});
    for (const view of ["evidence", "data", "cohort"]) {
      await page.locator(`[data-view="${view}"]`).click();
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `${view} overflows at ${width}px`);
    }
  }
  await page.locator("#clear").click();
  assert.equal(await page.locator("#rows tr").count(), 0);
  assert.deepEqual(errors, []);
  await browser.close();
  console.log("Browser checks passed: demo, upload, rejection, ranking, filters, pagination, detail, export, evidence, schema, desktop/mobile.");
})().catch(error => { console.error(error); process.exit(1); });
