# -*- coding: utf-8 -*-
"""从 mod 的动画包批量导出「展示图」（物品 idle 动画的第一帧）。

用法：
    python tools/extract_mod_showcase.py <mod目录 或 mod.zip>
    # 例如： python tools/extract_mod_showcase.py D:\\Users\\huan\\Documents\\GitHub\\lj_mod

本脚本只负责：
  ① 找出 mod 里的 anim/*.zip
  ② 生成两份 Lua 脚本（先 dry-run 看选了哪个动画、有哪些幽灵符号，再正式导出）
真正的渲染与导出由 dst-app 的 script 模式完成（见文末命令）。

**注意：dst-app 每次启动都会联网检查更新，务必按下面的「断网运行」设置环境变量。**

断网运行（重要）
----------------
    $env:DST_UPDATE_MANIFEST_URL = "http://127.0.0.1:9/none.json"
    $env:HTTP_PROXY  = "http://127.0.0.1:9"
    $env:HTTPS_PROXY = "http://127.0.0.1:9"
    $env:ALL_PROXY   = "http://127.0.0.1:9"
    $env:NO_PROXY    = "127.0.0.1,localhost"

（9 是 discard 端口，本地连接会立刻被拒，因此不会有任何外部流量。）

导出目录：images/lingjie/showcase/<物品id>.png

关于「幽灵符号」（重要）
------------------------
dst-app 的符号查找是**跨 build 按名字解析**的：某个动画里引用了一个自己 build 里
并不存在的符号时，只要同一次导入的其它 build 里有同名符号，就会被画上去。

实例：聚气淬具匣 lj_cuiju_box 的 closed 帧里有一个遗留的 swap_object 元件，
      批量导入时它从灵韵（弓）的 build 解析出来，于是匣子图上多画了一把弓。

本脚本在导出前会**逐个检查帧内元件**：凡是元素符号不在该条目的 build 里的，
就把它所在的 Layer 加进 hide_layers 一起导出。丹药那种用 override_symbols
刻意替换的符号会被排除在外，不会误伤。

已知特例（这些包的动画不叫 idle，或需要符号覆盖，均已内置）：
    lj_chiyan_scorpion_dragon -> 动画 idle_loop_side
        （该 bank 没有 idle，只有 idle_loop_side / upside / downside；
          不加这条会兜底选中 downside 俯视角度，头部会被身体挡住看不见）
    lj_crystalcrown  -> 动画 anim
    lj_cuiju_box     -> 动画 closed
    lj_huangjie_box  -> 动画 closed
    lj_blood_bat     -> 动画 fly_loop_side
    lj_demon_bat     -> 动画 fly_loop_side
    lj_soul_devouring_snake -> 借用 lj_three_headed_snake 的 bank
    5 本线索日志       -> 借用 lj_log 的 bank
    17 种丹药         -> 共用 lj_pill 的 idle 动画，
                        靠 override_symbols 把 swap_food 换成各自丹药的符号
                        （见 lj_pill.lua:142 OverrideSymbol("swap_food", "lj_pill", name)）
"""

import io
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, ".work")
OUT = os.path.join(ROOT, "images", "lingjie", "showcase")

PILL_IDS = (
    "lj_failed_pill", "lj_ningqi_pill", "lj_warming_pill", "lj_cooling_pill",
    "lj_stillness_pill", "lj_reiki_pill", "lj_explosion_pill", "lj_drying_pill",
    "lj_invincible_pill", "lj_bigu_pill", "lj_yinqi_pill", "lj_ruwei_pill",
    "lj_restore_pill", "lj_extraordinary_pill", "lj_heying_pill",
    "lj_disaster_pill", "lj_juling_pill",
)
LOG_IDS = ("lj_ice_log", "lj_dragon_log", "lj_mighty_log", "lj_dust_log", "lj_purplemonster_log")
BANK_ALIAS = {
    "lj_soul_devouring_snake": "lj_three_headed_snake",
    # 挖出来的根没有自己的包，动画在父本植物里（dug = 挖出来那一帧）
    "lj_reiki_dug_grass": "lj_reiki_grass",
    "lj_red_magic_dug_flower": "lj_red_magic_flower",
}
ANIM_OVERRIDE = {
    # 生物一律优先取**正面**朝向（-downside / -down），看着最完整；
    # 注意：蝎龙之前用 downside 时头看不见，那是跨包串图造成的，指定 builds 之后正面就正常了。
    "lj_chiyan_scorpion_dragon": "idle_loop_downside",
    "lj_crystalcrown": "anim",
    "lj_cuiju_box": "closed",
    "lj_huangjie_box": "closed",
    "lj_blood_bat": "fly_loop_down",
    "lj_demon_bat": "fly_loop_down",
    "lj_reiki_dug_grass": "dug",
    "lj_red_magic_dug_flower": "dug",
}


