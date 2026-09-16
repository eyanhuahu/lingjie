/* 灵界 wiki —— 鼠标拖尾特效（四角闪光星）
 *
 * 参照 bigxian0201/start-home- 的 sparkles.js：鼠标走过撒下**会闪的四角星**。
 * 三条关键差异（前两条是踩坑后改的，第三条是因为本站底色不同）：
 *
 *   ① 撒点改成**按移动距离补插值**，不是按时间节流。
 *      只按时间节流的话，快速移动时两点之间会空一大截，一转弯就断成一节一节；
 *      现在是「每走 SPACING 像素沿路径均匀撒一颗」，多快都是连续一条，转弯也顺。
 *   ② 星星用**线性渐变**（亮心 → 实色 → 略深的边）+ 径向渐变光晕，不是纯色块。
 *   ③ 配色按**米白底色**重新调过：参考站是深色底，白/淡黄星一上去就看不见；
 *      这里白星也给它一条金色边，浅底上才有轮廓。
 *
 * 画布挂在 <html> 下、pointer-events:none —— 不挡点击，也不会被 app.js 重建 body 时删掉。
 * DPR 封顶 2、粒子总数封顶、没东西可画时连清屏都跳过、系统开「减少动态效果」就整个不启动。
 * 想调浓淡/大小/频率，只改下面 CFG 与 STARS 两个表。
 */
