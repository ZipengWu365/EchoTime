#!/usr/bin/env node
/**
 * Exercise the similarity lab's rendering and controls with Node built-ins.
 *
 * Run: node tools/check_similarity_lab_ui.js
 * Optional: --write-svg /tmp/echotime-lab-svg-check
 *
 * This is a deliberately small DOM shim, NOT a browser or layout test. It
 * validates the actual shipped JS against every saved state and method without
 * installing dependencies, starting a browser, or making a network request.
 */
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const bundle = path.resolve(__dirname, "../src/echotime/data/similarity_lab");
const html = fs.readFileSync(path.join(bundle, "similarity-lab.html"), "utf8");
const payload = JSON.parse(fs.readFileSync(path.join(bundle, "states.json"), "utf8"));
const scriptURL = "https://example.test/assets/similarity-lab/lab.js";

class Element {
  constructor(id) {
    this.id = id;
    this.value = "";
    this.events = {};
    this.attributes = {};
    this.classList = { add() {}, remove() {} };
    this.body = null;
    this._html = "";
    this.textContent = "";
  }

  set innerHTML(value) {
    this._html = value;
    if (this.id.endsWith("method") || this.id === "perturbation") {
      const match = value.match(/<option value="([^"]+)"/);
      this.value = match ? match[1] : "";
    }
  }

  get innerHTML() { return this._html; }
  setAttribute(key, value) { this.attributes[key] = value; }
  addEventListener(name, callback) { this.events[name] = callback; }
  querySelector(selector) {
    assert.equal(selector, ".method-body");
    return this.body || (this.body = new Element(this.id + "-body"));
  }
  click() { if (this.events.click) this.events.click(); }
}

const ids = [...html.matchAll(/id="([^"]+)"/g)].map(match => match[1]);
const elements = Object.fromEntries(ids.map(id => [id, new Element(id)]));
elements.strength.value = "12";
elements.inspect.value = "32";

const document = {
  currentScript: { src: scriptURL },
  getElementById(id) {
    assert(elements[id], `HTML element #${id} is missing`);
    return elements[id];
  },
  documentElement: { dataset: {} },
  addEventListener() {},
  createElement: () => new Element("a"),
};

let tick;
const window = {
  addEventListener() {},
  setInterval(callback) { tick = callback; return 1; },
  clearInterval() { tick = null; },
  setTimeout(callback) { callback(); },
};

const context = {
  document, window, URL, Blob, console,
  fetch: async url => {
    assert.equal(url, new URL("states.json", scriptURL).href,
      "The UI must only request its bundled numerical data");
    return { ok: true, json: async () => payload };
  },
};
vm.runInNewContext(fs.readFileSync(path.join(bundle, "lab.js"), "utf8"), context);

setImmediate(() => {
  try {
    assert.equal(document.documentElement.dataset.labReady, "true");
    const perturbations = payload.data.perturbations.map(item => item.id);
    const methods = payload.data.methods.map(item => item.id);
    let stateMethodRenders = 0;

    for (const kind of perturbations) {
      for (let level = 0; level < payload.data.levels; level++) {
        for (const method of methods) {
          elements.perturbation.value = kind;
          elements.strength.value = String(level);
          elements["right-method"].value = method;
          elements["right-method"].events.change();
          for (const id of ["left-card", "right-card"]) {
            const content = elements[id].body.innerHTML;
            assert(content.includes("<svg"));
            assert(!/\b(?:NaN|Infinity|undefined)\b/.test(content),
              `Invalid geometry or unresolved data: ${kind}/${level}/${method}`);
          }
          stateMethodRenders++;
        }
      }
    }

    // Check shared-input inspection, including the last first-difference interval.
    elements.perturbation.value = "warp";
    elements.strength.value = "20";
    elements["left-method"].value = "dtw";
    elements["right-method"].value = "derivative";
    elements["right-method"].events.change();
    for (const position of [0, 20, 44, 63]) {
      elements.inspect.value = String(position);
      elements.inspect.events.input();
      assert(!/\b(?:NaN|Infinity|undefined)\b/.test(elements["right-card"].body.innerHTML));
    }

    elements.reset.click();
    assert.equal(elements.strength.value, "0");
    elements.play.click();
    assert.equal(elements.play.textContent, "Pause");
    tick();
    assert.equal(elements.strength.value, "1");
    elements.play.click();
    assert.equal(elements.play.textContent, "Play levels");
    elements["gif-toggle"].click();
    assert(elements["comparison-image"].src.endsWith(".gif"));
    elements["gif-toggle"].click();
    assert(elements["comparison-image"].src.endsWith(".png"));

    let svgFiles = 0;
    const outputFlag = process.argv.indexOf("--write-svg");
    if (outputFlag !== -1) {
      assert(process.argv[outputFlag + 1], "--write-svg requires an output directory");
      const output = path.resolve(process.argv[outputFlag + 1]);
      fs.mkdirSync(output, { recursive: true });
      const writeSVG = (name, svg) => {
        fs.writeFileSync(path.join(output, name),
          svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" '));
        svgFiles++;
      };
      elements.perturbation.value = "phase";
      elements.strength.value = "20";
      elements["left-method"].value = "rmse";
      elements["right-method"].value = "dft";
      elements["right-method"].events.change();
      writeSVG("raw.svg", elements["raw-plot"].innerHTML);
      for (const method of methods) {
        elements["right-method"].value = method;
        elements["right-method"].events.change();
        const svgs = [...elements["right-card"].body.innerHTML.matchAll(/<svg[\s\S]*?<\/svg>/g)];
        svgs.forEach((match, i) => writeSVG(`${method}-${i}.svg`, match[0]));
      }
    }

    console.log(JSON.stringify({
      stateMethodRenders, svgFiles,
      checks: ["finite SVG geometry", "all saved states and methods", "inspection endpoints",
        "identity reset", "play/pause", "GIF/still toggle"],
      environment: "Node VM with a minimal DOM shim; not a real browser layout test",
    }, null, 2));
  } catch (error) {
    console.error(error.stack);
    process.exitCode = 1;
  }
});