def emit(path, lines):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("已生成 %s (%d 字节)" % (path, os.path.getsize(path)))


def collect_anims(src):
    """返回 (anim 目录, 动画包文件名列表)。src 可以是 mod 目录或 mod.zip。"""
    if os.path.isdir(src):
        anim_dir = os.path.join(src, "anim")
        if not os.path.isdir(anim_dir):
            raise SystemExit("目录里没有 anim/：%s" % src)
        names = sorted(f for f in os.listdir(anim_dir) if f.lower().endswith(".zip"))
        return anim_dir, names

    anim_dir = os.path.join(WORK, "anims")
    os.makedirs(anim_dir, exist_ok=True)
    z = zipfile.ZipFile(src)
    names = []
    for name in z.namelist():
        if name.lower().endswith(".zip") and "/anim/" in name.replace("\\", "/"):
            base = os.path.basename(name)
            with open(os.path.join(anim_dir, base), "wb") as fh:
                fh.write(z.read(name))
            names.append(base)
    return anim_dir, sorted(names)


def plan_of(data):
    plan = []
    for it in data["items"]:
        iid = it["id"]
        if not iid.startswith("lj_"):
            continue
        entry = {"id": iid, "bank": None, "anim": ANIM_OVERRIDE.get(iid), "sym": None}
        if iid in PILL_IDS:
            entry["bank"] = "lj_pill"
            entry["anim"] = "idle"
            entry["sym"] = "swap_food"      # 用符号覆盖区分每一种丹药
        elif iid in LOG_IDS:
            entry["bank"] = "lj_log"
        elif iid in BANK_ALIAS:
            entry["bank"] = BANK_ALIAS[iid]
        plan.append(entry)
    return sorted(plan, key=lambda e: e["id"])


LUA_COMMON = """local ANIMS = [[{anims}\\]]
local OUT   = [[{out}\\]]
local files = {{
{files}
}}
local paths = {{}}
for _, f in ipairs(files) do paths[#paths + 1] = ANIMS .. f end

local imported = doc:import_resources(paths)
print(string.format("IMPORTED builds=%d banks=%d", #imported.builds, #imported.banks))

local plan = {{
{plan}
}}

-- 该条目自己的 build：先按 bank 名找，再按物品 id 找
local function build_for(name)
    if name == nil then return nil end
    return doc.builds:find(name)
end

-- 选动画：指定名 > 精确 idle > 任何 idle* 开头（并在报告里标出来）
local function find_anim(bank, want)
    if bank == nil then return nil, "no-bank", nil end
    if want ~= nil then
        local a = bank.animations:find(want)
        if a then return a, want, bank end
        return nil, "missing:" .. want, bank
    end
    local a = bank.animations:find("idle")
    if a then return a, "idle", bank end
    for ai = 1, #bank.animations do
        local c = bank.animations[ai]
        if string.sub(string.lower(c.name), 1, 4) == "idle" then
            return c, c.name .. " (fallback)", bank
        end
    end
    return nil, "no-idle", bank
end

-- 找出「符号不在自己 build 里」的元件所在的 Layer，导出时隐藏掉。
-- 找不到该条目自己的 build 时不做判断（否则每个符号都会被当成幽灵，图会被清空）。
local function phantom_layers(frame, build, override_src)
    local layers, names = {{}}, {{}}
    if build == nil then return layers, false end
    for _, s in ipairs(build.symbols) do names[string.lower(s.name)] = true end
    for _, e in ipairs(frame.elements) do
        local nm = string.lower(tostring(e.symbol))
        local is_override = override_src ~= nil and nm == string.lower(override_src)
        if not is_override and not names[nm] then
            layers[tostring(e.layer)] = true
        end
    end
    return layers, true
end
"""

