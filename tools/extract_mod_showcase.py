# -*- coding: utf-8 -*-
"""从 mod 的动画包批量导出「展示图」（物品 idle 动画的第一帧）。

需要用户自己的 DST Mod Tool（dst-app）：本脚本只负责
  ① 解出 mod 里的 anim/*.zip
  ② 生成两份 Lua 脚本（先用 dry-run 配对，再正式导出）
真正的渲染与导出由 dst-app 的 script 模式完成。

用法：
    python tools/extract_mod_showcase.py <mod.zip>

随后按脚本打印出的两条命令执行。**注意：dst-app 每次启动都会联网检查更新，
建议先按下面的「断网运行」设置环境变量再跑。**

断网运行（重要）
----------------
dst-app 启动时会请求 gitee 上的更新清单，且它用的是 reqwest，
尊重标准代理环境变量。要让它完全不联网，先设好：

    $env:DST_UPDATE_MANIFEST_URL = "http://127.0.0.1:9/none.json"
    $env:HTTP_PROXY  = "http://127.0.0.1:9"
    $env:HTTPS_PROXY = "http://127.0.0.1:9"
    $env:ALL_PROXY   = "http://127.0.0.1:9"
    $env:NO_PROXY    = "127.0.0.1,localhost"

（9 是 discard 端口，本地连接会立刻被拒，因此不会有任何外部流量；
  NO_PROXY 保留本地地址，避免影响 dst-app 自己的本地 IPC。）

更彻底的做法是用管理员权限加一条 Windows 防火墙出站规则，直接封掉该 exe。

导出目录：images/lingjie/showcase/<物品id>.png

已知特例（这些包的动画不叫 idle，或需要符号覆盖，均已内置）：
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
ANIMS = os.path.join(WORK, "anims")
OUT = os.path.join(ROOT, "images", "lingjie", "showcase")

PILL_IDS = (
    "lj_failed_pill", "lj_ningqi_pill", "lj_warming_pill", "lj_cooling_pill",
    "lj_stillness_pill", "lj_reiki_pill", "lj_explosion_pill", "lj_drying_pill",
    "lj_invincible_pill", "lj_bigu_pill", "lj_yinqi_pill", "lj_ruwei_pill",
    "lj_restore_pill", "lj_extraordinary_pill", "lj_heying_pill",
    "lj_disaster_pill", "lj_juling_pill",
)
LOG_IDS = ("lj_ice_log", "lj_dragon_log", "lj_mighty_log", "lj_dust_log", "lj_purplemonster_log")
BANK_ALIAS = {"lj_soul_devouring_snake": "lj_three_headed_snake"}
ANIM_OVERRIDE = {
    "lj_crystalcrown": "anim",
    "lj_cuiju_box": "closed",
    "lj_huangjie_box": "closed",
    "lj_blood_bat": "fly_loop_side",
    "lj_demon_bat": "fly_loop_side",
}


def emit(path, lines):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("已生成 %s (%d 字节)" % (path, os.path.getsize(path)))


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


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    mod_zip = sys.argv[1]
    os.makedirs(ANIMS, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    z = zipfile.ZipFile(mod_zip)
    zips = []
    for name in z.namelist():
        if name.lower().endswith(".zip") and "/anim/" in name.replace("\\", "/"):
            base = os.path.basename(name)
            with open(os.path.join(ANIMS, base), "wb") as fh:
                fh.write(z.read(name))
            zips.append(base)
    zips.sort()
    print("解出 %d 个动画包 -> %s" % (len(zips), ANIMS))

    data = json.load(io.open(os.path.join(ROOT, "data.json"), encoding="utf-8"))
    plan = plan_of(data)
    print("导出计划 %d 个" % len(plan))

    head = [
        "local ANIMS = [[%s\\]]" % ANIMS,
        "local OUT   = [[%s\\]]" % OUT,
        "local files = {",
    ]
    for i in range(0, len(zips), 4):
        head.append("    " + " ".join('"%s",' % x for x in zips[i:i + 4]))
    head += ["}", "local paths = {}", "for _, f in ipairs(files) do paths[#paths + 1] = ANIMS .. f end",
             "local imported = doc:import_resources(paths)",
             'print(string.format("IMPORTED builds=%d banks=%d", #imported.builds, #imported.banks))',
             "", "local plan = {"]
    for e in plan:
        parts = ['id = "%s"' % e["id"]]
        if e["bank"]:
            parts.append('bank = "%s"' % e["bank"])
        if e["anim"]:
            parts.append('anim = "%s"' % e["anim"])
        if e["sym"]:
            parts.append('sym = "%s"' % e["sym"])
        head.append("    { %s }," % ", ".join(parts))
    head += ["}", ""]

    body = [
        "local okN, missN = 0, 0",
        "for _, e in ipairs(plan) do",
        "    local bank = doc.banks:find(e.bank or e.id)",
        "    local anim = nil",
        "    if bank then",
        '        anim = e.anim and bank.animations:find(e.anim) or bank.animations:find("idle")',
        "        if not anim then",
        "            for ai = 1, #bank.animations do",
        "                local a = bank.animations[ai]",
        '                if string.sub(string.lower(a.name), 1, 4) == "idle" then anim = a break end',
        "            end",
        "        end",
        "    end",
        "    if not anim then",
        "        for ki = 1, #doc.banks do",
        "            local a = doc.banks[ki].animations:find(e.id)",
        "            if a then anim = a break end",
        "        end",
        "    end",
        "    if anim and #anim.frames >= 1 then",
        "        okN = okN + 1",
        '        print(string.format("OK   %-34s frames=%d", e.id, #anim.frames))',
        "        if EXPORT then",
        "            local opts = { max_dimension = 512 }",
        "            if e.sym then opts.override_symbols = { [e.sym] = e.id } end",
        '            anim.frames[1]:export_png(OUT .. e.id .. ".png", opts)',
        "        end",
        "    else",
        "        missN = missN + 1",
        '        print(string.format("MISS %-34s", e.id))',
        "    end",
        "end",
        'print(string.format("RESULT resolved=%d missing=%d", okN, missN))',
    ]

    emit(os.path.join(WORK, "batch_dryrun.lua"), head + ["local EXPORT = false"] + body)
    emit(os.path.join(WORK, "batch_export.lua"), head + ["local EXPORT = true"] + body)
    print("")
    print("接着跑（把 <dst-app> 换成实际 exe 路径）：")
    print('  <dst-app> script --bypass --file "%s"' % os.path.join(WORK, "batch_dryrun.lua"))
    print('  <dst-app> script --bypass --file "%s"' % os.path.join(WORK, "batch_export.lua"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
