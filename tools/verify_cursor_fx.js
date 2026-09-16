// 鼠标拖尾特效（site/js/cursorFx.js）的确定性自检
//
// 为什么不用浏览器测：无头 Chrome 在虚拟时间下 requestAnimationFrame 几乎不跑
// （实测 28 次移动只跑了 2 帧），粒子还没画出来就截图，看到的全是假象。
// 所以这里用 Node 桩环境给画布 API 打点，手动喂事件、手动推帧，结果可重复。
//
// 用法： node tools/verify_cursor_fx.js      （退出码 0 = 通过）
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const CODE = fs.readFileSync(path.join(__dirname, "..", "site", "js", "cursorFx.js"), "utf8");

function makeCtx(stat) {
  const rec = (name) => () => { stat[name] = (stat[name] || 0) + 1; };
  return {
    setTransform() {}, clearRect: rec("clearRect"), save() {}, restore() {},
    beginPath: rec("beginPath"), moveTo: rec("moveTo"), lineTo: rec("lineTo"),
    arc: rec("arc"), bezierCurveTo: rec("bezierCurveTo"), fillRect: rec("fillRect"),
    stroke: rec("stroke"), fill: rec("fill"), drawImage: rec("drawImage"),
    createRadialGradient: () => ({ addColorStop() {} }),
    translate() {}, rotate() {},
    set globalAlpha(v) { stat.lastAlpha = v; },
    get globalAlpha() { return stat.lastAlpha; },
    set fillStyle(v) {}, set strokeStyle(v) {}, set lineWidth(v) {}, set lineCap(v) {},
  };
}

function run({ reducedMotion }) {
  const clock = { now: 1000 };
  const listeners = {};
  const rafQueue = [];
  let canvasCount = 0;
  let mainCanvas = null;   // 特效那张全屏画布（第一个创建的），后面还会创建光点贴图小画布

  function makeCanvas() {
    const stat = {};
    canvasCount++;
    const canvas = { width: 0, height: 0, style: {}, stat, getContext: () => makeCtx(stat), setAttribute() {} };
    if (!mainCanvas) mainCanvas = canvas;
    return canvas;
  }

  const document = {
    documentElement: { appendChild() {} },
    createElement(tag) {
      if (tag === "canvas") return makeCanvas();
      return { style: {}, setAttribute() {}, appendChild() {} };
    },
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
  };

  const window = {
    matchMedia: () => ({ matches: Boolean(reducedMotion) }),
    devicePixelRatio: 1,
    innerWidth: 1200,
    innerHeight: 800,
    addEventListener() {},
    requestAnimationFrame(cb) { rafQueue.push(cb); return rafQueue.length; },
  };

  const sandbox = {
    window, document, console,
    performance: { now: () => clock.now },
    requestAnimationFrame: (cb) => window.requestAnimationFrame(cb),
  };
  vm.createContext(sandbox);
  vm.runInContext(CODE, sandbox);

  const fire = (type, x, y) => (listeners[type] || []).forEach((fn) => fn({ clientX: x, clientY: y }));

  function frame() {
    const cb = rafQueue.shift();
    if (!cb) return null;
    clock.now += 16.7;
    if (mainCanvas) for (const k of Object.keys(mainCanvas.stat)) delete mainCanvas.stat[k];
    cb(clock.now);
    return mainCanvas ? mainCanvas.stat : null;
  }

  function frames(n) {
    let last = null;
    for (let i = 0; i < n; i++) last = frame() || last;
    return last;
  }

  return { clock, fire, frame, frames, canvasCount, getCanvas: () => mainCanvas };
}

const fails = [];
const check = (ok, msg) => { if (!ok) fails.push(msg); };

// ---- 1. 减少动态效果时不启动 ----
{
  const env = run({ reducedMotion: true });
  check(env.canvasCount === 0, "开了「减少动态效果」还创建了画布");
  console.log("① 减少动态效果：画布数 =", env.canvasCount, env.canvasCount === 0 ? "✓ 不启动" : "✗");
}

// ---- 2. 移动轨迹能撒出粒子并画出来 ----
{
  const env = run({ reducedMotion: false });
  let x = 120, y = 160;
  for (let i = 0; i < 30; i++) {
    x += 24; y += 8;
    env.clock.now += 30;
    env.fire("mousemove", x, y);
  }
  const stat = env.frames(2);
  console.log("② 30 次移动后一帧的画法调用：", JSON.stringify(stat));
  check(stat && stat.drawImage >= 15, "移动后画出来的光点太少（drawImage=" + (stat && stat.drawImage) + "）");
  check(stat && stat.stroke >= 5, "移动后没画出描边类粒子（stroke=" + (stat && stat.stroke) + "）");
}

// ---- 3. 点击要迸出涟漪 + 火星 ----
{
  const env = run({ reducedMotion: false });
  env.clock.now += 100;
  env.fire("pointerdown", 400, 300);
  const stat = env.frames(1);
  console.log("③ 点击一帧的画法调用：", JSON.stringify(stat));
  check(stat && stat.arc >= 2, "点击没画出剑气涟漪（arc=" + (stat && stat.arc) + "）");
  check(stat && stat.drawImage >= 10, "点击没迸出火星（drawImage=" + (stat && stat.drawImage) + "）");
}

// ---- 4. 粒子总数有上限 ----
{
  const env = run({ reducedMotion: false });
  for (let i = 0; i < 900; i++) {
    env.clock.now += 30;
    env.fire("mousemove", 200 + (i % 300), 200 + (i % 120));
  }
  const stat = env.frames(1);
  console.log("④ 900 次移动后一帧：drawImage =", stat.drawImage, "（上限 420）");
  check(stat.drawImage <= 420, "粒子数超过上限：" + stat.drawImage);
}

// ---- 5. 静止一会儿要浮现阵法圆环 ----
{
  const env = run({ reducedMotion: false });
  env.clock.now += 50;
  env.fire("mousemove", 500, 400);
  env.frames(2);
  env.clock.now += 900;          // 静止 900ms
  env.frames(30);                 // 让粒子散掉
  env.clock.now += 300;
  const stat = env.frames(1);
  console.log("⑤ 静止后一帧：arc =", stat.arc, " stroke =", stat.stroke);
  check(stat.arc >= 2, "静止后没有浮现阵法圆环（arc=" + stat.arc + "）");
}

console.log("");
if (fails.length) {
  console.log("失败项：");
  fails.forEach((f) => console.log("  ✗ " + f));
  process.exit(1);
}
console.log("全部通过 ✓");


