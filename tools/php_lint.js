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
    engine = null;   // v135: fall back to the built-in structural checker
  }
}

/**
 * v135: dependency-free fallback lint.
 *
 * php-parser is the real grammar check, but a fresh clone (or an offline CI
 * box) may not have node_modules yet. Silently skipping meant a syntax error
 * could ship unnoticed, so this fallback still catches the mistakes that
 * actually white-screen a WordPress site: unbalanced braces/parens/brackets,
 * an unterminated string, heredoc or block comment, and a stray closing tag.
 * Strings, comments and heredocs are skipped while scanning.
 *
 * @param {string} code PHP source.
 * @returns {string|null} Error message, or null when the file looks sane.
 */
function fallbackCheck(code) {
  const pairs = { "}": "{", ")": "(", "]": "[" };
  const stack = [];
  let i = 0;
  let line = 1;
  const n = code.length;
  let inPhp = false;
  while (i < n) {
    const c = code[i];
    if (c === "\n") { line++; i++; continue; }
    if (!inPhp) {
      if (code.startsWith("<?php", i) || code.startsWith("<?=", i)) { inPhp = true; i += 3; }
      else { i++; }
      continue;
    }
    if (code.startsWith("?>", i)) { inPhp = false; i += 2; continue; }
    if (code.startsWith("//", i) || c === "#") {
      const nl = code.indexOf("\n", i);
      i = nl === -1 ? n : nl;
      continue;
    }
    if (code.startsWith("/*", i)) {
      const end = code.indexOf("*/", i + 2);
      if (end === -1) return `line ${line}: block comment mudiyaledu`;
      for (let k = i; k < end; k++) if (code[k] === "\n") line++;
      i = end + 2;
      continue;
    }
    if (c === "'" || c === '"') {
      const quote = c;
      let k = i + 1;
      while (k < n) {
        if (code[k] === "\\") { k += 2; continue; }
        if (code[k] === "\n") line++;
        if (code[k] === quote) break;
        k++;
      }
      if (k >= n) return `line ${line}: string mudiyaledu (${quote})`;
      i = k + 1;
      continue;
    }
    const here = /^<<<(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1\r?\n/.exec(code.slice(i));
    if (here) {
      const label = here[2];
      const close = new RegExp(`^\\s*${label}\\b`, "m");
      const rest = code.slice(i + here[0].length);
      const m = close.exec(rest);
      if (!m) return `line ${line}: heredoc ${label} close ledu`;
      const consumed = here[0].length + m.index + m[0].length;
      for (let k = 0; k < consumed; k++) if (code[i + k] === "\n") line++;
      i += consumed;
      continue;
    }
    if (c === "{" || c === "(" || c === "[") { stack.push({ c, line }); i++; continue; }
    if (pairs[c]) {
      const top = stack.pop();
      if (!top || top.c !== pairs[c]) return `line ${line}: '${c}' match avvaledu`;
      i++;
      continue;
    }
    i++;
  }
  if (stack.length) {
    return `line ${stack[stack.length - 1].line}: '${stack[stack.length - 1].c}' close avvaledu`;
  }
  return null;
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

const parser = engine
  ? new engine({
    parser: { extractDoc: false, suppressErrors: false, version: 802 },
    ast: { withPositions: true },
  })
  : null;
const mode = parser ? "php-parser" : "fallback";

let bad = 0;
let minified = 0;
for (const f of files) {
  const code = fs.readFileSync(f, "utf8");
  if (parser) {
    try {
      parser.parseCode(code, f);
    } catch (err) {
      bad++;
      const line = (err.loc && err.loc.start && err.loc.start.line) || "?";
      console.log(`✘ ${path.relative(process.cwd(), f)}:${line} — ${err.message}`);
    }
  } else {
    const problem = fallbackCheck(code);
    if (problem) {
      bad++;
      console.log(`✘ ${path.relative(process.cwd(), f)} — ${problem}`);
    }
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
console.log(`php-lint [${mode}]: ${files.length - bad}/${files.length} files OK` +
            (minified ? ` (${minified} informational)` : ""));
process.exit(bad ? 1 : 0);
