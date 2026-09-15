// 灵界 Wiki —— 用真实站点代码验证 data.json
//
// 作用：直接把 site/js/sheetsContent.js 跑起来，喂进 data.json，
//       确认前台归一化后的结果正确（卷目、条目、词条跳转、图片解析）。
//       这样不用开浏览器也能验证数据能不能被站点正确读取。
//
// 用法：
//     node tools/verify_site.js
//
// 退出码 0 = 通过；1 = 失败。

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.dirname(__dirname);
const DATA_JSON = path.join(ROOT, "data.json");
const SHEETS_JS = path.join(ROOT, "site", "js", "sheetsContent.js");

const failures = [];
const warnings = [];

function check(cond, msg) {
  if (!cond) failures.push(msg);
}

// ---- 1. 读出 data.json ----
let data;
try {
  data = JSON.parse(fs.readFileSync(DATA_JSON, "utf8"));
} catch (err) {
  console.error("data.json 读取/解析失败：" + err.message);
  process.exit(1);
}

// ---- 2. 在沙箱里加载真实站点脚本 ----
const sandbox = {
  console,
  TextDecoder,
  Blob,
  Response,
  DecompressionStream,
  fetch: (url) => {
    const target = String(url);
    if (target.indexOf("data.json") >= 0) {
      return Promise.resolve(
        new Response(fs.readFileSync(DATA_JSON, "utf8"), {
          status: 200,
          headers: { "content-type": "application/json" },
        })
      );
    }
    return Promise.resolve(new Response("not found", { status: 404 }));
  },
  window: {},
  document: {
    createElement: () => ({ innerHTML: "", textContent: "", content: { textContent: "" } }),
    createTextNode: (t) => ({ textContent: t }),
  },
  DOMParser: class {
    parseFromString() {
      throw new Error("verify 环境未提供 DOMParser");
    }
  },
};
sandbox.window = sandbox;
sandbox.self = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(SHEETS_JS, "utf8"), sandbox, { filename: "sheetsContent.js" });

const Sheets = sandbox.window.SheetsContent;
check(Sheets && typeof Sheets.buildContentFromSheets === "function", "sheetsContent.js 未导出 buildContentFromSheets");
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

// ---- 3. 用站点自己的逻辑归一化 ----
const built = Sheets.buildContentFromSheets(data);

// 站点要求 sections 与 items 都非空，否则 app.js 会抛「解析失败」
check(built.sections.length > 0, "归一化后 sections 为空");
check(built.items.length > 0, "归一化后 items 为空");

// 逐一核对：raw data.json 的可见条目都必须活下来
const rawVisible = data.items.filter((r) => !Sheets.isHidden(r["是否展示"]));
check(
  built.items.length === rawVisible.length,
  `条目数不符：data.json 可见 ${rawVisible.length} 条，归一化后 ${built.items.length} 条`
);

const sectionIds = new Set(built.sections.map((s) => s.id));
for (const item of built.items) {
  if (!sectionIds.has(item.section)) {
    failures.push(`条目 ${item.id} 的分类「${item.section}」不存在，前台不会显示`);
  }
  if (!item.name) failures.push(`条目 ${item.id} 没有名称`);
  if (!item.detailText) warnings.push(`条目 ${item.id} 详情为空`);
}
check(
  !built.sections.some((s) => s.id === "uncategorized"),
  "出现了 uncategorized 卷目，说明有条目的分类失配"
);

// ---- 4. 图片：按「留空」要求，不应解析出任何卡片图 ----
const withImages = built.items.filter((it) => Array.isArray(it.images) && it.images.filter(Boolean).length);
check(withImages.length === 0, `有 ${withImages.length} 个条目解析出了图片，但本次要求图片字段全部留空`);

// ---- 5. 词条自动跳转 ----
const byId = new Map(built.items.map((it) => [it.id, it]));
const byName = new Map(built.items.map((it) => [it.name, it]));
let xrefOk = 0;
for (const row of built.tele) {
  const terms = String(row.field || "").split(/[，,、|;\n\r]+/).map((t) => t.trim()).filter(Boolean);
  const target = byId.get(row.target_id) || byName.get(row.target_id) || (terms.length === 1 ? byName.get(terms[0]) : null);
  if (!target) {
    failures.push(`词条「${row.field}」->「${row.target_id}」解析不到目标，自动跳转不会生效`);
  } else {
    xrefOk += 1;
  }
}