LUA_BODY = """
local okN, missN = 0, 0
for _, e in ipairs(plan) do
    local bank = doc.banks:find(e.bank or e.id)
    local anim, how, owner = find_anim(bank, e.anim)
    if anim == nil and e.anim == nil then
        for ki = 1, #doc.banks do
            local a = doc.banks[ki].animations:find(e.id)
            if a then anim, how, owner = a, "by-name", doc.banks[ki] break end
        end
    end

    if anim ~= nil and #anim.frames >= 1 then
        okN = okN + 1
        local frame = anim.frames[1]
        local build = build_for(e.bank or e.id) or build_for(e.id)
            or (owner ~= nil and build_for(owner.name)) or nil
        local ph, checked = phantom_layers(frame, build, e.sym)
        local phlist = {}
        for k in pairs(ph) do phlist[#phlist + 1] = k end
        table.sort(phlist)
        print(string.format("OK   %-32s anim=%-24s build=%-24s hide=%s%s",
            e.id, tostring(how), build ~= nil and build.name or "-", table.concat(phlist, ","),
            checked and "" or "  (build 未找到，跳过幽灵检查)"))
        if EXPORT then
            local opts = { max_dimension = 512 }
            -- 关键：只允许用该条目自己的 build 渲染。
            -- dst-app 找符号是跨 build 按名字来的，批量导入时同名符号（head、body、shadow…）
            -- 会被别的包抢走 —— 魂幡图上因此多过一个蝎子头。显式给 builds 就只查这一套图集。
            if build ~= nil then opts.builds = { build } end
            if #phlist > 0 then opts.hide_layers = phlist end
            if e.sym then opts.override_symbols = { [e.sym] = e.id } end
            frame:export_png(OUT .. e.id .. ".png", opts)
        end
    else
        missN = missN + 1
        print(string.format("MISS %-32s how=%s", e.id, tostring(how)))
    end
end
print(string.format("RESULT resolved=%d missing=%d", okN, missN))
"""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = sys.argv[1]
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    anim_dir, zips = collect_anims(src)
    print("找到 %d 个动画包 -> %s" % (len(zips), anim_dir))

    data = json.load(io.open(os.path.join(ROOT, "data.json"), encoding="utf-8"))
    plan = plan_of(data)
    print("导出计划 %d 个" % len(plan))

    files = []
    for i in range(0, len(zips), 4):
        files.append("    " + " ".join('"%s",' % x for x in zips[i:i + 4]))

    plan_lines = []
    for e in plan:
        parts = ['id = "%s"' % e["id"]]
        if e["bank"]:
            parts.append('bank = "%s"' % e["bank"])
        if e["anim"]:
            parts.append('anim = "%s"' % e["anim"])
        if e["sym"]:
            parts.append('sym = "%s"' % e["sym"])
        plan_lines.append("    { %s }," % ", ".join(parts))

    common = LUA_COMMON.format(anims=anim_dir, out=OUT,
                               files="\n".join(files), plan="\n".join(plan_lines))

    emit(os.path.join(WORK, "batch_dryrun.lua"), [common, "local EXPORT = false", LUA_BODY])
    emit(os.path.join(WORK, "batch_export.lua"), [common, "local EXPORT = true", LUA_BODY])

    print("")
    print("接着跑（把 <dst-app> 换成实际 exe 路径，并先设好断网环境变量）：")
    print('  <dst-app> script --bypass --file "%s"' % os.path.join(WORK, "batch_dryrun.lua"))
    print('  <dst-app> script --bypass --file "%s"' % os.path.join(WORK, "batch_export.lua"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
