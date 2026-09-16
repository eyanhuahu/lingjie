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
    arc: rec("arc"), closePath: rec("closePath"), fillRect: rec("fillRect"),
    stroke: rec("stroke"), fill: rec("fill"), drawImage: rec("drawImage"),
    createRadialGradient: () => ({ addColorStop() {} }),
    createLinearGradient: () => ({ addColorStop() {} }),
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
  let mainCanvas = null;

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
    let lastStat = null;
    for (let i = 0; i < n; i++) lastStat = frame() || lastStat;
    return lastStat;
  }

  return { clock, fire, frame, frames, canvasCount };
}

const fails = [];
const check = (ok, msg) => { if (!ok) fails.push(msg); };

// ---- 1. 减少动态效果时不启动 ----
{
  const env = run({ reducedMotion: true });
  check(env.canvasCount === 0, "开了「减少动态效果」还创建了画布");
  console.log("① 减少动态效果：画布数 =", env.canvasCount, env.canvasCount === 0 ? "✓ 不启动" : "✗");
}

// ---- 2. 连续移动：撒出来的是四角星（渐变星体 + 光晕）----
{
  const env = run({ reducedMotion: false });
  let x = 120, y = 160;
  for (let i = 0; i < 30; i++) {
    x += 24; y += 8;
    env.clock.now += 16;
    env.fire("mousemove", x, y);
  }
  const stat = env.frames(1);
  console.log("② 30 次移动后一帧：", JSON.stringify(stat));
  check(stat && stat.drawImage >= 20, "星星太少（drawImage=" + (stat && stat.drawImage) + "）");
  check(stat && stat.fill >= 10, "没有画出星体（fill=" + (stat && stat.fill) + "）");
  check(stat && stat.closePath >= 10, "星体不是闭合的四角星路径（closePath=" + (stat && stat.closePath) + "）");
}

// ---- 3. 连续移动 + 急转弯都不能断（按距离补插值）----
{
  const env = run({ reducedMotion: false });
  // 先向右 400px、再向上 400px：共 40 次小步移动，转一个直角弯
  let x = 100, y = 500;
  env.clock.now += 16;
  env.fire("mousemove", x, y);
  for (let i = 0; i < 20; i++) { x += 20; env.clock.now += 16; env.fire("mousemove", x, y); }
  for (let i = 0; i < 20; i++) { y -= 20; env.clock.now += 16; env.fire("mousemove", x, y); }
  const stat = env.frames(1);
  // 路径 800px、间距 9px → 大约 88 颗；转弯处若断了会明显少于这个数
  console.log("③ 800px 直角路径后一帧：drawImage =", stat.drawImage, "（期望 ≈ 800/16 = 50）");
  check(stat.drawImage >= 44, "转弯处断了或者没补插值（drawImage=" + stat.drawImage + "）");

  // 单次瞬移（比如鼠标从屏幕外跳进来）要被上限挡住，不能一口气炸出几百颗
  const env2 = run({ reducedMotion: false });
  env2.clock.now += 16;
  env2.fire("mousemove", 100, 400);
  env2.clock.now += 16;
  env2.fire("mousemove", 900, 400);
  const stat2 = env2.frames(1);
  console.log("   单次跨 800px 瞬移：drawImage =", stat2.drawImage, "（上限 maxPerMove=18）");
  check(stat2.drawImage <= 22, "瞬移没有限流（drawImage=" + stat2.drawImage + "）");
}

// ---- 4. 点击要迸发一圈星星 + 涟漪 ----
{
  const env = run({ reducedMotion: false });
  env.clock.now += 100;
  env.fire("pointerdown", 400, 300);
  const stat = env.frames(1);
  console.log("④ 点击一帧：drawImage =", stat.drawImage, " arc =", stat.arc, " fill =", stat.fill);
  check(stat.drawImage >= 12, "点击没迸出星星（drawImage=" + stat.drawImage + "）");
  check(stat.arc >= 1, "点击没有涟漪（arc=" + stat.arc + "）");
}

// ---- 5. 粒子总数有上限 ----
{
  const env = run({ reducedMotion: false });
  for (let i = 0; i < 900; i++) {
    env.clock.now += 16;
    env.fire("mousemove", 100 + (i % 1000), 200 + (i % 300));
  }
  const stat = env.frames(1);
  console.log("⑤ 900 次移动后一帧：drawImage =", stat.drawImage, "（上限 300）");
  check(stat.drawImage <= 300, "粒子数超过上限：" + stat.drawImage);
}

// ---- 6. 星星会自己消失（不能越积越多）----
{
  const env = run({ reducedMotion: false });
  env.clock.now += 16;
  env.fire("mousemove", 300, 300);
  env.clock.now += 16;
  env.fire("mousemove", 360, 320);
  env.frames(1);
  for (let i = 0; i < 200; i++) { env.clock.now += 16.7; env.frame(); }
  const stat = env.frames(1);
  console.log("⑥ 静置 3.3 秒后：list 画法调用 =", stat ? JSON.stringify(stat) : "(空)");
  check(!stat || !stat.drawImage, "星星没有按时消失：" + JSON.stringify(stat));
}

console.log("");
if (fails.length) {
  console.log("失败项：");
  fails.forEach((f) => console.log("  ✗ " + f));
  process.exit(1);
}
console.log("全部通过 ✓");

