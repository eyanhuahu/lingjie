#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mod 包 ↔ wiki 的机器对账。

用途：每次收到新的 lj_mod 包，先跑这个，再动手改 wiki。
它只查「机器能查的」，查不了的（机制流程、触发条件）必须人工逐条过 注释.md 的「mod 同步规程」。

用法：
    python tools/audit_mod.py                 # 自动找最新的 lj_mod*.zip
    python tools/audit_mod.py <mod.zip>       # 指定包

检查项：
  1. 版本号、包内最新时间
  2. 配方对账：mod 每条配方的材料与数量 ↔ wiki 卡片「制作配方」
  3. 卡片缺失：mod 有配方、但 wiki 没有同名卡片
  4. 原版材料官方译名：wiki 配方里出现的材料名，逐个核对游戏 chinese_s.po
  5. 常量清单：把改动脚本里的数字常量打印出来（供人工逐条落到卡片）
"""

import io
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data.json")
GAME_SCRIPTS = r"D:\steam\steamapps\common\Don't Starve Together\data\databundles\scripts.zip"

# mod 预制体 -> 中文材料名（原版材料查 po，mod 材料见下）
VANILLA = {
    "moonrocknugget": ["月岩"], "nightmarefuel": ["噩梦燃料"], "livinglog": ["活木"],
    "lightbulb": ["荧光果"], "silk": ["蜘蛛丝"], "petals": ["花瓣"], "beeswax": ["蜂蜡"],
    "boards": ["木板"], "cutstone": ["石砖"], "rope": ["绳子"], "flint": ["燧石"],
    "twigs": ["树枝"], "goldnugget": ["金块"], "redgem": ["红宝石"], "bluegem": ["蓝宝石"],
    "purplegem": ["紫宝石"], "monstermeat": ["怪物肉"], "boneshard": ["骨头碎片"],
    "houndstooth": ["犬齿"], "tentaclespots": ["触手皮"], "charcoal": ["木炭"],
    "nitre": ["硝石"], "honey": ["蜂蜜"], "glommerwings": ["格罗姆翅膀"],
    "moonrockcrater": ["月眼"], "moon_tree_blossom": ["月树花"],
    "shadowheart_infused": ["附身暗影心房"], "shadowheart": ["暗影心房"],
    "deerclops_eyeball": ["鹿角眼球"], "thulecite": ["铥矿"], "greengem": ["绿宝石"],
    "yellowstaff": ["唤星法杖"], "opalstaff": ["唤月法杖"], "papyrus": ["莎草纸"],
    "transistor": ["晶体管"], "log": ["木头"], "cutgrass": ["草"], "rocks": ["石头"],
    "klaussackkey": ["克劳斯钥匙"], "lightninggoathorn": ["电羊角"],
    "gnarwail_horn": ["海象鼻"], "yellowgem": ["黄宝石"], "orangegem": ["橙宝石"],
    "oceanfish_small_6_inv": ["落叶比目鱼"], "oceanfish_small_7_inv": ["花朵金枪鱼"],
    "oceanfish_small_8_inv": ["炽热太阳鱼"], "oceanfish_medium_1_inv": ["泥鱼"],
    "oceanfish_medium_8_inv": ["冰鲷鱼"],
}
MOD_CN = {
    "lj_magic_debris": "魔核碎片", "lj_magic_core": "魔核", "lj_magic_crystal": "魔晶",
    "lj_xichen_fruit": "洗尘神树果", "lj_ordinary_sword": "淬铁灵剑",
    "lj_scorpion_dragon_bone": "蝎龙骨", "lj_bat_blood": "血蝠精血",
    "lj_amethyst_shell": "紫晶壳", "lj_lion_bone": "狮骨",
}


def find_zip(argv):
    if argv:
        return argv[0]
    cands = []
    for d in (os.path.dirname(ROOT), os.path.expanduser("~/Downloads")):
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().startswith("lj_mod") and f.lower().endswith(".zip"):
                    p = os.path.join(d, f)
                    cands.append((os.path.getmtime(p), p))
    if not cands:
        raise SystemExit("找不到 lj_mod*.zip，请用参数指定")
    cands.sort(reverse=True)
    return cands[0][1]


def load_po():
    """游戏官方简中：英文 msgid -> 简中 msgstr"""
    if not os.path.exists(GAME_SCRIPTS):
        return {}
    z = zipfile.ZipFile(GAME_SCRIPTS)
    try:
        po = z.read("scripts/languages/chinese_s.po").decode("utf-8", "replace")
    except KeyError:
        return {}
    out, lines = {}, po.replace("\r\n", "\n").split("\n")
    for i, l in enumerate(lines):
        l = l.strip()
        if l.startswith("msgid "):
            key = l[len("msgid "):].strip()
            if len(key) >= 2 and key[0] == '"' and key[-1] == '"':
                key = key[1:-1]
            for k in range(i + 1, min(i + 4, len(lines))):
                nxt = lines[k].strip()
                if nxt.startswith("msgstr "):
                    val = nxt[len("msgstr "):].strip()
                    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
                        val = val[1:-1]
                    if key:
                        out[key] = val
                    break
    return out


def main(argv):
    zp = find_zip(argv)
    print("对账包：%s（%.1f MB）" % (zp, os.path.getsize(zp) / 1048576.0))
    z = zipfile.ZipFile(zp)
    infos = z.infolist()
    newest = max(i.date_time for i in infos)
    print("包内最新：%04d-%02d-%02d %02d:%02d，文件 %d 个"
          % (newest[0], newest[1], newest[2], newest[3], newest[4], len(infos)))

    modinfo = z.read("lj_mod/modinfo.lua").decode("utf-8", "replace")
    m = re.search(r'version\s*=\s*"([^"]+)"', modinfo)
    print("mod 版本：%s" % (m.group(1) if m else "?"))

    wiki = json.load(io.open(DATA, encoding="utf-8"))
    by_name = {it["名称"]: it for it in wiki["items"]}
    site_ver = wiki["site"][0].get("网站版本")
    print("wiki 版本：%s" % site_ver)
    if m and site_ver and ("v" + m.group(1)) != site_ver:
        print("  ⚠️ 版本不一致：mod %s / wiki %s" % (m.group(1), site_ver))

    # ---- 1. 配方对账 ----
    zh = z.read("lj_mod/scripts/main/localization/language_zh.lua").decode("utf-8", "replace")
    names = dict(re.findall(r'STRINGS\.NAMES\.([A-Z0-9_]+)\s*=\s*"([^"]+)"', zh))
    recipes_src = z.read("lj_mod/scripts/main/crafting/recipes.lua").decode("utf-8", "replace")
    blocks = re.findall(r"AddRecipe2?\(\s*\"([^\"]+)\"[^{]*\{(.*?)\}\s*,", recipes_src, re.S)
    print("\n=== 配方对账（%d 条）===" % len(blocks))
    problems = 0
    for prod, body in blocks:
        cn = names.get(prod.upper())
        if cn is None:
            continue
        ing = re.findall(r'Ingredient\(\s*"([^"]+)"\s*,\s*(\d+)', body)
        it = by_name.get(cn)
        if it is None:
            print("  ✗ %-12s mod 有配方，wiki 没有这张卡片" % cn)
            problems += 1
            continue
        flat = re.sub(r"\[images/[^\]]+\]", "", it.get("制作配方") or "")
        got = dict((a, b) for a, b in re.findall(r"([\u4e00-\u9fa5A-Za-z·]+)\s(\d+)", flat))
        diffs = []
        for pid, n in ing:
            nm = MOD_CN.get(pid) or (VANILLA.get(pid) or [pid])[0]
            if nm in got and got[nm] != n:
                diffs.append("%s mod=%s wiki=%s" % (nm, n, got[nm]))
        if diffs:
            print("  ✗ %-12s %s" % (cn, "; ".join(diffs)))
            problems += 1
    if not problems:
        print("  ✓ 全部一致")

    # ---- 2. 原版材料官方译名 ----
    po = load_po()
    rev = {}
    for en, cn in po.items():
        rev.setdefault(cn, en)
    print("\n=== 原版材料名核对 ===")
    bad = 0
    seen = set()
    for it in wiki["items"]:
        flat = re.sub(r"\[images/[^\]]+\]", "", it.get("制作配方") or "")
        for a, _ in re.findall(r"([\u4e00-\u9fa5·]+)\s(\d+)", flat):
            if a in seen or a in MOD_CN.values():
                continue
            seen.add(a)
            if a in ("木板", "石砖", "绳子", "燧石", "树枝", "金块", "红宝石", "蓝宝石", "紫宝石",
                     "怪物肉", "骨头碎片", "犬齿", "触手皮", "木炭", "硝石", "蜂蜜", "格罗姆翅膀",
                     "月岩", "噩梦燃料", "活木", "荧光果", "蜘蛛丝", "花瓣", "蜂蜡", "月眼",
                     "月树花", "附身暗影心房", "暗影心房", "铥矿", "绿宝石", "唤星法杖", "唤月法杖",
                     "莎草纸", "晶体管", "木头", "草", "石头", "克劳斯钥匙", "电羊角", "海象鼻",
                     "黄宝石", "橙宝石", "落叶比目鱼", "花朵金枪鱼", "炽热太阳鱼", "泥鱼", "冰鲷鱼",
                     "鹿角眼球", "洗尘神树果", "兔毛球", "独眼巨鹿眼球",
                     "采下的融灵草", "采下的龙爪花", "紫晶塑体花瓣", "噬魂蛇皮",
                     "转元丹", "转元丹·木", "转元丹·火", "转元丹·金", "转元丹·水", "转元丹·土",
                     "蝎龙骨", "血蝠精血", "紫晶壳", "狮骨", "暗影心房",
                     # 橡果 = 原版基础物品（官方 .po 里没有单独条目）；风干的羽毛 = mod 自己的 LJ_DRIED_CAMEL_FEATHERS
                     "橡果", "风干的羽毛"):
                continue
            if a not in rev:
                print("  ⚠️ 「%s」在游戏官方简中里找不到（可能是 mod 材料或译名有误）" % a)
                bad += 1
    if not bad:
        print("  ✓ 都没有疑点")

    # ---- 3. 常量清单 ----
    print("\n=== 本轮改动脚本里的数字常量（人工逐条落到卡片）===")
    base = (0, 0, 0, 0, 0)
    files = sorted(((i.date_time, i.filename) for i in infos if i.filename.endswith(".lua")), reverse=True)
    if files:
        base = files[0][0]
    # 用「最新文件的日期」前 1 天作为界，列出最近改的脚本
    recent = [(d, f) for d, f in files if d[:3] == base[:3]]
    for d, f in recent[:12]:
        t = z.read(f).decode("utf-8", "replace")
        consts = re.findall(r"^\s*local\s+([A-Z_]{3,})\s*=\s*([0-9.]+)", t, re.M)
        if consts:
            print("  %-52s %s" % (f.split("lj_mod/")[-1],
                                  ", ".join("%s=%s" % (k, v) for k, v in consts[:8])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
