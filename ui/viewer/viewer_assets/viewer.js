(function () {
const CFG = __CFG__;
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const hexStr = n => "#" + n.toString(16).padStart(6, "0");
const lerp = (c1, c2, t) => {
  const f = s => ((c1 >> s) & 255) * (1 - t) + ((c2 >> s) & 255) * t;
  return (Math.round(f(16)) << 16) | (Math.round(f(8)) << 8) | Math.round(f(0));
};
function hsl(h, s, l) {
  s /= 100; l /= 100;
  const k = n => (n + h / 30) % 12, a = s * Math.min(l, 1 - l);
  const f = n => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return (Math.round(255 * f(0)) << 16) | (Math.round(255 * f(8)) << 8) | Math.round(255 * f(4));
}

/* ---------------- state ---------------- */
const S = {
  rep: CFG.style, col: CFG.colorBy, spin: CFG.autoRotate, speed: 0.3, wire: false, axes: true, legend: true,
  lig: true, water: false, pocket: false, slice: false, depth: 0, thick: 100, opacity: 0.6,
  mode: "select", dark: CFG.dark,
  sel: {}, meas: [], mShapes: [], mLabels: [], dists: [],
  chains: [], range: {}, bmin: 0, bmax: 1, hasSS: false, hasLig: false, ligNames: [],
  nAtoms: 0, nProt: 0, nRes: 0, radius: 30, min: {x:0,y:0,z:0}, max: {x:0,y:0,z:0},
  view0: null, surfId: null, base: "Loading…", note: ""
};

const wrap = $("wrap");
if (CFG.minimal) wrap.classList.add("minimal");

$("rep").value = S.rep;
$("col").value = S.col;

/* ---------------- Streamlit theme detection ---------------- */

function readStreamlitThemePreference() {
  try {
    // Use the global Streamlit theme preference.
    return window.parent.localStorage.getItem("stActiveTheme-/-v2");
  } catch (error) {
    return null;
  }
}

function detectDarkFromPage() {
  try {
    const doc = window.parent.document;

    const app =
      doc.querySelector('[data-testid="stApp"]') ||
      doc.querySelector('[data-testid="stAppViewContainer"]') ||
      doc.body;

    // Check explicit theme attributes first.
    const theme =
      app?.getAttribute("data-theme") ||
      doc.documentElement.getAttribute("data-theme") ||
      doc.body?.getAttribute("data-theme");

    if (theme && /^(dark|light)$/i.test(theme)) {
      return theme.toLowerCase() === "dark";
    }

    // Fall back to the actual rendered page background.
    const candidates = [
      app,
      doc.documentElement,
      doc.body
    ].filter(Boolean);

    for (const element of candidates) {
      const styles = window.parent.getComputedStyle(element);
      const bg = styles.backgroundColor;
      const match = bg && bg.match(/\d+(?:\.\d+)?/g);

      if (!match || match.length < 3) continue;

      const [r, g, b] = match.slice(0, 3).map(Number);
      const alpha = match.length >= 4 ? Number(match[3]) : 1;

      if (alpha === 0) continue;

      const luminance =
        (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;

      return luminance < 0.5;
    }
  } catch (error) {
    // The browser may restrict access to the parent iframe.
  }

  return null;
}

function getInitialDarkTheme() {
  // FoldShield uses a fixed light palette across browsers and devices.
  return false;
}

/* ---------------- Theme initialization ---------------- */

S.dark = getInitialDarkTheme();

function getThemeBackground(dark) {
  return dark ? "#000000" : "#ffffff";
}

function applyThemeBackground(dark) {
  const background = getThemeBackground(dark);

  // Set the iframe document background before rendering the canvas.
  document.documentElement.style.backgroundColor = background;

  if (document.body) {
    document.body.style.backgroundColor = background;
  }

  // Update viewer containers.
  wrap.classList.toggle("dark", dark);
  wrap.style.backgroundColor = background;

  const stage = $("stage");
  if (stage) {
    stage.style.backgroundColor = background;
  }

  const viewerHost = $("v");
  if (viewerHost) {
    viewerHost.style.backgroundColor = background;

    // Prevent a white CSS background from showing through the canvas.
    viewerHost.querySelectorAll("canvas").forEach(canvas => {
      canvas.style.backgroundColor = background;
    });
  }
}

// Apply the correct theme before creating the WebGL viewer.
applyThemeBackground(S.dark);

const v = $3Dmol.createViewer("v", {
  backgroundColor: getThemeBackground(S.dark),
  antialias: true
});

/* ---------------- Live theme synchronization ---------------- */

function syncStreamlitTheme() {
  // Ignore browser, OS and Streamlit user theme preferences.
}

// React to theme preference changes.
window.addEventListener("storage", event => {
  if (!event.key || event.key.startsWith("stActiveTheme-")) {
    syncStreamlitTheme();
  }
});

// Watch the parent Streamlit page for theme changes.
try {
  const parentDoc = window.parent.document;

  const observer = new MutationObserver(() => {
    syncStreamlitTheme();
  });

  observer.observe(parentDoc.documentElement, {
    attributes: true,
    attributeFilter: ["class", "style", "data-theme"],
    subtree: true
  });

  if (parentDoc.body) {
    observer.observe(parentDoc.body, {
      attributes: true,
      attributeFilter: ["class", "style", "data-theme"],
      subtree: true
    });
  }
} catch (error) {
  // Keep the initial theme if parent-document access is restricted.
}

/* ---------------- selections ---------------- */
const isWater = a => a.resn === "HOH" || a.resn === "WAT" || a.resn === "H2O";
let SEL_PROT = { hetflag: false };
const SEL_LIG = { predicate: a => a.hetflag && !isWater(a) };
const SEL_WAT = { predicate: isWater };

/* ---------------- colour functions ---------------- */
const CHAIN_PAL = [0x4e79a7,0xf28e2b,0xe15759,0x76b7b2,0x59a14f,0xedc948,0xb07aa1,0xff9da7,0x9c755f,0xbab0ac];
const CPK = {C:0x909090,N:0x3050f8,O:0xff0d0d,S:0xffd123,P:0xff8000,H:0xffffff,FE:0xe06633,ZN:0x7d80b0,
             MG:0x8aff00,CA:0x3dff00,NA:0xab5cf2,CL:0x1ff01f,F:0x90e050,BR:0xa62929,I:0x940094};
const RES_GROUPS = [
  {name:"Hydrophobic", c:0xf59e0b, r:"ALA VAL LEU ILE MET PHE TRP PRO"},
  {name:"Polar",       c:0x10b981, r:"SER THR ASN GLN TYR"},
  {name:"Positive (+)",c:0x3b82f6, r:"LYS ARG HIS"},
  {name:"Negative (−)",c:0xef4444, r:"ASP GLU"},
  {name:"Gly / Cys",   c:0xa855f7, r:"GLY CYS"}
];
const RES_MAP = {};
RES_GROUPS.forEach(g => g.r.split(" ").forEach(n => RES_MAP[n] = g.c));
const elemColor = a => { const c = CPK[String(a.elem || "C").toUpperCase()]; return c === undefined ? 0xff1493 : c; };
const ligColor = a => String(a.elem || "").toUpperCase() === "C" ? 0x22c55e : elemColor(a);

const COLORS = {
  spectrum: a => {
    const r = S.range[a.chain];
    if (!r || r[1] === r[0] || typeof a.resi !== "number") return 0x9ca3af;
    const t = Math.max(0, Math.min(1, (a.resi - r[0]) / (r[1] - r[0])));
    return hsl(240 * (1 - t), 80, 50);
  },
  chain: a => { const i = S.chains.indexOf(a.chain); return CHAIN_PAL[(i < 0 ? 0 : i) % CHAIN_PAL.length]; },
  ss: a => a.ss === "h" ? 0xe5484d : a.ss === "s" ? 0xf5a524 : 0x9ca3af,
  residue: a => RES_MAP[a.resn] !== undefined ? RES_MAP[a.resn] : 0x9ca3af,
  bfactor: a => {
    const t = Math.max(0, Math.min(1, ((a.b || 0) - S.bmin) / ((S.bmax - S.bmin) || 1)));
    return t < 0.5 ? lerp(0x2563eb, 0xffffff, t * 2) : lerp(0xffffff, 0xdc2626, (t - 0.5) * 2);
  },
  element: elemColor
};

/* ---------------- status / info ---------------- */
function setStatus() { $("status").textContent = S.base + (S.note ? "  ·  " + S.note : ""); }
let noteT = null;
function note(msg, ms) {
  S.note = msg; setStatus(); clearTimeout(noteT);
  if (ms) noteT = setTimeout(() => { S.note = ""; setStatus(); }, ms);
}
const SS_NAME = { h: "helix", s: "sheet", c: "coil" };
const lab = a => `${a.resn}${a.resi}:${a.atom}`;

function renderInfo(a) {
  let h = "";
  if (a) {
    h += `<b>${esc(a.resn)} ${esc(a.resi)}</b> <span class="m">chain ${esc(a.chain)}</span><br>` +
         `Atom <b>${esc(a.atom)}</b> (${esc(a.elem)}) <span class="m">#${esc(a.serial)}</span><br>` +
         `<span class="m">x,y,z</span> ${a.x.toFixed(1)}, ${a.y.toFixed(1)}, ${a.z.toFixed(1)}<br>` +
         `<span class="m">B-factor</span> ${(a.b || 0).toFixed(1)}` +
         (a.hetflag ? "" : ` · <span class="m">SS</span> ${SS_NAME[a.ss] || "coil"}`);
  }
  const keys = Object.keys(S.sel);
  if (keys.length) {
    h += `<div class="selection-head"><div class="hd">Selected (${keys.length})</div>` +
         `<button class="selection-clear" type="button" data-clear-selections>Clear</button></div>` +
         keys.slice(0, 12).map(k => `<button class="chip" type="button" data-remove-selection="${esc(k)}" aria-label="Remove ${esc(S.sel[k].text)}">${esc(S.sel[k].text)} <span aria-hidden="true">×</span></button>`).join("") +
         (keys.length > 12 ? ` +${keys.length - 12}` : "");
  }
  if (S.dists.length) {
    h += `<div class="hd">Distances</div>` + S.dists.map(d => `<div>${esc(d)}</div>`).join("");
  }
  $("info").innerHTML = h;                      // "" when there is nothing to show: the CSS hides the empty panel
}

$("info").addEventListener("click", event => {
  if (event.target.closest("[data-clear-selections]")) {
    clearSelectionAndReset();
    return;
  }
  const remove = event.target.closest("[data-remove-selection]");
  if (remove) removeResidueSelection(remove.getAttribute("data-remove-selection"));
});

/* ---------------- legend ---------------- */
function renderLegend() {
  const L = $("legend");
  if (!S.legend) { L.style.display = "none"; return; }
  L.style.display = "block";
  const row = (c, t) => `<div class="lg"><i style="background:${hexStr(c)}"></i>${esc(t)}</div>`;
  let h = "";
  if (S.col === "spectrum") {
    const stops = [0, .25, .5, .75, 1].map(t => `hsl(${240 * (1 - t)},80%,50%)`).join(",");
    h += `<div class="hd">Residue position</div><div class="grad" style="background:linear-gradient(90deg,${stops})"></div>` +
         `<div class="row"><span>N-term</span><span>C-term</span></div>`;
  } else if (S.col === "chain") {
    h += `<div class="hd">Chains</div>` + S.chains.map(c => row(COLORS.chain({chain: c}), "Chain " + c)).join("");
  } else if (S.col === "ss") {
    h += `<div class="hd">Secondary structure</div>` + row(0xe5484d, "Helix") + row(0xf5a524, "β-sheet") + row(0x9ca3af, "Coil / loop");
    if (!S.hasSS) h += `<div class="m">No HELIX/SHEET records: all coil</div>`;
  } else if (S.col === "residue") {
    h += `<div class="hd">Residue type</div>` + RES_GROUPS.map(g => row(g.c, g.name)).join("");
  } else if (S.col === "bfactor") {
    h += `<div class="hd">B-factor</div><div class="grad" style="background:linear-gradient(90deg,#2563eb,#fff,#dc2626)"></div>` +
         `<div class="row"><span>${S.bmin.toFixed(0)} (rigid)</span><span>${S.bmax.toFixed(0)} (mobile)</span></div>`;
  } else if (S.col === "element") {
    h += `<div class="hd">Element</div>` + [["C",0x909090],["N",0x3050f8],["O",0xff0d0d],["S",0xffd123],["P",0xff8000],["H",0xffffff]].map(([e,c]) => row(c, e)).join("");
  }
  const extra = [];
  if (S.lig && S.hasLig) extra.push(row(0x22c55e, "Ligand: " + S.ligNames.slice(0, 4).join(", ")));
  if (S.pocket && S.hasLig) extra.push(row(0xffffff, "Pocket ≤ 5 Å (sticks)"));
  if (Object.keys(S.sel).length) extra.push(row(0xff2d95, "Selected residue"));
  if (S.water) extra.push(row(0x60a5fa, "Water"));
  if (extra.length) h += `<div class="hd">Overlays</div>` + extra.join("");
  L.innerHTML = h;
}

/* ---------------- styles ---------------- */
function applyStyle() {
  const cf = COLORS[S.col] || COLORS.spectrum, P = SEL_PROT;
  v.setStyle({}, {});
  switch (S.rep) {
    case "cartoon": case "surface": v.setStyle(P, { cartoon: { colorfunc: cf } }); break;
    case "cartoon+sticks": v.setStyle(P, { cartoon: { colorfunc: cf }, stick: { colorfunc: cf, radius: 0.12 } }); break;
    case "sticks": v.setStyle(P, { stick: { colorfunc: cf, radius: 0.16 } }); break;
    case "ballstick": v.setStyle(P, { stick: { colorfunc: cf, radius: 0.12 }, sphere: { colorfunc: cf, scale: 0.28 } }); break;
    case "spheres": v.setStyle(P, { sphere: { colorfunc: cf } }); break;
    case "lines": v.setStyle(P, { line: { colorfunc: cf } }); break;
  }
  if (S.wire && S.rep !== "lines") v.addStyle(P, { line: { colorfunc: cf } });
  if (S.lig && S.hasLig) v.addStyle(SEL_LIG, { stick: { colorfunc: ligColor, radius: 0.2 }, sphere: { colorfunc: ligColor, scale: 0.25 } });
  if (S.water) v.addStyle(SEL_WAT, { sphere: { color: 0x60a5fa, radius: 0.35, opacity: 0.8 } });
  if (S.pocket && S.hasLig) v.addStyle({ within: { distance: 5, sel: SEL_LIG }, hetflag: false, byres: true }, { stick: { colorfunc: cf, radius: 0.18 } });
  Object.values(S.sel).forEach(o => v.addStyle(
    { within: { distance: 7, sel: { chain: o.chain, resi: o.resi } }, hetflag: false, byres: true },
    { stick: { colorfunc: cf, radius: 0.13 } }
  ));
  Object.values(S.sel).forEach(o => v.addStyle({ chain: o.chain, resi: o.resi }, { stick: { color: 0xff2d95, radius: 0.3 } }));
  v.render();
}

let surfTok = 0;
function surfStyle() {
  const opacity = Object.keys(S.sel).length ? Math.min(S.opacity, 0.18) : S.opacity;
  return { opacity, colorfunc: COLORS[S.col] || COLORS.spectrum, wireframe: S.wire };
}
function applySurface() {
  surfTok++; const tok = surfTok;
  v.removeAllSurfaces(); S.surfId = null;
  if (S.rep !== "surface") { v.render(); return; }
  note("computing surface…");
  const type = S.nProt > 30000 ? $3Dmol.SurfaceType.VDW : $3Dmol.SurfaceType.MS;
  try {
    Promise.resolve(v.addSurface(type, surfStyle(), SEL_PROT, SEL_PROT)).then(id => {
      if (tok !== surfTok) { try { v.removeSurface(id); } catch (e) {} return; }
      S.surfId = id; note(""); v.render();
    }).catch(() => note("surface failed", 3000));
  } catch (e) { note("surface failed", 3000); }
}

function applySpin() {
  v.spin(false);
  if (S.spin) v.spin("y", S.speed);
}

function applyAxes() {
  $("orientation").style.display = S.axes ? "grid" : "none";
  updateOrientation();
}

function updateOrientation(view) {
  const q = (view || v.getView()).slice(4, 8);
  const [qx, qy, qz, qw] = q;
  const center = 28, scale = 19;
  const axes = [
    ["X", [1, 0, 0]], ["Y", [0, 1, 0]], ["Z", [0, 0, 1]]
  ];
  axes.forEach(([name, basis]) => {
    const [x, y, z] = basis;
    const tx = 2 * (qy * z - qz * y);
    const ty = 2 * (qz * x - qx * z);
    const tz = 2 * (qx * y - qy * x);
    const rx = x + qw * tx + qy * tz - qz * ty;
    const ry = y + qw * ty + qz * tx - qx * tz;
    const rz = z + qw * tz + qx * ty - qy * tx;
    const x2 = center + rx * scale;
    const y2 = center - ry * scale;
    const line = $("axis" + name);
    const label = $("axisLabel" + name);
    line.setAttribute("x2", x2.toFixed(2));
    line.setAttribute("y2", y2.toFixed(2));
    line.style.opacity = String(0.35 + 0.65 * ((rz + 1) / 2));
    label.setAttribute("x", (center + rx * (scale + 5)).toFixed(2));
    label.setAttribute("y", (center - ry * (scale + 5) + 3).toFixed(2));
    label.setAttribute("text-anchor", rx < -0.2 ? "end" : rx > 0.2 ? "start" : "middle");
    label.style.opacity = line.style.opacity;
  });
}
v.setViewChangeCallback(updateOrientation);

/* ---------------- interaction ---------------- */
function focusSelection() {
  const residues = Object.values(S.sel);
  if (!residues.length) {
    v.zoomTo({}, 600);
    return;
  }
  const localStructure = {
    or: residues.map(o => ({
      within: { distance: 8, sel: { chain: o.chain, resi: o.resi } },
      hetflag: false
    }))
  };
  v.zoomTo(localStructure, 600);
}

function toggleResidue(a) {
  const key = a.chain + ":" + a.resi + (a.icode || "");
  if (S.sel[key]) { if (S.sel[key].label) v.removeLabel(S.sel[key].label); delete S.sel[key]; }
  else {
    const text = `${a.resn}${a.resi}:${a.chain}`;
    const label = v.addLabel(text, { position: { x: a.x, y: a.y, z: a.z }, fontSize: 12, fontColor: "white",
      backgroundColor: "#ff2d95", backgroundOpacity: 0.9, borderThickness: 0, inFront: true });
    S.sel[key] = { chain: a.chain, resi: a.resi, text, label };
  }
  applyStyle(); applySurface(); focusSelection(); renderLegend(); renderInfo(a);
}

function measureClick(a) {
  S.meas.push(a);
  S.mShapes.push(v.addSphere({ center: { x: a.x, y: a.y, z: a.z }, radius: 0.45, color: 0xfacc15, opacity: 0.85 }));
  if (S.meas.length === 2) {
    const p = S.meas[0], q = S.meas[1], d = Math.hypot(p.x - q.x, p.y - q.y, p.z - q.z);
    S.mShapes.push(v.addCylinder({ start: { x: p.x, y: p.y, z: p.z }, end: { x: q.x, y: q.y, z: q.z }, radius: 0.07,
      color: 0xfacc15, dashed: true, dashLength: 0.35, gapLength: 0.2, fromCap: 1, toCap: 1 }));
    S.mLabels.push(v.addLabel(d.toFixed(2) + " Å", { position: { x: (p.x + q.x) / 2, y: (p.y + q.y) / 2, z: (p.z + q.z) / 2 },
      fontSize: 12, fontColor: "#111", backgroundColor: "#facc15", backgroundOpacity: 0.95, inFront: true }));
    S.dists.push(`${lab(p)} ↔ ${lab(q)}: ${d.toFixed(2)} Å`);
    S.meas = [];
  }
  v.render(); renderInfo(a);
}

function clearAll() {
  Object.values(S.sel).forEach(o => o.label && v.removeLabel(o.label)); S.sel = {};
  S.mShapes.forEach(s => v.removeShape(s)); S.mLabels.forEach(l => v.removeLabel(l));
  S.mShapes = []; S.mLabels = []; S.meas = []; S.dists = [];
  applyStyle(); applySurface(); v.zoomTo({}, 600); renderLegend(); renderInfo(null);
}

function clearSelectionAndReset() {
  if (Object.keys(S.sel).length) {
    Object.values(S.sel).forEach(o => o.label && v.removeLabel(o.label));
    S.sel = {};
    applyStyle(); applySurface(); renderLegend(); renderInfo(null);
  }
  v.zoomTo({}, 600);
}

function removeResidueSelection(key) {
  const selected = S.sel[key];
  if (!selected) return;
  if (selected.label) v.removeLabel(selected.label);
  delete S.sel[key];
  applyStyle(); applySurface(); focusSelection(); renderLegend(); renderInfo(null);
}

/* Must run AFTER the model is loaded: setClickable/setHoverable only flag atoms that already exist.
   (Registering them before addModel/download was why clicks did nothing.) */
const isMinimal = () => wrap.classList.contains("minimal");
let interactive = false;
let atomClickHandled = false;
function enableInteraction() {
  if (interactive) return;
  interactive = true;
  v.setClickable({}, true, function (atom) {
    atomClickHandled = true;
    if (S.mode === "measure" && !isMinimal()) measureClick(atom); else toggleResidue(atom);
  });
  v.setHoverable({}, true,
    function (atom) {
      if (isMinimal()) return;
      if (!atom.hLabel) atom.hLabel = v.addLabel(`${atom.resn} ${atom.resi}:${atom.chain} · ${atom.atom}`,
        { position: atom, backgroundColor: "#111827", backgroundOpacity: 0.88, fontColor: "white", fontSize: 11, borderThickness: 0 });
    },
    function (atom) { if (atom.hLabel) { v.removeLabel(atom.hLabel); delete atom.hLabel; } }
  );
}

// Defer until the viewer's own click handler has had a chance to mark atom hits.
// Clicking empty canvas clears the focused residue and restores the full model framing.
$("stage").addEventListener("click", event => {
  if (event.target.closest(".ov, #orientation")) return;
  setTimeout(() => {
    const hitAtom = atomClickHandled;
    const dragged = pointerDragged;
    atomClickHandled = false;
    pointerDragged = false;
    if (!hitAtom && !dragged) clearSelectionAndReset();
  }, 0);
});

/* pause auto-rotate while the user drags, resume shortly after */
let resumeT = null;
let pointerOrigin = null;
let pointerDragged = false;
$("stage").addEventListener("pointerdown", event => {
  pointerOrigin = { x: event.clientX, y: event.clientY };
  pointerDragged = false;
  if (S.spin) { v.spin(false); clearTimeout(resumeT); }
});
window.addEventListener("pointermove", event => {
  if (!pointerOrigin || pointerDragged) return;
  pointerDragged = Math.hypot(event.clientX - pointerOrigin.x, event.clientY - pointerOrigin.y) > 5;
});
window.addEventListener("pointerup", () => {
  pointerOrigin = null;
  if (S.spin) { clearTimeout(resumeT); resumeT = setTimeout(() => { if (S.spin) v.spin("y", S.speed); }, 1500); }
});
window.addEventListener("pointercancel", () => { pointerOrigin = null; });

/* ---------------- toolbar wiring ---------------- */
$("rep").onchange = e => { S.rep = e.target.value; applyStyle(); applySurface(); renderLegend(); };
$("col").onchange = e => { S.col = e.target.value; applyStyle(); applySurface(); renderLegend(); };
function setMode(m) {
  S.mode = m; S.meas = [];
  $("bModeSel").classList.toggle("on", m === "select");
  $("bModeMeas").classList.toggle("on", m === "measure");
  $("v").style.cursor = m === "measure" ? "crosshair" : "default";
}
$("bModeSel").onclick = () => { setMode("select"); note("", 0); };
$("bModeMeas").onclick = () => { setMode("measure"); note("click two atoms to measure", 2500); };
setMode("select");

[
  ["bSpin",  "spin",   applySpin],
  ["bWire",  "wire",   () => { applyStyle(); applySurface(); }],
  ["bAxes",  "axes",   applyAxes],
  ["bLegend","legend", renderLegend],
  ["bLig",   "lig",    () => { applyStyle(); renderLegend(); }],
  ["bWat",   "water",  () => { applyStyle(); renderLegend(); }],
  ["bPocket","pocket", () => { applyStyle(); renderLegend(); }],
].forEach(([id, key, fn]) => {
  const b = $(id);
  b.classList.toggle("on", !!S[key]);
  b.onclick = () => {
    if ((key === "pocket" || key === "lig") && !S.hasLig) { note("no ligand in this structure", 2500); return; }
    S[key] = !S[key]; b.classList.toggle("on", S[key]); fn();
  };
});

$("bClear").onclick = clearAll;
$("bFocus").onclick = () => {
  const ks = Object.values(S.sel);
  if (!ks.length) v.zoomTo({}, 600); else v.zoomTo({ or: ks.map(o => ({ chain: o.chain, resi: o.resi })) }, 600);
};
$("bReset").onclick = () => { if (S.view0) v.setView(S.view0); else v.zoomTo(); v.render(); };
$("bShot").onclick = () => {
  const uri = v.pngURI();
  try { const a = document.createElement("a"); a.href = uri; a.download = (CFG.pdbId || "structure") + ".png";
        document.body.appendChild(a); a.click(); a.remove(); }
  catch (e) { window.open(uri, "_blank"); }
};
$("bFull").onclick = () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else if (wrap.requestFullscreen) wrap.requestFullscreen().catch(() => note("fullscreen blocked by the browser", 3000));
};
new ResizeObserver(() => { v.resize(); v.render(); }).observe($("stage"));

/* Minimal view keeps residue selection active; fullscreen adds the extended controls and panels.
   Leaving fullscreen returns to the compact view and clears selections. */
function syncFullscreen() {
  if (!CFG.minimal) return;
  const full = document.fullscreenElement === wrap || document.webkitFullscreenElement === wrap;
  wrap.classList.toggle("minimal", !full);
  if (S.nAtoms) { if (full) enableInteraction(); else clearAll(); }
  v.resize(); v.render();
}
["fullscreenchange", "webkitfullscreenchange"].forEach(ev => document.addEventListener(ev, syncFullscreen));

/* ---------------- icons + tooltips ---------------- */
if (window.lucide) lucide.createIcons();
else document.querySelectorAll("[data-label]").forEach(b => { b.textContent = b.dataset.label; });   // offline fallback

const tip = $("tip");
function showTip(el) {
  const parts = el.getAttribute("data-tip").split("|");
  tip.innerHTML = `<b>${esc(parts[0])}</b>${parts[1] ? esc(parts[1]) : ""}`;
  tip.classList.add("show");
  const r = el.getBoundingClientRect(), tw = tip.offsetWidth, th = tip.offsetHeight;
  const x = Math.max(4, Math.min(r.left + r.width / 2 - tw / 2, window.innerWidth - tw - 4));
  let y = r.bottom + 6; if (y + th > window.innerHeight - 4) y = r.top - th - 6;
  tip.style.left = x + "px"; tip.style.top = y + "px";
}
document.addEventListener("mouseover", e => {
  const el = e.target.closest ? e.target.closest("[data-tip]") : null;
  if (el) showTip(el); else tip.classList.remove("show");
});
document.addEventListener("mousedown", () => tip.classList.remove("show"));
document.documentElement.addEventListener("mouseleave", () => tip.classList.remove("show"));

/* ---------------- load ---------------- */
function onLoaded() {
  const atoms = v.selectedAtoms({});
  if (!atoms.length) { S.base = "Could not load structure"; setStatus(); return; }
  const res = {}, ligs = {}; let nProt = 0, nRes = 0, bmin = 1e9, bmax = -1e9;
  atoms.forEach(a => {
    if (!a.hetflag) {
      nProt++;
      const k = a.chain + "|" + a.resi + (a.icode || "");
      if (!res[k]) { res[k] = 1; nRes++; }
      const r = S.range[a.chain];
      if (!r) S.range[a.chain] = [a.resi, a.resi]; else { if (a.resi < r[0]) r[0] = a.resi; if (a.resi > r[1]) r[1] = a.resi; }
      if (S.chains.indexOf(a.chain) < 0) S.chains.push(a.chain);
      if (typeof a.b === "number") { if (a.b < bmin) bmin = a.b; if (a.b > bmax) bmax = a.b; }
      if (a.ss === "h" || a.ss === "s") S.hasSS = true;
    } else if (!isWater(a)) ligs[a.resn] = 1;
  });
  if (nProt === 0) SEL_PROT = {};
  S.nAtoms = atoms.length; S.nProt = nProt; S.nRes = nRes;
  S.bmin = bmin > bmax ? 0 : bmin; S.bmax = bmin > bmax ? 1 : bmax;
  S.ligNames = Object.keys(ligs); S.hasLig = S.ligNames.length > 0;
  $("bPocket").disabled = !S.hasLig;

  const ext = $3Dmol.getExtent(atoms);
  S.min = { x: ext[0][0], y: ext[0][1], z: ext[0][2] }; S.max = { x: ext[1][0], y: ext[1][1], z: ext[1][2] };
  S.radius = Math.max(5, Math.hypot(S.max.x - S.min.x, S.max.y - S.min.y, S.max.z - S.min.z) / 2);

  S.base = `Structure  ·  ${S.nAtoms.toLocaleString()} atoms  ·  ${nRes} residues  ·  ${S.chains.length || 1} chain(s)` +
           (S.hasLig ? `  ·  ligand: ${S.ligNames.slice(0, 3).join(", ")}` : "");
  setStatus();
  enableInteraction();
  applyStyle(); applySurface();
  v.zoomTo(); S.view0 = v.getView();
  applyAxes(); applySpin(); renderLegend(); renderInfo(null); v.render();
}

renderInfo(null); renderLegend();
if (CFG.pdbText) { v.addModel(CFG.pdbText, CFG.fmt); onLoaded(); }
else {
  $3Dmol.download("pdb:" + CFG.pdbId, v, {}, onLoaded);
  setTimeout(() => { if (!S.nAtoms) { S.base = "Loading is taking long – check the PDB id / network"; setStatus(); } }, 10000);
}
})();