(function () {
  "use strict";

  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var CFG = {
    spacing: 16,         // 鼠标每走多少像素撒一颗星（越大越稀）
    maxParticles: 300,   // 粒子总数上限
    maxPerMove: 18,      // 单次移动最多补几颗（防瞬移时炸出几百颗）
    life: [0.9, 2.0],    // 星星寿命（秒）
    size: [3.2, 8.0],    // 星星半径（像素）
    drift: 0.26,         // 散开速度
    rise: 0.18,          // 轻微上浮
    burstCount: 10,      // 点击迸发的星星数
    jitter: 5            // 撒点时的随机偏移，免得排成一条死板的直线
  };

  // 每颗星一组颜色：亮心（白）/ 实色 / 光晕色。
  // 实色**全部是蓝色系**（陛下指定），五种蓝在色相和明度上拉开，撒出来才有层次；
  // 依旧保持低饱和度，不用金色、不用粉紫。边缘仍然是白色描边（见 drawStar）。
  var STARS = [
    { core: "#FFFFFF", body: "#9CCFE0", halo: "#9CCFE0" },   // 淡青蓝
    { core: "#FFFFFF", body: "#A9C8EE", halo: "#A9C8EE" },   // 淡天蓝
    { core: "#FFFFFF", body: "#AEB6E4", halo: "#AEB6E4" },   // 淡靛蓝
    { core: "#FFFFFF", body: "#8FC7D8", halo: "#8FC7D8" },   // 稍深的蓝
    { core: "#FFFFFF", body: "#D3E4F2", halo: "#C9DCEF" }    // 冰蓝白（原来是纯白那档）
  ];

  var TAU = Math.PI * 2;
  var rand = Math.random;
  function pick(a) { return a[Math.floor(rand() * a.length)]; }
  function between(range) { return range[0] + rand() * (range[1] - range[0]); }

  function rgba(hex, alpha) {
    var h = hex.replace("#", "");
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + alpha + ")";
  }

  // ---- 画布 ----
  var canvas = document.createElement("canvas");
  canvas.id = "cursorFxCanvas";
  canvas.setAttribute("aria-hidden", "true");
  canvas.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:9999;";
  document.documentElement.appendChild(canvas);
  var ctx = canvas.getContext("2d");
  var W = 0, H = 0;

  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    canvas.style.width = W + "px";
    canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener("resize", resize);

  // ---- 光晕贴图（预先画好，避免每帧建渐变）----
  var glowCache = {};
  function glowSprite(color) {
    if (glowCache[color]) return glowCache[color];
    var size = 64;
    var c = document.createElement("canvas");
    c.width = c.height = size;
    var g = c.getContext("2d");
    var grd = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    grd.addColorStop(0, rgba(color, 0.75));
    grd.addColorStop(0.32, rgba(color, 0.3));
    grd.addColorStop(1, rgba(color, 0));
    g.fillStyle = grd;
    g.fillRect(0, 0, size, size);
    glowCache[color] = c;
    return c;
  }

  var list = [];
  var rings = [];

  function push(p) {
    list.push(p);
    if (list.length > CFG.maxParticles) list.splice(0, list.length - CFG.maxParticles);
  }

  // 一颗四角星；scale 用于点击时迸发的大星
  function spawnStar(x, y, scale, forceColor) {
    var pal = forceColor || pick(STARS);
    var speed = CFG.drift * (0.4 + rand() * 1.2) * (scale || 1);
    var ang = rand() * TAU;
    push({
      x: x + (rand() - 0.5) * CFG.jitter,
      y: y + (rand() - 0.5) * CFG.jitter,
      vx: Math.cos(ang) * speed,
      vy: Math.sin(ang) * speed - CFG.rise * (0.4 + rand()),
      size: between(CFG.size) * (scale || 1),
      rot: rand() * TAU,
      spin: (rand() - 0.5) * 0.05,
      life: 1,
      decay: 1 / (between(CFG.life) * 60),
      phase: rand() * TAU,
      twinkle: 0.06 + rand() * 0.09,
      pal: pal
    });
  }

  // 点击：一圈星星 + 中心几颗大星 + 一圈光晕涟漪
  function spawnBurst(x, y) {
    rings.push({ x: x, y: y, r: 4, life: 1 });
    for (var i = 0; i < CFG.burstCount; i++) {
      var a = (i / CFG.burstCount) * TAU + rand() * 0.3;
      var d = 4 + rand() * 10;
      spawnStar(x + Math.cos(a) * d, y + Math.sin(a) * d, 0.8 + rand() * 0.4);
    }
    for (var j = 0; j < 3; j++) spawnStar(x, y, 1.5 + rand() * 0.5);
  }

  // ---- 画：四角星 + 渐变 ----
  function starPath(cx, cy, r, rot) {
    var inner = r * 0.42;
    ctx.beginPath();
    for (var i = 0; i < 8; i++) {
      var rad = i % 2 === 0 ? r : inner;
      var a = (i * Math.PI) / 4 + rot;
      var px = cx + Math.cos(a) * rad;
      var py = cy + Math.sin(a) * rad;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.closePath();
  }

  function drawStar(p) {
    var tw = 0.55 + 0.45 * Math.sin(p.phase);          // 闪烁
    var fade = Math.max(0, Math.min(1, p.life));
    var alpha = fade * (0.5 + 0.5 * tw);
    if (alpha <= 0.01) return;
    var r = p.size * (0.72 + 0.42 * tw);

    // 光晕（用星体自己的淡色）
    var halo = glowSprite(p.pal.halo);
    ctx.globalAlpha = alpha * 0.45;
    ctx.drawImage(halo, p.x - r * 3, p.y - r * 3, r * 6, r * 6);

    // 星体：白心 → 淡色，再描一圈白边
    var g = ctx.createLinearGradient(p.x - r, p.y - r, p.x + r, p.y + r);
    g.addColorStop(0, "#FFFFFF");
    g.addColorStop(0.55, p.pal.body);
    g.addColorStop(1, p.pal.body);
    ctx.globalAlpha = alpha;
    ctx.fillStyle = g;
    starPath(p.x, p.y, r, p.rot);
    ctx.fill();
    ctx.globalAlpha = alpha * 0.9;
    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = Math.max(0.6, r * 0.16);
    ctx.stroke();
  }

  function drawRings() {
    for (var i = rings.length - 1; i >= 0; i--) {
      var g = rings[i];
      g.r += 2.4;
      g.life -= 0.032;
      if (g.life <= 0) { rings.splice(i, 1); continue; }
      ctx.globalAlpha = g.life * 0.28;
      ctx.strokeStyle = "#C2A24E";
      ctx.lineWidth = 2 * g.life + 0.5;
      ctx.beginPath();
      ctx.arc(g.x, g.y, g.r, 0, TAU);
      ctx.stroke();
    }
  }

  var state = { x: 0, y: 0, px: 0, py: 0, hasLast: false, acc: 0, lastFrame: 0 };
  var last = 0, dirty = false;

  // 沿这段路径均匀补星：不管移动多快、转多急，都是一条连续的星轨
  function move(x, y) {
    var ox = state.px;
    var oy = state.py;
    if (!state.hasLast) {
      state.hasLast = true;
      ox = x; oy = y;
      state.acc = CFG.spacing;          // 起手也撒一颗
    }
    state.px = x; state.py = y; state.x = x; state.y = y;

    var dx = x - ox;
    var dy = y - oy;
    state.acc += Math.sqrt(dx * dx + dy * dy);
    var n = Math.floor(state.acc / CFG.spacing);
    if (n <= 0) return;
    state.acc -= n * CFG.spacing;       // 余量留到下次，间距始终均匀
    if (n > CFG.maxPerMove) n = CFG.maxPerMove;

    for (var i = 1; i <= n; i++) {
      var t = i / (n + 1);
      spawnStar(ox + dx * t, oy + dy * t);
    }
  }

  function frame(t) {
    var dt = last ? Math.min((t - last) / 16.7, 3) : 1;
    last = t;

    if (dirty || list.length || rings.length) {
      ctx.clearRect(0, 0, W, H);
      for (var i = list.length - 1; i >= 0; i--) {
        var p = list[i];
        p.life -= p.decay * dt;
        if (p.life <= 0) { list.splice(i, 1); continue; }
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.rot += p.spin * dt;
        p.phase += p.twinkle * dt;
        drawStar(p);
      }
      drawRings();
      ctx.globalAlpha = 1;
      dirty = Boolean(list.length || rings.length);
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  document.addEventListener("mousemove", function (e) {
    move(e.clientX, e.clientY);
  }, { passive: true });

  document.addEventListener("touchmove", function (e) {
    var touch = e.touches && e.touches[0];
    if (touch) move(touch.clientX, touch.clientY);
  }, { passive: true });

  document.addEventListener("pointerdown", function (e) {
    state.hasLast = false;               // 重新起头，免得从上次的位置拖一条长线过来
    move(e.clientX, e.clientY);
    spawnBurst(e.clientX, e.clientY);
  }, { passive: true });
})();