// ---- 6. 配方：确认图标语法能被 parseRecipe 正确切分 ----
function splitRecipe(recipe) {
  return String(recipe || "")
    .split(/(\[\[[^\]]+\]\]|\[[^\]]+\])/g)
    .filter(Boolean)
    .map((part) => {
      if (/^\[\[([^\]]+)\]\]$/.test(part)) return { type: "xref", value: part.slice(2, -2) };
      const m = part.match(/^\[([^\]]+)\]$/);
      if (m) return { type: "icon", value: m[1].trim() };
      return { type: "text", value: part };
    });
}
let recipes = 0;
let icons = 0;
let missingIconFiles = 0;
for (const item of built.items) {
  if (!item.recipe) continue;
  recipes += 1;
  for (const seg of splitRecipe(item.recipe)) {
    if (seg.type !== "icon") continue;
    icons += 1;
    const fsPath = path.join(ROOT, seg.value.split("/").join(path.sep));
    if (!fs.existsSync(fsPath)) {
      missingIconFiles += 1;
      failures.push(`条目 ${item.id} 的配方图标文件不存在：${seg.value}`);
    }
  }
}

// ---- 7. 走一遍站点真正使用的加载入口 loadContentJson ----
(async () => {
  check(typeof Sheets.loadContentJson === "function", "sheetsContent.js 未导出 loadContentJson（站点无法读取 data.json）");
  let loaded = null;
  try {
    loaded = await Sheets.loadContentJson();
  } catch (err) {
    failures.push(`loadContentJson() 抛错：${err.message}`);
  }
  if (loaded) {
    check(!!loaded.data, "loadContentJson() 没有返回 data");
    check(loaded.source === "./data.json", `loadContentJson() 的 source 不是 ./data.json：${loaded.source}`);
    check(
      loaded.data.items.length === built.items.length,
      `loadContentJson() 与 buildContentFromSheets() 结果不一致：${loaded.data.items.length} vs ${built.items.length}`
    );
  }

  // ---- 8. 输出 ----
  console.log("站点代码验证结果（真实 sheetsContent.js）");
  console.log(`  卷目 ${built.sections.length} 个`);
  console.log(`  条目 ${built.items.length} 个（data.json 可见 ${rawVisible.length} 个）`);
  console.log(`  词条自动跳转 ${xrefOk} / ${built.tele.length} 条生效`);
  console.log(`  配方法 ${recipes} 条，其中图标 ${icons} 个，缺失 ${missingIconFiles} 个`);
  console.log(`  卡片图片：${withImages.length} 个条目带图（本次要求为 0）`);
  console.log(`  加载入口：${loaded ? "loadContentJson() 正常" : "loadContentJson() 失败"}`);
  if (built.sections.length) {
    console.log("  卷目清单：");
    for (const s of built.sections) {
      const n = built.items.filter((it) => it.section === s.id).length;
      console.log(`    ${s.id.padEnd(10)} ${s.name.padEnd(10)} ${n} 条`);
    }
  }
  const sample = built.items[0];
  if (sample) {
    console.log("  样例条目：");
    console.log(`    id=${sample.id} 名称=${sample.name} 分类=${sample.section}`);
    console.log(`    标签=${JSON.stringify(sample.tags)}`);
    console.log(`    配方=${sample.recipe}`);
    console.log(`    详情长度=${sample.detailText.length} 字`);
  }
  if (warnings.length) {
    console.log(`\n警告 ${warnings.length} 条：`);
    for (const w of warnings) console.log("  ! " + w);
  }
  if (failures.length) {
    console.log(`\n失败 ${failures.length} 条：`);
    for (const f of failures) console.log("  x " + f);
    process.exit(1);
  }
  console.log("\n没有失败项 ✓");
})();
