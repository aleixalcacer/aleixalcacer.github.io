// Rotating convex hull: vertices are "archetypes", inner points are convex mixtures of them.
// Drag to rotate. Without JS the static triangle in index.html is shown instead.
const svg = document.querySelector(".simplex");
if (svg) {
  const V = [[2, -36, 3], [30, -14, 8], [10, -16, -28], [-26, -12, -10],
             [-12, -14, 27], [26, 16, -14], [-30, 14, 6], [-2, 38, -2]];
  const mean = (idx) => [0, 1, 2].map((k) => idx.reduce((s, i) => s + V[i][k], 0) / idx.length);
  const mixOf = [0, 5, 6]; // the highlighted point is a mixture of these three archetypes
  const P = [mean(mixOf), mean([1, 2, 4]), mean([3, 4, 7]), mean([1, 5, 7]),
             mean([0, 2, 3]), mean([4, 5, 6]), mean([2, 6, 7])];
  let angle = 0.6;
  let tilt = 0.5;
  let last = null;

  // Hull edges: a triple of vertices is a face if every other vertex lies on one side of its plane.
  const sub = (a, b) => a.map((x, i) => x - b[i]);
  const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const hull = new Set();
  V.forEach((a, i) => V.forEach((b, j) => V.forEach((c, k) => {
    if (i >= j || j >= k) return;
    const n = cross(sub(b, a), sub(c, a));
    const side = V.map((p) => dot(n, sub(p, a)));
    if (side.every((s) => s >= -1e-6) || side.every((s) => s <= 1e-6)) {
      [[i, j], [j, k], [i, k]].forEach((e) => hull.add(e.join()));
    }
  })));

  const make = (tag, cls) => {
    const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
    el.setAttribute("class", cls);
    svg.append(el);
    return el;
  };
  svg.setAttribute("viewBox", "-48 -48 96 96");
  svg.replaceChildren();
  const edges = [...hull].map((e) => [make("line", "hull"), ...e.split(",").map(Number)]);
  const mixes = mixOf.map((i) => [make("line", "mix"), i]);
  const points = P.map(() => make("circle", "p"));
  const verts = V.map(() => make("circle", "v"));

  const rotate = ([x, y, z]) => {
    const c = Math.cos(angle), s = Math.sin(angle);
    [x, z] = [x * c + z * s, -x * s + z * c];
    const ct = Math.cos(tilt), st = Math.sin(tilt);
    return [x, y * ct - z * st, y * st + z * ct];
  };
  const fade = (el, z) => el.setAttribute("opacity", Math.min(1, Math.max(0.2, 0.6 + z / 70))); // far = faint
  const line = (el, a, b) => {
    fade(el, (a[2] + b[2]) / 2);
    el.setAttribute("x1", a[0]); el.setAttribute("y1", a[1]);
    el.setAttribute("x2", b[0]); el.setAttribute("y2", b[1]);
  };
  const dotAt = (el, q, r) => {
    fade(el, q[2]);
    el.setAttribute("cx", q[0]); el.setAttribute("cy", q[1]);
    el.setAttribute("r", r * (1 + q[2] / 120));
  };
  const draw = () => {
    const v = V.map(rotate), p = P.map(rotate);
    edges.forEach(([el, a, b]) => line(el, v[a], v[b]));
    mixes.forEach(([el, i]) => line(el, p[0], v[i]));
    points.forEach((el, i) => dotAt(el, p[i], 2));
    verts.forEach((el, i) => dotAt(el, v[i], 3));
  };

  svg.addEventListener("pointerdown", (e) => { last = [e.clientX, e.clientY]; svg.setPointerCapture(e.pointerId); });
  svg.addEventListener("pointermove", (e) => {
    if (last === null) return;
    angle += (e.clientX - last[0]) * 0.02;
    tilt += (e.clientY - last[1]) * 0.02;
    last = [e.clientX, e.clientY];
    draw();
  });
  svg.addEventListener("pointerup", () => { last = null; });
  svg.addEventListener("pointercancel", () => { last = null; });

  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const spin = () => {
    if (last === null) { angle += 0.005; draw(); }
    requestAnimationFrame(spin);
  };
  draw();
  if (!still) spin();
}
