#!/usr/bin/env node
/**
 * v64: Real PHP syntax lint for the theme — php-parser (PHP 8 grammar) tho.
 *
 * Enduku: sandbox/CI lo `php -l` binary ledu → PHP files syntax tappu unna
 * teliyadu (silent risk!). Ee script node + php-parser tho **nijamaina**
 * syntax check chestundi. php-parser lekapote build script skip chestundi.
 *
 * Usage: node tools/php_lint.js [dir ...]   (default: wordpress-theme/studentup)
 * Exit 1 = syntax error (build fail avvali).
 */
"use strict";
const fs = require("fs");
const path = require("path");

let engine = null;
try {
  engine = require(path.join(__dirname, "..", "tests", "runtime",
                           "node_modules", "php-parser"));
} catch (e) {
  try {
    engine = require("php-parser");
  } catch (e2) {
    console.log("SKIP php-lint: php-parser ledu (npm i php-parser --no-save)");
    process.exit(0);
  }
}

const roots = process.argv.slice(2).length
  ? process.argv.slice(2)
  : [path.join(__dirname, "..", "wordpress-theme", "studentup")];

function walk(dir, out) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    const st = fs.statSync(p);
    if (st.isDirectory()) {
      if (name === "node_modules" || name === ".git") continue;
      walk(p, out);
    } else if (name.endsWith(".php")) {
      out.push(p);
    }
  }
  return out;
}

const files = [];
for (const r of roots) walk(r, files);
files.sort();

const parser = new engine({
  parser: { extractDoc: false, suppressErrors: false, version: 802 },
  ast: { withPositions: true },
});

let bad = 0;
let minified = 0;
for (const f of files) {
  const code = fs.readFileSync(f, "utf8");
  try {
    parser.parseCode(code, f);
  } catch (err) {
    bad++;
    const line = (err.loc && err.loc.start && err.loc.start.line) || "?";
    console.log(`✘ ${path.relative(process.cwd(), f)}:${line} — ${err.message}`);
  }
  // house rule: no closing "?>" at EOF for pure-PHP files (WP standard),
  // and every file must guard ABSPATH.
  if (!/defined\(\s*['"]ABSPATH['"]\s*\)/.test(code)) {
    bad++;
    console.log(`✘ ${path.relative(process.cwd(), f)} — ABSPATH guard ledu`);
  }
  if (/<\?php[\s\S]*\?>\s*$/.test(code) && !/<\/[a-z]/i.test(code)) {
    minified++; // informational only
  }
}
console.log(`php-lint: ${files.length - bad}/${files.length} files OK` +
            (minified ? ` (${minified} informational)` : ""));
process.exit(bad ? 1 : 0);
