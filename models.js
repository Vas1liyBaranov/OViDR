// Модели оборудования собираются из примитивов A-Frame по описанию в models.json.
// Каждая деталь: t — тип, p — положение, s — размеры, m — материал, r — поворот (градусы),
// c — класс (lamp — сигнальная лампа, card — карточка с данными), a/b — концы стержня.
// Координаты модели: x вдоль станка, y вверх, z к зрителю, сторона маркера = 1.

const MATERIALS = {
  paint:         "color: #7f9486; roughness: 0.55; metalness: 0.15",
  paintDark:     "color: #56645b; roughness: 0.6; metalness: 0.1",
  paintMill:     "color: #7d93a6; roughness: 0.55; metalness: 0.15",
  paintMillDark: "color: #566a7c; roughness: 0.6; metalness: 0.1",
  steel:         "color: #b9bec4; roughness: 0.3; metalness: 0.85",
  brightSteel:   "color: #e4e8ec; roughness: 0.2; metalness: 0.9",
  alu:           "color: #d6dadf; roughness: 0.4; metalness: 0.7",
  table:         "color: #9aa0a6; roughness: 0.35; metalness: 0.7",
  dark:          "color: #2b2f33; roughness: 0.6; metalness: 0.2",
  black:         "color: #151515; roughness: 0.5",
  grey:          "color: #8a8f94; roughness: 0.5",
  frame:         "color: #3a3d40; roughness: 0.45; metalness: 0.5",
  bed:           "color: #1f1f1f; roughness: 0.3",
  red:           "color: #c0392b; roughness: 0.4",
  green:         "color: #27ae60; roughness: 0.4",
  orange:        "color: #ff7a1a; roughness: 0.5",
  brass:         "color: #b8963e; roughness: 0.35; metalness: 0.8",
  screen:        "color: #1e5f9f; emissive: #1e5f9f; emissiveIntensity: 0.6",
  tube:          "color: #f0f0f0; opacity: 0.85; transparent: true",
  lamp:          "color: #2e9e4f; emissive: #2e9e4f; emissiveIntensity: 0.5",
  card:          "shader: flat; color: #ffffff"
};

// поворот, который направляет ось Y цилиндра от точки a к точке b (порядок осей A-Frame YXZ)
function rodTransform(a, b) {
  const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const len = Math.hypot(d[0], d[1], d[2]);
  const tilt = Math.acos(d[1] / len) * 180 / Math.PI;
  const turn = Math.atan2(d[0], d[2]) * 180 / Math.PI;
  return {
    position: (a[0] + b[0]) / 2 + " " + (a[1] + b[1]) / 2 + " " + (a[2] + b[2]) / 2,
    rotation: tilt + " " + turn + " 0",
    height: len
  };
}

function buildPart(parent, p, skipCard) {
  if (skipCard && p.c === "card") return;
  const s = p.s;
  let tag, attrs;
  if (p.t === "rod") {
    const tr = rodTransform(p.a, p.b);
    tag = "a-cylinder";
    attrs = { position: tr.position, rotation: tr.rotation, radius: s[0], height: tr.height,
              "segments-radial": 10 };
  } else {
    tag = "a-" + p.t;
    attrs = { position: p.p.join(" ") };
    if (p.r) attrs.rotation = p.r.join(" ");
    if (p.t === "box")      Object.assign(attrs, { width: s[0], height: s[1], depth: s[2] });
    if (p.t === "cylinder") Object.assign(attrs, { radius: s[0], height: s[1], "segments-radial": 24 });
    if (p.t === "cone")     Object.assign(attrs, { "radius-bottom": s[0], "radius-top": s[1], height: s[2] });
    if (p.t === "torus")    Object.assign(attrs, { radius: s[0], "radius-tubular": s[1], "segments-tubular": 32 });
    if (p.t === "sphere")   Object.assign(attrs, { radius: s[0] });
    if (p.t === "plane")    Object.assign(attrs, { width: s[0], height: s[1] });
  }
  const el = document.createElement(tag);
  for (const k in attrs) el.setAttribute(k, attrs[k]);
  el.setAttribute("material", MATERIALS[p.m] || MATERIALS.grey);
  if (p.c) el.classList.add(p.c);
  parent.appendChild(el);
}

// строит все модели: для каждого id в models.json ищет контейнер "#model-<id> .body"
async function loadModels(skipCard) {
  const data = await fetch("models.json", { cache: "no-store" }).then((r) => r.json());
  for (const id in data) {
    const body = document.querySelector("#model-" + id + " .body");
    if (body) data[id].forEach((p) => buildPart(body, p, skipCard));
  }
  return data;
}
