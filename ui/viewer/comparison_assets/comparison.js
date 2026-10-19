(function () {
  const C = CFG;
  const $ = id => document.getElementById(id);
  const esc = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const tokenColor = token => C.tokenColors[token] || "#aab4bd";
  const states = [];
  let selectedIndex = null;
  let synchronizing = false;
  let syncCameras = true;
  let autoRotate = false;
  let representation = "trace";
  let colorMode = "token";
  const hiddenTokens = new Set();
  let pointerDragged = false;
  let atomClickHandled = false;
  let pointerStart = null;

  if (C.dark) $("compare").classList.add("dark");
  if (window.lucide) lucide.createIcons();
  $("title-ref").textContent = C.models[0].title;
  $("title-query").textContent = C.models[1].title;

  const bg = C.dark ? "#090807" : "#ffffff";
  const viewerOptions = {backgroundColor: bg, antialias: true, disableFog: true};
  const views = [
    $3Dmol.createViewer("view-ref", viewerOptions),
    $3Dmol.createViewer("view-query", viewerOptions),
  ];

  function pdbFromJson(model) {
    // Build an in-memory CA-only model from JSON coordinates. No PDB file is requested or opened.
    return model.coords.map((p, i) => {
      const serial = String(i + 1).padStart(5, " ");
      const resi = String(i + 1).padStart(4, " ");
      return `ATOM  ${serial}  CA  UNK A${resi}    ${Number(p[0]).toFixed(3).padStart(8, " ")}${Number(p[1]).toFixed(3).padStart(8, " ")}${Number(p[2]).toFixed(3).padStart(8, " ")}  1.00  0.00          C `;
    }).join("\n") + "\nTER\nEND\n";
  }

  function colorFor(model, index) {
    if (colorMode === "position") {
      const t = index / Math.max(1, model.coords.length - 1);
      const a = t < 0.5 ? 0x2563eb : 0xffffff;
      const b = t < 0.5 ? 0xffffff : 0xdc2626;
      const p = t < 0.5 ? t * 2 : (t - 0.5) * 2;
      const channel = shift => Math.round(((a >> shift) & 255) * (1 - p) + ((b >> shift) & 255) * p);
      return (channel(16) << 16) | (channel(8) << 8) | channel(0);
    }
    return parseInt(tokenColor(model.tokens[index]).slice(1), 16);
  }

  function drawTrace(state) {
    state.lines.forEach(shape => state.viewer.removeShape(shape));
    state.lines = [];
    if (representation !== "trace") return;
    const {coords, tokens} = state.model;
    for (let i = 0; i < coords.length - 1; i++) {
      if (hiddenTokens.has(tokens[i]) || hiddenTokens.has(tokens[i + 1])) continue;
      const selectedSegment = selectedIndex === i ||
        (selectedIndex === coords.length - 1 && i === coords.length - 2);
      // Cylinders render with a true 3D radius, avoiding WebGL's thin-line width limits.
      state.lines.push(state.viewer.addCylinder({
        start: {x: coords[i][0], y: coords[i][1], z: coords[i][2]},
        end: {x: coords[i + 1][0], y: coords[i + 1][1], z: coords[i + 1][2]},
        color: selectedSegment ? 0xff00d4 : colorFor(state.model, i),
        radius: selectedSegment ? 0.3 : 0.22,
        clickable: true,
        callback: () => {
          atomClickHandled = true;
          selectResidue(i);
        },
      }));
    }
  }

  function applyModelStyle(state) {
    state.viewer.setStyle({}, {sphere: {
      radius: representation === "trace" ? 0.18 : 0.48,
      colorfunc: atom => {
        const index = Math.max(0, Number(atom.resi) - 1);
        return representation === "beads" && selectedIndex === index
          ? 0xff00d4 : colorFor(state.model, index);
      },
    }});
    state.model.tokens.forEach((token, index) => {
      if (hiddenTokens.has(token)) state.viewer.setStyle({resi: index + 1}, {});
    });
    drawTrace(state);
    state.viewer.render();
  }

  function clearHighlight() {
    states.forEach(state => {
      if (state.selectionLabel) state.viewer.removeLabel(state.selectionLabel);
      state.selectionLabel = null;
    });
  }

  function selectResidue(index) {
    const sharedCount = Math.min(C.models[0].coords.length, C.models[1].coords.length);
    if (!Number.isInteger(index) || index < 0 || index >= sharedCount) return;
    selectedIndex = index;
    clearHighlight();
    states.forEach(state => {
      applyModelStyle(state);
      const p = state.model.coords[index];
      const token = state.model.tokens[index] || "Unknown";
      state.selectionLabel = state.viewer.addLabel(`Residue - ${index}, Token: ${token}`, {
        position: {x:p[0], y:p[1], z:p[2]}, fontSize: 11,
        fontColor: "#21150f", backgroundColor: "#d89267",
        backgroundOpacity: 0.94, borderThickness: 0, inFront: true,
      });
      state.viewer.render();
    });

  }

  function clearSelection() {
    selectedIndex = null;
    clearHighlight();
    states.forEach(state => {
      applyModelStyle(state);
      state.viewer.render();
    });
  }

  function onCameraChange(sourceIndex, view) {
    if (!syncCameras || synchronizing) return;
    synchronizing = true;
    const other = states[1 - sourceIndex].viewer;
    other.setView(view || states[sourceIndex].viewer.getView());
    other.render();
    requestAnimationFrame(() => { synchronizing = false; });
  }

  function updateAxis(state, view) {
    const q = (view || state.viewer.getView()).slice(4, 8);
    const [qx, qy, qz, qw] = q;
    const axes = [["x", [1, 0, 0]], ["y", [0, 1, 0]], ["z", [0, 0, 1]]];
    axes.forEach(([axis, [x, y, z]]) => {
      const tx = 2 * (qy * z - qz * y);
      const ty = 2 * (qz * x - qx * z);
      const tz = 2 * (qx * y - qy * x);
      const rx = x + qw * tx + qy * tz - qz * ty;
      const ry = y + qw * ty + qz * tx - qx * tz;
      const rz = z + qw * tz + qx * ty - qy * tx;
      const x2 = 40 + rx * 25;
      const y2 = 40 - ry * 25;
      const line = $(`${state.axisPrefix}-axis-${axis}`);
      const label = $(`${state.axisPrefix}-label-${axis}`);
      const opacity = 0.3 + 0.7 * ((rz + 1) / 2);
      line.setAttribute("x2", x2.toFixed(2));
      line.setAttribute("y2", y2.toFixed(2));
      line.style.opacity = String(opacity);
      label.setAttribute("x", (40 + rx * 31).toFixed(2));
      label.setAttribute("y", (40 - ry * 31 + 3).toFixed(2));
      label.style.opacity = String(opacity);
    });
  }

  function updateAxisVisibility() {
    $("axis-ref").style.display = "block";
    $("axis-query").style.display = syncCameras ? "none" : "block";
    $("compare").classList.toggle("linked", syncCameras);
  }

  C.models.forEach((model, index) => {
    const viewer = views[index];
    viewer.addModel(pdbFromJson(model), "pdb");
    const atoms = viewer.selectedAtoms({});
    const state = {viewer, model, lines: [], selectionLabel: null,
      axisPrefix: index === 0 ? "ref" : "query"};
    states.push(state);
    applyModelStyle(state);
    viewer.setClickable({}, true, atom => {
      atomClickHandled = true;
      selectResidue(Number(atom.resi) - 1);
    });
    viewer.setHoverable({}, true, atom => {
      if (!atom.compareHover) {
        const index = Number(atom.resi) - 1;
        atom.compareHover = viewer.addLabel(`Residue - ${index}, Token: ${esc(model.tokens[index] || "Unknown")}`, {
          position: atom, fontSize: 10, fontColor: C.dark ? "#e8f1f7" : "#fff",
          backgroundColor: C.dark ? "#211d1a" : "#4e3427", backgroundOpacity: 0.92,
          borderThickness: 0,
        });
      }
    }, atom => {
      if (atom.compareHover) { viewer.removeLabel(atom.compareHover); delete atom.compareHover; }
    });
    viewer.zoomTo({}, 0);
    viewer.render();
    viewer.setViewChangeCallback(view => {
      updateAxis(state, view);
      onCameraChange(index, view);
    });
    updateAxis(state, viewer.getView());
    state.atomCount = atoms.length;

    const canvas = $(index === 0 ? "view-ref" : "view-query");
    canvas.addEventListener("pointerdown", event => {
      pointerStart = [event.clientX, event.clientY];
      pointerDragged = false;
    });
    canvas.addEventListener("pointermove", event => {
      if (!pointerStart) return;
      if (Math.hypot(event.clientX - pointerStart[0], event.clientY - pointerStart[1]) > 5) pointerDragged = true;
    });
    canvas.addEventListener("pointerup", () => { pointerStart = null; });
    canvas.addEventListener("click", () => setTimeout(() => {
      const hit = atomClickHandled;
      atomClickHandled = false;
      const dragged = pointerDragged;
      pointerDragged = false;
      if (!hit && !dragged) clearSelection();
    }, 0));
  });
  updateAxisVisibility();

  function renderLegend() {
    $("legend").innerHTML = colorMode === "token"
      ? C.tokenNames.map((token, index) => `<button type="button" class="legend-item${hiddenTokens.has(token) ? " is-hidden" : ""}" data-token-index="${index}" aria-pressed="${!hiddenTokens.has(token)}" title="Toggle ${esc(token)} residues in both models"><i class="legend-swatch" style="background:${tokenColor(token)}"></i>${esc(token)}</button>`).join("")
      : '<span class="legend-item">N-terminus</span><span class="position-gradient"></span><span class="legend-item">C-terminus</span>';
  }
  $("legend").addEventListener("click", event => {
    const button = event.target.closest("button[data-token-index]");
    if (!button) return;
    const token = C.tokenNames[Number(button.dataset.tokenIndex)];
    if (hiddenTokens.has(token)) hiddenTokens.delete(token);
    else hiddenTokens.add(token);
    if (selectedIndex !== null && (hiddenTokens.has(C.models[0].tokens[selectedIndex]) ||
        hiddenTokens.has(C.models[1].tokens[selectedIndex]))) clearSelection();
    renderLegend();
    states.forEach(applyModelStyle);
  });
  renderLegend();

  function setMode(mode) {
    representation = mode;
    $("trace").classList.toggle("active", mode === "trace");
    $("beads").classList.toggle("active", mode === "beads");
    states.forEach(applyModelStyle);
    if (selectedIndex !== null) selectResidue(selectedIndex);
  }
  $("trace").onclick = () => setMode("trace");
  $("beads").onclick = () => setMode("beads");
  $("sync").onclick = () => {
    syncCameras = !syncCameras;
    $("sync").classList.toggle("active", syncCameras);
    $("sync").title = syncCameras ? "Synchronized views on" : "Synchronized views off";
    updateAxisVisibility();
  };
  $("spin").onclick = () => {
    autoRotate = !autoRotate;
    $("spin").classList.toggle("active", autoRotate);
    views.forEach(viewer => autoRotate ? viewer.spin("y", 0.25) : viewer.spin(false));
  };
  $("color").onclick = () => {
    colorMode = colorMode === "token" ? "position" : "token";
    $("color-label").textContent = colorMode === "token" ? "Tokens" : "Position";
    renderLegend();
    states.forEach(applyModelStyle);
    if (selectedIndex !== null) selectResidue(selectedIndex);
  };
  $("fit").onclick = () => views.forEach(viewer => { viewer.zoomTo({}, 500); viewer.render(); });
  $("clear").onclick = clearSelection;

  const resize = new ResizeObserver(() => views.forEach(viewer => { viewer.resize(); viewer.render(); }));
  resize.observe($("compare"));
  window.addEventListener("beforeunload", () => resize.disconnect());
})();
