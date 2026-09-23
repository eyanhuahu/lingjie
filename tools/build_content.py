# -*- coding: utf-8 -*-
"""
灵界 Wiki 内容批量生成器（一次性批量建档工具）

作用：把《灵界设定.docx》的文字内容整理成站点读取的 data.json；数值与命名一律以 lj_mod 源码为准。
说明：data.json 才是内容真源；本脚本用于首次批量建档与大批量重建。
      日常少量改字可直接改 data.json，改完记得跑一遍 validate_content.py。

用法：
    python tools/build_content.py            # 生成 data.json
"""

import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(ROOT, "images")
OUT_JSON = os.path.join(ROOT, "data.json")

# ---------------------------------------------------------------------------
# 图标索引：文件名(小写) -> 相对 index.html 的路径
# ---------------------------------------------------------------------------
ICON_INDEX = {}
# 展示图目录不参与「图标」索引：配方里的材料图标必须用 icons/ 下的小图标，
# 否则材料会被换成 idle 展示大图（两者同名，会互相覆盖）。
_SHOWCASE_MARK = os.path.join("lingjie", "showcase")
for dirpath, _dirnames, filenames in os.walk(IMAGES_DIR):
    if _SHOWCASE_MARK in dirpath:
        continue
    for fn in filenames:
        if not fn.lower().endswith(".png"):
            continue
        base = os.path.splitext(fn)[0].lower()
        rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace("\\", "/")
        ICON_INDEX[base] = rel

# 中文材料名 -> 图标文件基名。None 表示"目前没有可用图标"（mod 物品或原版缺图）
MATERIAL_ICON = {
    # —— 原版材料（图标已确认存在）——
    "木板": "boards",
    "砖块": "cutstone",
    "石砖": "cutstone",
    "绳子": "rope",
    "硝石": "nitre",
    "蜂蜜": "honey",
    "松果": "pinecone",
    "蝴蝶翅膀": "butterflywings",
    "月娥翅膀": "moonbutterflywings",
    "腺体": "spidergland",
    "格罗姆粘液": "glommerfuel",
    "格罗姆翅膀": "glommerwings",
    "辣椒": "pepper",
    "噩梦燃料": "nightmarefuel",
    "蜂刺": "stinger",
    "芦苇": "cutreeds",
    "橙宝石": "orangegem",
    "绿宝石": "greengem",
    "蓝宝石": "bluegem",
    "红宝石": "redgem",
    "紫宝石": "purplegem",
    "黄宝石": "yellowgem",
    "铥矿": "thulecite",
    "兔毛": "manrabbit_tail",
    "猪皮": "pigskin",
    "蕨类植物": "foliage",
    "藤壶": "barnacle",
    "饼干切割机壳": "cookiecuttershell",
    "犀牛角": "minotaurhorn",
    "蘑菇皮": "shroom_skin",
    "发光浆果": "wormlight",
    "活木": "livinglog",
    "羊奶": "goatmilk",
    "黄油": "butter",
    "蜂王浆": "royal_jelly",
    "巨鹿眼球": "deerclops_eyeball",
    "鳞片": "dragon_scales",
    "暗影心房": "shadowheart",
    "金块": "goldnugget",
    "石头": "rocks",
    "草": "cutgrass",
    "燧石": "flint",
    "树枝": "twigs",
    "木头": "log",
    "莎草纸": "papyrus",
    "电子元件": "transistor",
    "一角鲸的角": "gnarwail_horn",
    "伏特羊角": "lightninggoathorn",
    "木炭": "charcoal",
    "化石碎片": "fossil_piece",
    "绿蘑菇": "green_cap",
    "高脚鸟蛋": "tallbirdegg",
    "怪物肉": "monstermeat",
    "蝙蝠翅膀": "batwing",
    # —— 下面这批是 2026 对照 mod 源码后订正的（原先是我猜错文件名）——
    "橡果": "acorn",
    "克劳斯袋钥匙": "klaussackkey",
    "彩虹宝石": "opalpreciousgem",
    "玻璃碎片": "moonglass",
    "告密的心": "reviver",
    "唤星法杖": "yellowstaff",
    "唤月法杖": "opalstaff",
    "仙人掌肉": "cactus_meat",
    # —— mod 自己的物品：图标来自 ethereal_realm_icons 图集（见 MOD_MATERIAL_ID）——
    "融灵草": None,
    "采下的融灵草": None,
    "融灵草根": None,
    "龙爪花": None,
    "采下的龙爪花": None,
    "龙爪花根": None,
    "紫晶塑体花": None,
    "紫晶塑体花瓣": None,
    # 花瓣是**原版**物品（petals），不是 mod 物品，走原版图标
    "花瓣": "petals",
    "魔核碎片": None,
    "魔核": None,
    "魔晶": None,
    "魂元妖树根": None,
    "蝎龙骨": None,
    "紫晶壳": None,
    "狮骨": None,
    "血蝠精血": None,
    "噬魂蛇皮": None,
    "噬魂蛇鳞片": None,
    "冰霜业火本体": None,
    "龙炎心火本体": None,
    "冰霜日志": None,
    "龙炎日志": None,
    "狂鬃日志": None,
    "尘火日志": None,
    "紫鳞日志": None,
}

# 展示图索引：images/lingjie/showcase/<物品id>.png
# 由 tools/extract_mod_showcase.py 借助 DST Mod Tool 从 idle 动画第一帧导出。
SHOWCASE_INDEX = {}
_SHOWCASE_DIR = os.path.join(IMAGES_DIR, "lingjie", "showcase")
if os.path.isdir(_SHOWCASE_DIR):
    for _fn in os.listdir(_SHOWCASE_DIR):
        if _fn.lower().endswith(".png"):
            SHOWCASE_INDEX[os.path.splitext(_fn)[0]] = "images/lingjie/showcase/" + _fn

WARNINGS = []


def icon_path(basename):
    if not basename:
        return None
    return ICON_INDEX.get(basename.lower())


# mod 自己的材料：中文名 -> 预制体 id。对应图标由 tools/extract_mod_icons.py
# 从 mod 的 ethereal_realm_icons 图集导出到 images/lingjie/icons/。
MOD_MATERIAL_ID = {
    "魔核碎片": "lj_magic_debris",
    "魔核": "lj_magic_core",
    "魔晶": "lj_magic_crystal",
    "采下的融灵草": "lj_reiki_cutgrass",
    "融灵草根": "lj_reiki_dug_grass",
    "采下的龙爪花": "lj_red_magic_cutflower",
    "龙爪花根": "lj_red_magic_dug_flower",
    "紫晶塑体花瓣": "lj_purple_magic_bloom",
    "血蝠精血": "lj_bat_blood",
    "蝎龙骨": "lj_scorpion_dragon_bone",
    "紫晶壳": "lj_amethyst_shell",
    "狮骨": "lj_lion_bone",
    "噬魂蛇皮": "lj_soul_snake_skin",
    "风干的羽毛": "lj_dried_camel_feathers",
    "冰霜业火本体": "lj_ice_flame",
    "龙炎心火本体": "lj_dragon_flame",
}


def icon_for(name):
    """先查 mod 材料表（优先），再查原版材料表。"""
    if name in MOD_MATERIAL_ID:
        return MOD_MATERIAL_ID[name]
    return MATERIAL_ICON.get(name)


# mod 源码里「配方材料的中文名」与「设计文档用的名字」不是一回事：
# 文档说"融灵草"，代码里炼丹用的是采集物 `lj_reiki_cutgrass`（官方名「采下的融灵草」）。
# 这里做统一翻译，保证配方文本与 mod 一致。
CODE_MATERIAL_NAME = {
    "融灵草": "采下的融灵草",
    "龙爪花": "采下的龙爪花",
    "紫晶塑体花": "紫晶塑体花瓣",
    "仙人掌": "仙人掌肉",
}

# 配方里的材料名 → 英文（用于卡片的「英文配方」）。
# 原版材料用原版英文名，mod 材料用 NAME_EN 里既有的官方英文名。
# 没收录的名字会在构建时报告出来，不会静默留中文。
MATERIAL_EN = {
    "魔晶": "Magic Crystal",
    "魔核": "Magic Core",
    "魔核碎片": "Magic Core Shard",
    "采下的融灵草": "Harvested Spirit-Melting Grass",
    "采下的龙爪花": "Harvested Dragon Claw Flower",
    "紫晶塑体花瓣": "Amethyst Form Petals",
    "蝎龙骨": "Scorpion Dragon Bone",
    "紫晶壳": "Amethyst Shell",
    "血蝠精血": "Blood Bat Essence",
    "噬魂蛇皮": "Soul Snake Skin",
    "风干的羽毛": "Dried Camel Feathers",
    "噩梦燃料": "Nightmare Fuel",
    "木板": "Boards",
    "绿宝石": "Green Gem",
    "铥矿": "Thulecite",
    "硝石": "Nitre",
    "活木": "Living Log",
    "石砖": "Cut Stone",
    "砖块": "Cut Stone",
    "蓝宝石": "Blue Gem",
    "红宝石": "Red Gem",
    "树枝": "Twigs",
    "绳子": "Rope",
    "莎草纸": "Papyrus",
    "鳞片": "Scales",
    "橙宝石": "Orange Gem",
    "黄宝石": "Yellow Gem",
    "紫宝石": "Purple Gem",
    "金块": "Gold Nugget",
    "木头": "Log",
    "燧石": "Flint",
    "巨鹿眼球": "Deerclops Eyeball",
    "玻璃碎片": "Moon Glass",
    "芦苇": "Cut Reeds",
    "蜂蜜": "Honey",
    "橡果": "Acorn",
    "松果": "Pine Cone",
    "蝴蝶翅膀": "Butterfly Wings",
    "月娥翅膀": "Moon Moth Wings",
    "腺体": "Spider Gland",
    "格罗姆粘液": "Glommer's Goop",
    "格罗姆翅膀": "Glommer's Wings",
    "绿蘑菇": "Green Cap",
    "高脚鸟蛋": "Tallbird Egg",
    "辣椒": "Pepper",
    "蜂刺": "Stinger",
    "告密的心": "Telltale Heart",
    "猪皮": "Pig Skin",
    "蕨类植物": "Foliage",
    "兔毛": "Bunny Puff",
    "藤壶": "Barnacle",
    "饼干切割机壳": "Cookie Cutter Shell",
    "犀牛角": "Guardian's Horn",
    "蘑菇皮": "Shroom Skin",
    "发光浆果": "Glow Berry",
    "羊奶": "Electric Milk",
    "黄油": "Butter",
    "蜂王浆": "Royal Jelly",
    "彩虹宝石": "Rainbow Gem",
    "草": "Cut Grass",
    "石头": "Rocks",
    "电子元件": "Electrical Doodad",
    "伏特羊角": "Volt Goat Horn",
    "一角鲸的角": "Gnarwail Horn",
    "暗影心房": "Shadow Atrium",
    "唤星法杖": "Star Caller's Staff",
    "唤月法杖": "Moon Caller's Staff",
    "仙人掌肉": "Cactus Flesh",
    "化石碎片": "Fossil Fragments",
    "克劳斯袋钥匙": "Klaus Sack Key",
    "冰霜业火本体": "Frost Karma Flame (full)",
    "龙炎心火本体": "Dragon Flame Heartfire (full)",
}


def recipe_en(recipe):
    """把中文配方串里的材料名换成英文（图标路径原样保留，分隔符仍是「、」）。

    做法是**按名字长度的降序做整串替换**，这样：
    · 「魔核碎片」不会被「魔核」先吃掉
    · 「橡果 3 或 [图标] 松果」这种一段里塞两个名字的写法也能各自换掉
    认不出的中文会记进 WARNINGS，方便维护者补 MATERIAL_EN。
    """
    if not recipe or not recipe.strip():
        return ""
    out = recipe
    for zh in sorted(MATERIAL_EN, key=len, reverse=True):
        if zh in out:
            out = out.replace(zh, MATERIAL_EN[zh])
    out = out.replace(" 或 ", " or ")
    # 换完之后还残留中文的，报告出来（可能名字带「本体」「或」这类前后缀）
    for chunk in out.split("、"):
        for ch in chunk:
            if "\u4e00" <= ch <= "\u9fff":
                WARNINGS.append("配方英文残留中文：%s" % chunk.strip())
                break
    return out


def R(*parts):
    """把配方拼成 '图标 名称 数量、图标 名称 数量' 形式。

    每个 part 为 (名称, 数量) 或 (名称, 数量, 图标基名/None)。
    数量为 None 时只写名称（例如"克劳斯袋钥匙"这种只检查持有、不消耗的材料）。
    """
    chunks = []
    for part in parts:
        raw_name, qty = part[0], part[1]
        name = CODE_MATERIAL_NAME.get(raw_name, raw_name)
        basename = part[2] if len(part) > 2 else icon_for(name)
        path = icon_path(basename)
        if basename and path is None:
            WARNINGS.append("配方图标缺失：%s -> %s" % (name, basename))
        label = name if qty is None else "%s %s" % (name, qty)
        chunks.append("[%s] %s" % (path, label) if path else label)
    return "、".join(chunks)


# ---------------------------------------------------------------------------
# 需要在「已修复的残骸祭坛」旁制作的高阶配方。
# 名单取自 mod 的 scripts/main/crafting/recipes.lua：这些配方挂在
# TECH.ETHEREAL_REALM_ONE 上，而残骸祭坛就是该科技树的原型站（AddPrototyperDef +
# inst.components.prototyper.trees = TUNING.PROTOTYPER_TREES.LJ_REMAINS_ALTAR），
# 所以每次制作都必须站在祭坛旁边。其余配方是二本科技，永久解锁。
ALTAR_RECIPES = {
    "lj_void_ring",
    "lj_star_sword",
    "lj_reiki_bow",
    "lj_keel_armour",
    "lj_crystalcrown",
    "lj_supernatural_power_pivot",
    "lj_seasons_nucleus",
    "lj_plant_nucleus",
    "lj_subdue_demons_nucleus",
    "lj_constant_temperature_nucleus",
}

# 站点信息 / 卷目 / 词条自动跳转
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 英文（站点中英切换用）
# ---------------------------------------------------------------------------
# 条目英文名：前 56 条直接取自 mod 的 scripts/main/localization/language_en.lua
# （与 language_zh.lua 的 STRINGS.NAMES 一一对照得到，属于官方英文名）；
# 其余 mod 里没有对应英文，由 wiki 侧按语义翻译，作者可随时改。
NAME_EN = {
    "lj_soul_banner": "Soul Banner",
    "lj_failed_pill": "Failed Pill",
    "lj_ningqi_pill": "Qi Condensing Pill",
    "lj_warming_pill": "Flame Warming Pill",
    "lj_cooling_pill": "Cold Flame Pill",
    "lj_stillness_pill": "Stillness Pill",
    "lj_reiki_pill": "Reiki Pill",
    "lj_explosion_pill": "Explosion Pill",
    "lj_drying_pill": "Drying Pill",
    "lj_invincible_pill": "Invincible Pill",
    "lj_bigu_pill": "Bigu Pill",
    "lj_yinqi_pill": "Qi Guiding Pill",
    "lj_ruwei_pill": "Subtle Realm Pill（Tribulation）",
    "lj_restore_pill": "Restore Spirit Pill（Tribulation）",
    "lj_extraordinary_pill": "Extraordinary Pill（Tribulation）",
    "lj_heying_pill": "Nascent Union Pill（Tribulation）",
    "lj_disaster_pill": "Disaster Breaking Pill（Tribulation）",
    "lj_juling_pill": "Spirit Manifesting Pill（Tribulation）",
    "lj_scorpion_dragon_bone": "Scorpion Dragon Bone",
    "lj_amethyst_shell": "Amethyst Shell",
    "lj_lion_bone": "Lion Bone",
    "lj_bat_blood": "Blood Bat Essence",
    "lj_soul_snake_skin": "Soul Snake Skin",
    "lj_snake_skin": "Soul Snake Scale",
    "lj_purple_magic_bloom": "Amethyst Form Petals",
    "lj_alchemy_furnace": "Alchemy Furnace",
    "lj_reiki_tablelamp": "Reiki Table Lamp",
    "lj_flag": "Formation Flag",
    "lj_supernatural_power_pivot": "Spirit Formation Pivot",
    "lj_ordinary_sword": "Tempered Iron Spirit Sword",
    "lj_reiki_bow": "Reiki Bow",
    "lj_star_sword": "Starfall",
    "lj_keel_armour": "Keel Armour",
    "lj_crystalcrown": "Crystal Crown",
    "lj_seasons_nucleus": "Seasons Nucleus",
    "lj_plant_nucleus": "Plant Nucleus",
    "lj_subdue_demons_nucleus": "Demon Subduing Nucleus",
    "lj_constant_temperature_nucleus": "Constant Temperature Nucleus",
    "lj_frozen_log": "Frozen Log",
    "lj_charred_scales": "Charred Scales",
    "lj_rotten_backpack": "Rotten Backpack",
    "lj_dried_camel_feathers": "Dried Camel Feathers",
    "lj_swollen_scroll": "Swollen Scroll",
    "lj_ice_log": "Frost Log",
    "lj_dragon_log": "Dragonflame Log",
    "lj_mighty_log": "Mighty Flame Log",
    "lj_dust_log": "Dustflame Log",
    "lj_purplemonster_log": "Purple Scale Log",
    "lj_remains_altar": "Remains Altar",
    "lj_remains_island": "Remains Island",
    "lj_chiyan_scorpion_dragon": "Blazing Rock Scorpion Dragon",
    "lj_little_scorpion": "Venomous Scorpion Larva",
    "lj_bat_nest": "Night Bat Nest",
    "lj_demon_bat": "Shadow Blood Bat",
    "lj_blood_bat": "Demon Bat",
    "lj_soul_devouring_snake": "Soul-devouring Snake（Hidden Boss）",
    "lj_moon_lion": "Eclipsed Crystalwing Lion",
    # ↓ 以下为 wiki 侧翻译（mod 英文表里没有对应项）
    "realm_system": "Realm System",
    "reiki_value": "Reiki",
    "timed_effects": "Timed Effects",
    "tribulation_rules": "Tribulation",
    "corruption_overview": "Demonization Overview",
    "corruption_light": "Light Demonization",
    "corruption_medium": "Moderate Demonization",
    "corruption_deep": "Deep Demonization",
    "corruption_drops": "Demonization Drops",
    "alchemy_rules": "Alchemy Rules",
    "pill_tiers": "Pill Tiers & Tribulation",
    "lj_moon_vase": "Moonlight Condensing Vase",
    "lj_reiki_gourd": "Spirit Void Gourd",
    "lj_magic_debris": "Magic Core Shard",
    "lj_magic_core": "Magic Core",
    "lj_magic_crystal": "Magic Crystal",
    "lj_reiki_cutgrass": "Harvested Spirit-Melting Grass",
    "lj_reiki_dug_grass": "Spirit-Melting Grass Root",
    "lj_red_magic_cutflower": "Harvested Dragon Claw Flower",
    "lj_red_magic_dug_flower": "Dragon Claw Flower Root",
    "lj_wudao_chair": "Enlightenment Tempering Seat",
    "lj_huangjie_box": "Wild Realm Storage Box",
    "lj_cuiju_box": "Qi-Gathering Weapon Case",
    "lj_reiki_table": "Spirit Jade Table",
    "lj_reiki_cultivatepool": "Mystic Spirit Cultivation Pool（Unreleased）",
    "lj_void_ring": "Void Ring",
    "zhenfa_overview": "Formations Overview",
    "zhen_siji": "Four Seasons Harmony Formation",
    "zhen_huichun": "Vitality Rejuvenation Formation",
    "zhen_quling": "Spirit-Banishing Demon-Locking Formation",
    "zhen_jiwen": "Extreme Temperature Ward Formation",
    "lj_reiki_grass": "Spirit-Melting Grass",
    "lj_red_magic_flower": "Dragon Claw Flower",
    "lj_purple_magic_flower": "Amethyst Form Flower",
    "yihuo_rules": "Flame Usage Rules",
    "lj_ordinary_flame": "Wasteland Flame",
    "lj_ice_flame": "Frost Karma Flame",
    "lj_dragon_flame": "Dragon Flame Heartfire",
    "lj_mighty_flame": "Wildmane Flame",
    "lj_dust_flame": "Spirit Dust Flame",
    "lj_purplemonster_flame": "Purple Scale Demon Flame",
    "lj_log": "Log",
    "lj_butterfly_island": "Butterfly Island",
}

# ---------------------------------------------------------------------------
# 英文内容（站点中英切换用）：按条目 id 归档，翻译到哪一条一目了然
# ---------------------------------------------------------------------------
# 结构：{"条目id": {"tags": "英文标签", "summary": "英文简介", "detail": """英文详情"""}}
# - 三段都可以留空；留空的段英文模式下自动退回中文
# - 详情沿用与中文一致的约定：小标题单独一行、行首全角空格表示缩进、
#   「标签　内容」两行以上会渲染成表格（标签 ≤8 字符且不含空格才会被认成表格）、
#   [[图片:路径|说明]] 独占一段、[路径] 表示行内小图标
EN_CONTENT = {
    "realm_system": {
        "tags": "Realm,Cultivation,Breakthrough,Experience,Attributes",
        "summary": "Nine realms, nine stages each. Kill creatures to earn experience and advance; dying costs one stage. Includes per-stage experience thresholds and per-realm stat bonuses.",
        "detail": """
Adds Realm and Reiki values, shown alongside the three vanilla stats.

[[图片:images/lingjie/anim/realm_badge.png|In-game realm badge (the icon in the middle switches to the matching number as you advance)]]

There are 9 realms: Mortal, Tempered, Sinew, Fasting, Guiding, Subtle, Exalted, Nascent, Manifest. Each realm has 9 stages — Tempered 1, Tempered 2 … Tempered 9.

How to advance
　Earn experience by killing creatures. You count as a participant if you attacked within the last 30 seconds and within 15 turf of the kill. Abigail's attacks, and kills made by Willow's fire, count for their owner (other followers do not).
　Experience gained = the target's maximum health × 5% (5% / 8% / 12% selectable in mod settings); the code reads its current maximum health, so demonization-inflated health counts too.

Bottlenecks and meditation
　Stages 1 to 3 have no bottleneck. Stage 3 → 4, stage 6 → 7, and stage 9 → the next realm all require meditation.
　A bottleneck parks your experience just below the threshold: at Guiding 3 with 8000 experience, even a boss worth 4000 experience only takes you to 8499 — the last point has to come from meditating.

Breakthrough
　From Sinew → Fasting onward, every realm breakthrough (Fasting, Guiding, Subtle, Exalted, Nascent, Manifest) needs the matching pill plus 10 seconds of meditation. 6 breakthrough pills in total.

Death penalty
　Every death costs one stage. After losing a stage you must take a Stillness Pill before you can cultivate again, otherwise you stay stuck.

Experience threshold per stage (stage 1 → 9; the number is the cumulative threshold)
Mortal　50 · 100 · 150 · 200 · 250 · 300 · 350 · 450 · 500
Tempered　500 · 600 · 700 · 800 · 900 · 1000 · 1100 · 1200 · 1300
Sinew　1300 · 1500 · 1700 · 1900 · 2100 · 2300 · 2500 · 2700 · 2900
Fasting　2900 · 3300 · 3700 · 4100 · 4500 · 4900 · 5300 · 5700 · 6100
Guiding　6100 · 6900 · 7700 · 8500 · 9300 · 10100 · 10900 · 11700 · 12500
Subtle　12500 · 14000 · 15500 · 17000 · 18500 · 20000 · 21500 · 23000 · 24500
Exalted　24500 · 27000 · 29500 · 32000 · 34500 · 37000 · 39500 · 42000 · 44500
Nascent　44500 · 48500 · 52500 · 56500 · 60500 · 64500 · 68500 · 72500 · 76500
Manifest　76500 · 82500 · 88500 · 94500 · 100500 · 106500 · 112500 · 118500 · 124500
　Within Mortal the first seven stages add +50 each, with 450 and 500 for stages 8 and 9. Inside every other realm the step is fixed: Tempered +100, Sinew +200, Fasting +400, Guiding +800, Subtle +1500, Exalted +2500, Nascent +4000, Manifest +6000.

Per-realm stat bonus (applies once you reach that realm)
Mortal　HP +0, Speed ×1.00, Reiki +0, Attack ×1.00
Tempered　HP +10, Speed ×1.05, Reiki +5, Attack ×1.25
Sinew　HP +15, Speed ×1.10, Reiki +10, Attack ×1.50
Fasting　HP +25, Speed ×1.15, Reiki +15, Attack ×1.75
Guiding　HP +40, Speed ×1.20, Reiki +20, Attack ×2.00
Subtle　HP +55, Speed ×1.25, Reiki +30, Attack ×2.25
Exalted　HP +70, Speed ×1.30, Reiki +40, Attack ×2.50
Nascent　HP +80, Speed ×1.35, Reiki +50, Attack ×2.75
Manifest　HP +100, Speed ×1.40, Reiki +70, Attack ×3.00
　Bonuses do not stack — reaching a new realm simply replaces the old values. HP and Reiki are flat additions to the cap; Speed and Attack are multipliers (Attack ×1.25 means +25% damage).
""",
    },
    "timed_effects": {
        "tags": "Interface,Status,Buffs,Debuffs",
        "summary": "The HUD panel for timed effects: buffs and negative effects shown separately. Draggable, follows the HUD scale.",
        "detail": """
Two independent panels that do not shift or scale along with the status bar:
　Negative effects: top-left by default.
　Buffs: bottom-right by default.

Dragging and saving: hold the right mouse button to drag a panel, and release to save its position; positions are stored alongside the vanilla HUD coordinate record.

Scaling: follows the vanilla HUD scale setting.

Visibility: a panel only ever shows your own effects, so other players never see them.

Negative effects (9): Starfire Burn, Frost Erosion, Scorpion Venom, Soul Snake Venom, Petrified, Bound, Flame Backlash, Alchemy Tribulation, Sacrificial Tribulation.
Buffs (6): Blazing Pill, Cold Flame Pill, Drying Pill, Explosion Pill, Invincible Pill, Restore Spirit Pill.

Also: the player avatar popup now has an "Ethereal Realm Guide" entry.
""",
    },
    "tribulation_rules": {
        "tags": "Realm,Tribulation,Alchemy,Judgment",
        "summary": "The full rules for the Sacrificial Tribulation on a deeply demonized death and the Alchemy Tribulation while refining.",
        "detail": """
There are two kinds of tribulation: the Sacrificial Tribulation that falls when a deeply demonized creature is killed by a player, and the Alchemy Tribulation while refining pills.

1. Sacrificial Tribulation (deeply demonized death)

Trigger: a deeply demonized creature killed by a player calls down a tribulation when it dies (kills credited to followers, the Void Ring and so on count as the player's).
Duration: 60 seconds, one strike every 6 seconds, and the first landing marker appears immediately instead of after 6 seconds.
Target: the landing spots are random within roughly 25 range of the corpse — a marker appears first and the bolt falls shortly after, and any player it hits takes damage.
Damage: an ordinary deeply demonized creature takes 10% of your maximum health, while an epic boss kills outright (100% of maximum health), ignoring invulnerability and damage absorption.
Warning: the bolt lands 1.5 seconds after the marker appears; players within 25 hear "The heavens have sensed it. A tribulation is coming!" and see a "Sacrificial Tribulation" countdown on the HUD, which disappears once they leave the area.

2. Alchemy Tribulation

Trigger: only mid-tier and high-tier pills can trigger it, with a 50% chance (the other 50% means no tribulation, and that batch always fails into a Failed Pill).
Pace: mid-tier strikes every 10 seconds, with the first landing marker at second 9; high-tier every 8 seconds, with the first marker at second 7.
Landing: the marker appears first and the bolt lands 1 second later, with a hit radius of 1.75.
Duration: the whole tribulation lasts 120 seconds, and you have to stay beside the furnace dodging until it ends before you can collect the pills.
Damage: the bolt empties your current health outright.
If you are hit: the furnace is destroyed on the spot, leaving only 5 Charcoal and 1 Failed Pill, with no materials returned.
Protection: a Disaster Breaking Pill makes you immune to the tribulation with no time limit, but it is lost on death and does nothing while merely carried.
Indicators: the negative-effect panel shows an "Alchemy Tribulation" countdown while refining, and dying to it records the cause of death as "Alchemy Tribulation Lightning".
Refining that never triggers it: using an exotic flame still owes the tribulation, but "special refining" (Soul Banner, Moonlight Condensing Vase, Dustflame Log and so on) always succeeds and never triggers one.
""",
    },
    "reiki_value": {
        "tags": "Realm,Reiki,Stats",
        "summary": "Starts at 50 and caps at 120; regenerates 3.3 per minute; below 5 you are weakened for 10 seconds.",
        "detail": """
[[图片:images/lingjie/anim/spirit_badge.png|In-game Reiki badge (flame icon, and the liquid level shows your current Reiki)]]

Reiki starts at 50 and grows as you advance realms, up to a maximum of 120.

Regenerates 3.3 Reiki per minute.

When Reiki runs dry (below 5) you enter a 10-second weakened state: vanilla drowsiness and grogginess stack up and you may fall asleep outright. When the weakness ends you regain 10 Reiki.

Reiki is spent by many techniques and artifacts — for example the Reiki Bow's ice infusion costs 20, and Starfall's meteor thrust costs 10.
""",
    },
    "corruption_overview": {
        "tags": "Demonization,Mechanics,World",
        "summary": "Creatures demonize at random as the world runs, and the threshold day is configurable. Past that day, epic bosses always demonize deeply.",
        "detail": """
Creatures roll a demonization level when they spawn. The threshold day can be set to 30 / 60 / 90 days; the default is 60.

Roll chances
　Before the threshold day: light 47.5%, moderate 47.5%, deep 5%.
　From the threshold day on: epic bosses always demonize deeply; other creatures get light 50%, moderate 25%, deep 25%.

Every demonized creature is hostile (neutral creatures such as Chester are excluded, as are special player relationships — spiders still will not attack Webber).

Demonization has three tiers, shown in game as "Demonization: Light / Moderate / Deep":
Light Demonization, Moderate Demonization, Deep Demonization.

Never demonized: shadow creatures (Crawling Horror, Terrorbeak, Shadow creatures, Ruins shadow creatures, Shadow Knight, Shadow Bishop, Shadow Rook, ocean shadow creatures and so on), passive critters, players, followers, walls, and equipment display models. Creatures hired by a player lose every demonization effect immediately.
""",
    },
    "corruption_light": {
        "tags": "Demonization,Light",
        "summary": "Demonized health uses a 1.60× discounted multiplier (the higher the base health, the closer to full); it applies Demonic Aura, Curse of Hunger and Shadow Slow to players.",
        "detail": """
Shown in game as "Light".

Core buff — Health
　Max health = max health before demonization × (1.60 − 65 ÷ (max health before demonization + 110))

Actual results:

　Base 100 → 129.05 (×1.290)
　Base 500 → 746.72 (×1.493)
　Base 2000 → 3138.39 (×1.569)
　Base 24000 → 38335.30 (×1.597)

The multiplier is fixed at 1.60; the lower the health, the more the 65 ÷ (health + 110) term takes away, so small creatures lose out while large ones approach the full multiplier. There is no adjustable decay threshold.

Player debuffs
Demonic Aura: within 5 range, players lose 1 sanity every 5 seconds.
Curse of Hunger: 30% chance when the player is hit by a creature; hunger drains 20% faster for 30 seconds.
Shadow Slow: 20% chance when the player is hit by a creature; movement speed −20% for 10 seconds.

On death it drops 1 to 3 Magic Core Shards plus the creature's own loot.
Creatures with 149 or less base health keep the light buff only and gain no demonization materials at all.
""",
    },
    "corruption_medium": {
        "tags": "Demonization,Moderate",
        "summary": "Demonized health uses a 1.95× discounted multiplier (the higher the base health, the closer to full); 12% damage reduction, a 5-second invulnerable shield at half health and 2% demonic reflection.",
        "detail": """
Shown in game as "Moderate".

Core buff — Health
　Max health = max health before demonization × (1.95 − 65 ÷ (max health before demonization + 110))

Actual results:

　Base 100 → 164.05 (×1.640)
　Base 500 → 921.72 (×1.843)
　Base 2000 → 3838.39 (×1.919)
　Base 24000 → 46735.30 (×1.947)

Core buff — Armour
All incoming external damage ×0.88 (a 12% physical damage reduction).

Player debuffs
Demonic Aura: within 10 range, players lose 3 sanity every 5 seconds.
Curse of Hunger: 30% chance when the player is hit by a creature; hunger drains 20% faster for 30 seconds.
Shadow Slow: 20% chance when the player is hit by a creature; movement speed −20% for 10 seconds.
Demonic Reflection: 10% chance when the creature takes damage from a player; reflects 2% of the damage.

Creature buffs
Conditional Vulnerability: dropping to 50% health or below triggers a shield; the creature takes no damage for 5 seconds, with a 5-minute cooldown. The shield shows as a red force field.

On death it drops 1 to 2 Magic Cores and 1 to 3 Magic Core Shards plus the creature's own loot.
""",
    },
    "corruption_deep": {
        "tags": "Demonization,Deep",
        "summary": "Demonized health uses a 2.35× discounted multiplier (the higher the base health, the closer to full); ignores every slow, plus Bone-Deep Poison, Mirror Confusion, Demonic Frenzy and Sacrificial Tribulation.",
        "detail": """
Shown in game as "Deep".

Core buff — Health
　Max health = max health before demonization × (2.35 − 65 ÷ (max health before demonization + 110))

Actual results:

　Base 100 → 204.05 (×2.040)
　Base 500 → 1121.72 (×2.243)
　Base 2000 → 4638.39 (×2.319)
　Base 24000 → 56335.30 (×2.347)

Core buff — Armour and size
All incoming external damage ×0.8 (a 20% physical damage reduction), plus +5 insulation / planar defense.
Movement speed +10%, and the creature is scaled up to 1.2×. (The three epic bosses — Eclipsed Crystalwing Lion, Blazing Rock Scorpion Dragon and Soul-devouring Snake — keep their original look and are not enlarged.)

Core buff — Slow immunity
Ignores every slow: it only accepts movement multipliers greater than 1.

Player debuffs
Demonic Aura: within 10 range, players lose 5 sanity every 5 seconds.
Curse of Hunger: 30% chance when the player is hit by a creature; hunger drains 20% faster for 30 seconds.
Shadow Slow: 20% chance when the player is hit by a creature; movement speed −20% for 10 seconds.
Demonic Reflection: 10% chance when the creature takes damage from a player; reflects 5% of the damage, capped at 75 damage per hit.
Mirror Confusion: 10% chance on attack; the player's movement direction flips 180° for the next 5 seconds.

Creature buffs
Conditional Vulnerability: while health is between 30% and 50% (>30% and ≤50%) it triggers a 12-second invulnerable shield, with a 5-minute cooldown. The shield shows as a red force field.
Bone-Deep Poison: normal attacks carry bone-eating poison. One poisoning lasts 240 seconds and does not stack (the timer can be refreshed, capped at 240 seconds), and the first tick lands the moment it hits.
　0 to 80 seconds: 6 damage every 10 seconds
　80 to 160 seconds: 10 damage every 10 seconds
　160 to 240 seconds: 14 damage every 10 seconds
　Antidote: a Stillness Pill works, and so does a gland. A gland antidote actually deducts "50 + the gland's normal healing"; if that would drop you below 5 health you keep 5.
Shadow Familiar: when it wakes up it summons one extra shadow with half the creature's base max health. The shadow carries no demonization effects and no armour, and a Soul Banner can refine it directly. Each body only summons it once.
Feeding on Remains: whenever a player dies, any deeply demonized boss within 40 of the death spot heals 10% of the health it has lost.
Demonic Frenzy: dropping to 30% health or below triggers a frenzy — damage +30%, its damage reduction and planar defense stop working (the damage multiplier and the +5 planar defense are removed), and it cannot heal at all while frenzied (every heal is blocked).
　Only epic bosses also get their skill cooldowns halved.
　The frenzy lasts 300 seconds (5 minutes) and can only trigger again once it has ended.
Sacrificial Tribulation: on death it calls down a tribulation for 60 seconds, striking every 6 seconds. The landing spots are random within roughly 25 range of the corpse — a marker appears first and the bolt falls shortly after, damaging any player it hits. (Kills credited to followers, the Void Ring and so on count as the player's and still trigger the tribulation.) an ordinary deeply demonized creature takes 10% of your maximum health, while an epic boss kills outright (100% of maximum health, ignoring invulnerability and damage absorption). The bolt lands 1.5 seconds after the marker appears, and the very first marker appears immediately instead of after 6 seconds.
　Warning: players within 25 of the landing spot hear "The heavens have sensed it. A tribulation is coming!" and see a "Sacrificial Tribulation" countdown on the HUD; it disappears once they leave the area.

On death it adds 1 Magic Crystal plus the creature's own loot, and doubles the vanilla drop amounts.
　Exception: the three epic bosses with their own complete loot tables — Eclipsed Crystalwing Lion, Blazing Rock Scorpion Dragon and Soul-devouring Snake — are neither doubled nor given a Magic Crystal.
""",
    },
    "corruption_drops": {
        "tags": "Demonization,Drops,Materials",
        "summary": "Light demonization drops Magic Core Shards, moderate drops Magic Cores, deep drops a Magic Crystal; vanilla creatures drop according to their demonization tier.",
        "detail": """
Magic Core Shard: killing a lightly demonized creature drops 1 to 3 shards (creatures with 149 or less base health get no extra materials).

Magic Core: dropped by bosses and demonic beasts; 99 Magic Core Shards craft one; moderately demonized creatures drop 1 to 2. Cannot be destroyed or deconstructed.

Magic Crystal: dropped by demonic beasts; 20 Magic Cores craft one; deeply demonized creatures drop 1. Cannot be destroyed or deconstructed.

Vanilla creatures drop Magic Core Shards and Magic Cores according to their demonization tier. A vanilla creature at deep demonization drops only 1 Magic Crystal, while large demonic beasts drop 2.
""",
    },
    "alchemy_rules": {
        "tags": "Alchemy,Pills,Rules",
        "summary": "Refining with a Wasteland Flame has a base 50% success rate; an exotic flame raises it to 100%. Failures become a Failed Pill and materials are not returned.",
        "detail": """
Refining uses a Wasteland Flame. Pills that do not trigger a tribulation have a 50% success chance either way, and refining time never changes.

Pills that can trigger a pill tribulation: 50% chance of no tribulation, in which case refining always fails and produces a Failed Pill; 50% chance of a lightning tribulation, and if you dodge it successfully the pill is refined. Taking a Disaster Breaking Pill skips the tribulation check.

Materials must be placed in the Alchemy Furnace in the listed amounts — more is fine, less is not. A failed refinement becomes a Failed Pill and the materials are not returned, so refine carefully.

Refining with an exotic flame raises the success chance to 100% — a strong exotic flame always succeeds, and it does not change the tribulation check (a pill that owes a tribulation still gets one).

Using a full exotic flame as fuel does not consume it (it only acts as the furnace fire); only split flames are consumable, and one is used up per batch.
""",
    },
    "pill_tiers": {
        "tags": "Alchemy,Pills,Tribulation,Stats",
        "summary": "Refining time, output and tribulation parameters for the four tiers: low (yellow), moderate (mystic), high (earth) and heaven (sky).",
        "detail": """
Pills come in four tiers: low (yellow), moderate (mystic), high (earth) and heaven (sky).

Low (refining time 2 minutes)
Refined with a Wasteland Flame, pills that do not trigger a tribulation have a 50% chance; with an exotic flame the chance is 100%.
99% chance to make 3 at a time, 1% chance to make 5.

Moderate (refining time 4 minutes)
Refined with a Wasteland Flame the chance is 50%, and a failure produces a Failed Pill; with an exotic flame the chance is 100%.
99% chance to make 1 at a time, 1% chance to make 2.
Moderate pill tribulation: a lightning strike every 10 seconds that kills outright, always telegraphed; the marker shows at second 9 and the bolt lands 1 second later, lasting 120 seconds. Dodge it or the refinement fails. Failing to dodge destroys the furnace and leaves 5 [images/inventoryimages1/charcoal.png] Charcoal and 1 Failed Pill.

High (refining time 8 minutes)
Refined with a Wasteland Flame the chance is 20%, and a failure produces a Failed Pill; with an exotic flame the chance is 100%.
Only 1 can be made at a time.
High pill tribulation: a lightning strike every 8 seconds that kills outright, always telegraphed; the marker shows at second 7 and the bolt lands 1 second later, lasting 120 seconds. Dodge it or the refinement fails. Failing to dodge destroys the furnace and leaves 5 [images/inventoryimages1/charcoal.png] Charcoal and 1 Failed Pill.

Tribulation readout: while refining, the HUD shows an "Alchemy Tribulation" countdown (driven by the furnace's remaining time); dying to it records the death cause as "Alchemy Tribulation Lightning".

Heaven (sky)
Not implemented yet.
""",
    },
    "lj_moon_vase": {
        "tags": "Artifact,Special Refining,Alchemy",
        "summary": "No pill tribulation and a 100% success rate; used on the Spirit Jade Table to absorb world reiki at night.",
        "detail": """
Special refining (no pill tribulation, 100% success)

Refining time 4 minutes.

Cannot be destroyed normally, but can be deconstructed with a Deconstruction Staff.

Rain prayer: right-click and pick "Pray for Rain" to spend 20 spirit fluid and force continuous rain; it clears itself after 10 minutes, and praying again restarts that timer. Spirit fluid caps at 100, and a vase that is short of it reports "Not enough spirit fluid".
""",
    },
    "lj_reiki_gourd": {
        "tags": "Artifact,Storage,Flames",
        "summary": "An 8-slot gourd that absorbs exotic flames and stores pills; it follows the player and automatically absorbs ownerless exotic flames within 16 range.",
        "detail": """
Special refining (no pill tribulation, 100% success)

Refining time 4 minutes.

Cannot be destroyed, and cannot be deconstructed with a Deconstruction Staff.

Absorbs exotic flames and stores pills, 8 slots.
Right-click in the inventory to open or close it (there is only one container — the one opened from a following gourd is the same one). While open it stays open; opening other chest-like items will not close the gourd.
Pick it up with the mouse, drop it on the ground and it follows you. While following, any ownerless exotic flame within 16 range flies into the gourd on its own, and once absorbed it belongs to the gourd's owner.
Picking the gourd up from your inventory or a backpack with the mouse and putting it down again returns it to the slot it came from whenever that slot is still usable.
While following: left-click opens or closes the gourd, right-click recalls it.
""",
    },
    "lj_soul_banner": {
        "tags": "Artifact,Shadow Creatures,Soul Refining",
        "summary": "Plant it in the ground to absorb shadow creatures and turn them into Magic Cores; giving it a Purple Scale Demon Flame unlocks Soul Refining.",
        "detail": """
Special refining (no pill tribulation, 100% success)

Refining time 4 minutes.

Cannot be destroyed or deconstructed.

Giving it a Purple Scale Demon Flame unlocks the Soul Refining skill.
Planted in the ground it automatically absorbs the 4 vanilla shadow creatures, plus the shadow clones produced by deep demonization; each one absorbed becomes a Magic Core dropped right below the banner.
　Other shadow creatures (Shadow Knight, Shadow Bishop, Shadow Rook and so on) are not absorbed.
""",
    },
    "lj_failed_pill": {
        "tags": "Pills,Low,Penalty",
        "summary": "The product of a failed refinement. Using it costs 30 sanity and 30 health, and restores 30 hunger.",
        "detail": """
A pill that failed to refine.

Using it costs 30 sanity and 30 health, and restores 30 hunger.

A failed refinement always yields a Failed Pill and never returns the materials, so open the furnace with care.
""",
    },
    "lj_ningqi_pill": {
        "tags": "Pills,Low,Food",
        "summary": "A low-tier pill that restores 50 hunger; werepigs like it too.",
        "detail": """
Low-tier pill (yellow), refining time 2 minutes.

Effect: restores 50 hunger, and werepigs like it too.
""",
    },
    "lj_warming_pill": {
        "tags": "Pills,Low,Temperature",
        "summary": "A low-tier pill that warms you and keeps you from freezing for 2 days.",
        "detail": """
Low-tier pill (yellow), refining time 2 minutes.

Effect: warming, prevents freezing cold, lasts 2 days.
""",
    },
    "lj_cooling_pill": {
        "tags": "Pills,Low,Temperature",
        "summary": "A low-tier pill that cools you and keeps you from overheating for 2 days.",
        "detail": """
Low-tier pill (yellow), refining time 2 minutes.

Effect: cooling, prevents overheating, lasts 2 days.
""",
    },
    "lj_stillness_pill": {
        "tags": "Pills,Low,Realm",
        "summary": "Take it after losing a realm stage to steady your mind and keep cultivating.",
        "detail": """
Low-tier pill (yellow), refining time 2 minutes.

Effect: taken after losing a stage on death, it steadies your mind and lets you keep cultivating.

This is the pill required to regain the ability to cultivate after a death penalty — without it you stay stuck.

Extra use: it is also an antidote — taking one removes Soul Snake Venom outright (see Bone-Deep Poison under "Deep Demonization").
""",
    },
    "lj_restore_pill": {
        "tags": "Pills,Moderate,Reiki,Tribulation",
        "summary": "A moderate tribulation pill: reiki surges, restoring 1 Reiki every 2 seconds for 1 day.",
        "detail": """
Moderate pill (mystic), refining time 4 minutes. Can trigger a pill tribulation.

Effect: reiki surges, restoring 1 Reiki every 2 seconds for 1 day.
""",
    },
    "lj_explosion_pill": {
        "tags": "Pills,Moderate,Damage",
        "summary": "A moderate pill that raises damage by 30% for 3 minutes.",
        "detail": """
Moderate pill (mystic), refining time 4 minutes.

Effect: +30% damage for a short time, lasting 3 minutes.
""",
    },
    "lj_drying_pill": {
        "tags": "Pills,Moderate,Moisture",
        "summary": "A moderate pill that makes you immune to wetness for 5 days.",
        "detail": """
Moderate pill (mystic), refining time 4 minutes.

Effect: immune to wetness for 5 days.
""",
    },
    "lj_invincible_pill": {
        "tags": "Pills,Moderate,Survival",
        "summary": "A moderate pill: for 30 seconds your health cannot drop below 1.",
        "detail": """
Moderate pill (mystic), refining time 4 minutes.

Effect: a 30-second "invincible" state — your health cannot drop below 1 for 30 seconds, and nothing else changes.
""",
    },
    "lj_bigu_pill": {
        "tags": "Pills,Moderate,Realm",
        "summary": "A moderate pill: meditate 10 seconds on the Enlightenment Tempering Seat to advance from Sinew to Fasting.",
        "detail": """
Moderate pill (mystic), refining time 4 minutes.

Effect: take it and meditate 10 seconds on the Enlightenment Tempering Seat to advance from the Sinew realm to Fasting.
""",
    },
    "lj_yinqi_pill": {
        "tags": "Pills,Moderate,Realm",
        "summary": "A moderate pill: meditate 10 seconds on the Enlightenment Tempering Seat to advance a realm.",
        "detail": """
Moderate pill (mystic), refining time 4 minutes.

Effect: take it and meditate 10 seconds on the Enlightenment Tempering Seat to advance from Fasting to Subtle.
""",
    },
    "lj_ruwei_pill": {
        "tags": "Pills,Moderate,Realm,Tribulation",
        "summary": "A moderate tribulation pill that helps a Guiding cultivator break through to Subtle.",
        "detail": """
Moderate pill (mystic), refining time 4 minutes. Can trigger a pill tribulation.

Effect: take it and meditate 10 seconds on the Enlightenment Tempering Seat to break the boundary from Guiding to Subtle and grow stronger.
""",
    },
    "lj_extraordinary_pill": {
        "tags": "Pills,High,Realm,Tribulation",
        "summary": "A high tribulation pill that raises a Subtle cultivator to Exalted.",
        "detail": """
High pill (earth), refining time 8 minutes. Can trigger a pill tribulation.

Effect: take it and meditate 10 seconds on the Enlightenment Tempering Seat to raise a Subtle cultivator to the Exalted level.
""",
    },
    "lj_heying_pill": {
        "tags": "Pills,High,Realm,Tribulation",
        "summary": "A high tribulation pill: meditate 10 seconds on the Enlightenment Tempering Seat to empower a Nascent cultivator.",
        "detail": """
High pill (earth), refining time 8 minutes. Can trigger a pill tribulation.

Effect: take it and meditate 10 seconds on the Enlightenment Tempering Seat to empower a Nascent-level cultivator.
""",
    },
    "lj_disaster_pill": {
        "tags": "Pills,High,Tribulation,Survival",
        "summary": "A high pill that makes you immune to pill tribulation lightning until it ends.",
        "detail": """
High pill (earth), refining time 8 minutes.

Effect: immune to pill tribulation lightning until it ends.

It is used to skip the lightning check when refining other pills — with no tribulation the refinement always fails and produces a Failed Pill, so taking a Disaster Breaking Pill skips the check and succeeds outright.
""",
    },
    "lj_juling_pill": {
        "tags": "Pills,High,Realm,Tribulation",
        "summary": "A high tribulation pill, extremely rare, that breaks through to the Manifest realm.",
        "detail": """
High pill (earth), refining time 8 minutes. Can trigger a pill tribulation.

Effect: take it and meditate 10 seconds on the Enlightenment Tempering Seat — extremely rare, it breaks through to the Manifest realm.
""",
    },
    "lj_reiki_pill": {
        "tags": "Pills,Moderate,Reiki",
        "summary": "A moderate pill that restores 30 Reiki.",
        "detail": """
Moderate pill (mystic), refining time 4 minutes.

Effect: restores 30 Reiki.
""",
    },
    "lj_magic_debris": {
        "tags": "Materials,Demonic Energy",
        "summary": "The lowest-grade demonic crystal, dropped by lightly demonized creatures; it can be crafted into Magic Cores.",
        "detail": """
Source: killing lightly demonized creatures drops 1 to 3.

Advanced use: 99 Magic Core Shards craft 1 Magic Core, and they are also the main material of the Tempered Iron Spirit Sword.

Cannot be destroyed or deconstructed.
""",
    },
    "lj_magic_core": {
        "tags": "Materials,Demonic Energy,Crafting",
        "summary": "Crafted from 99 Magic Core Shards. Dropped by bosses, demonic beasts and moderately demonized creatures.",
        "detail": """
Crafting: 99 Magic Core Shards craft one.

Source: killing bosses and demonic beasts drops them; moderately demonized creatures drop 1 to 2.

Cannot be destroyed or deconstructed.

Craftable in the <Ethereal Realm>, <Magic> and <Refine> tabs.

Advanced use: 20 Magic Cores craft 1 Magic Crystal, and they are the core material of many pills, structures and artifacts.
""",
    },
    "lj_magic_crystal": {
        "tags": "Materials,Demonic Energy,Crafting",
        "summary": "Crafted from 20 Magic Cores. Dropped by demonic beasts and deeply demonized creatures; essential for high-tier pills and armour.",
        "detail": """
Crafting: 20 Magic Cores craft one.

Source: killing demonic beasts drops them; deeply demonized creatures drop 1.

Cannot be destroyed or deconstructed.

A vanilla creature at deep demonization drops only 1 Magic Crystal, while large demonic beasts drop 2.

Craftable in the <Ethereal Realm>, <Magic> and <Refine> tabs.
""",
    },
    "lj_scorpion_dragon_bone": {
        "tags": "Materials,Boss Drop",
        "summary": "The bones of the Blazing Rock Scorpion Dragon, the epic boss of the ancient ruins (Remains Island); used to craft Keel Armour and the Spirit Manifesting Pill.",
        "detail": """
Source: killing the epic boss "Blazing Rock Scorpion Dragon" at the Remains Altar (ancient ruins) drops 1.

Use: core material of Keel Armour and the Spirit Manifesting Pill.
""",
    },
    "lj_amethyst_shell": {
        "tags": "Materials,Boss Drop",
        "summary": "The crystal shell of the Eclipsed Crystalwing Lion; used to craft the Crystal Crown and the Nascent Union Pill.",
        "detail": """
Source: killing the epic boss "Eclipsed Crystalwing Lion" drops 1.

Use: core material of the Crystal Crown and the Nascent Union Pill.
""",
    },
    "lj_lion_bone": {
        "tags": "Materials,Boss Drop",
        "summary": "The bones of the Eclipsed Crystalwing Lion.",
        "detail": """
Source: killing the epic boss "Eclipsed Crystalwing Lion" drops 1.
""",
    },
    "lj_bat_blood": {
        "tags": "Materials,Demon Beast Drop",
        "summary": "Essence blood of the Shadow Blood Bat; used to craft Keel Armour, the Crystal Crown and the Extraordinary Pill, and it can also refill armour durability outright.",
        "detail": """
Source: killing a Shadow Blood Bat on Butterfly Island always drops 1.

Use: Keel Armour, Crystal Crown, Extraordinary Pill.

1 Blood Bat Essence restores Keel Armour / Crystal Crown to full durability.

Stack limit 20.
""",
    },
    "lj_soul_snake_skin": {
        "tags": "Materials,Boss Drop",
        "summary": "The hide of the Soul-devouring Snake; used to craft the Extraordinary Pill.",
        "detail": """
Source: killing the hidden boss "Soul-devouring Snake" drops 3.

Use: Extraordinary Pill.
""",
    },
    "lj_snake_skin": {
        "tags": "Materials,Boss Mechanic",
        "summary": "Scales the Soul-devouring Snake drops every 2000 damage taken; players cannot pick them up, but they can be burned with an exotic flame.",
        "detail": """
Source: the Soul-devouring Snake drops one every 2000 health of damage taken; players cannot pick them up, and they can be burned with an exotic flame.

Mechanic: once the Soul-devouring Snake first falls to 50% health it actively seeks out and eats the scales to heal itself, 1000 health each. So burn the scales lying on the ground with an exotic flame as soon as possible.
""",
    },
    "lj_reiki_cutgrass": {
        "tags": "Materials,Spirit Plants,Alchemy",
        "summary": "The part harvested from Spirit-Melting Grass; the base material of nearly every pill.",
        "detail": """
Source: harvesting "Spirit-Melting Grass" gives 1 [images/inventoryimages1/cutgrass.png] Cut Grass plus 1 Harvested Spirit-Melting Grass.

Use: almost every pill needs it — Qi Condensing Pill, Flame Warming Pill, Cold Flame Pill, Stillness Pill, Reiki Pill, Drying Pill, Invincible Pill, Bigu Pill and Restore Spirit Pill — as well as repairing the Remains Altar.

Note: in game "Spirit-Melting Grass" is the plant growing in the ground, while "Harvested Spirit-Melting Grass" is the material you put in the furnace — they are two different items.
""",
    },
    "lj_reiki_dug_grass": {
        "tags": "Materials,Spirit Plants",
        "summary": "The root left behind when Spirit-Melting Grass is dug up; it can be replanted.",
        "detail": """
Source: 5% chance of an extra one when harvesting "Spirit-Melting Grass".

Use: transplanting Spirit-Melting Grass elsewhere.
""",
    },
    "lj_red_magic_cutflower": {
        "tags": "Materials,Spirit Plants,Alchemy",
        "summary": "The part harvested from a Dragon Claw Flower; used in moderate and high-tier pills.",
        "detail": """
Source: harvesting a "Dragon Claw Flower" gives 1 [images/inventoryimages2/petals.png] Petals plus 1 Harvested Dragon Claw Flower.

Use: Invincible Pill, Nascent Union Pill.
""",
    },
    "lj_red_magic_dug_flower": {
        "tags": "Materials,Spirit Plants",
        "summary": "The root left behind when a Dragon Claw Flower is dug up.",
        "detail": """
Source: 5% chance of an extra one when harvesting a "Dragon Claw Flower".

Use: transplanting Spider Lilies elsewhere.
""",
    },
    "lj_purple_magic_bloom": {
        "tags": "Materials,Spirit Plants,Repair",
        "summary": "Petals chopped from an Amethyst Form Flower; used to repair the Remains Altar.",
        "detail": """
Source: chopping an "Amethyst Form Flower". An Eclipsed Crystalwing Lion usually guards it, and nothing drops while the lion is alive.

Use: repairing the Remains Altar needs 1.
""",
    },
    "lj_purple_magic_flower": {
        "tags": "Spirit Plants,Materials,Boss",
        "summary": "Grows near the Mandrake plains and spawns one flower within 4 range every day; an Eclipsed Crystalwing Lion always guards it.",
        "detail": """
Spawn: near the Mandrake plains, only one per world. The world keeps a record of whether that flower has been generated, so an older save grows one when you enter it, and a flower that vanishes abnormally is put back (the record is saved).

Behaviour: spawns one flower within 4 range of itself every day.

Cannot be burned and must be chopped with an axe. An Eclipsed Crystalwing Lion stands beside it. It cannot be transplanted.
It regrows 10 days after being harvested.

While the lion is alive the Amethyst Form Flower cannot be chopped for loot, so deal with the Eclipsed Crystalwing Lion first.
Once the lion dies the flower can be harvested immediately, once; the lion respawns on its own 20-day timer (the panel shows "Moon Lion respawn remaining"), and when it comes back the flower is restored.

Use: repairing the Remains Altar.
""",
    },
    "lj_alchemy_furnace": {
        "tags": "Structures,Alchemy",
        "summary": "The core alchemy structure. 5 slots: 4 for materials and 1 for fuel.",
        "detail": """
Can be destroyed with a hammer, returning 2 [images/inventoryimages1/boards.png] Boards, 2 [images/inventoryimages1/cutstone.png] Cut Stone and 5 [images/inventoryimages2/nitre.png] Nitre.

5 slots: 4 for materials and 1 for fuel (Wasteland Flame / exotic flame), plus a refine button.

Craftable in the <Ethereal Realm> and <Structures> tabs.
""",
    },
    "lj_wudao_chair": {
        "tags": "Structures,Realm,Meditation",
        "summary": "The dedicated building for secluded meditation. It steadies your realm, restores sanity and Reiki, stops hunger drain and grants 1 experience every 10 seconds.",
        "detail": """
Can be destroyed with a hammer, returning 6 [images/inventoryimages1/cutgrass.png] Cut Grass, 6 [images/inventoryimages3/rocks.png] Rocks and 3 [images/inventoryimages2/nightmarefuel.png] Nightmare Fuel.

The dedicated meditation structure needed to raise stages and realms. Meditating steadies your realm, restores 1 sanity and 1 Reiki every 3 seconds, and stops hunger drain.

An idle-time favourite: 1 experience every 10 seconds.

Stages 3 / 6 / 9 of every realm need meditation; from the Guiding realm onward you also need the matching pill alongside the meditation.

Craftable in the <Ethereal Realm> and <Structures> tabs.
""",
    },
    "lj_reiki_table": {
        "tags": "Structures,Reiki",
        "summary": "A tier-2 science structure. Put a Moonlight Condensing Vase in it at night to absorb world reiki (at least 30 seconds).",
        "detail": """
Can be destroyed with a hammer; crafted with tier-2 science, and destroyed it returns 2 [images/inventoryimages2/goldnugget.png] Gold Nuggets, 2 [images/inventoryimages2/log.png] Logs and 5 [images/inventoryimages1/cutstone.png] Cut Stone.

Put a Moonlight Condensing Vase in it at night to absorb world reiki; note that it needs at least 30 seconds.
""",
    },
    "lj_reiki_tablelamp": {
        "tags": "Structures,Light",
        "summary": "A 2-slot light source. A split flame adds 10 range of light for 8 minutes; an exotic flame lights the area permanently.",
        "detail": """
Can be destroyed with a hammer, returning no materials.

2 slots. A split flame increases the lit radius by 10 each and lasts 8 minutes; a full exotic flame provides light permanently.

Craftable in the <Ethereal Realm>, <Structures> and <Light> tabs.
""",
    },
    "lj_reiki_cultivatepool": {
        "tags": "Structures,Spirit Plants,Unreleased",
        "summary": "Not implemented in the mod source, so it is hidden from the site for now.",
        "detail": """
⚠️ This content is not implemented in the mod source, so the entry is hidden and never shown on the site.

How this was checked (against the lj_mod source):
- A full code search finds no prefab called lj_reiki_cultivatepool
- It is not registered in the structures group of scripts/main/config/prefab_groups.lua
- scripts/main/localization/language_zh.lua has no matching Chinese name
- Only scripts/prefabs/alchemy/lj_moon_vase.lua carries a comment: the demon-tree cultivation use is not wired up yet, and the consumption ratio is still to be decided.

The originally planned description (for when it ships):

Can be destroyed with a hammer.
Put a Soul Tree Root in it to let it grow.
""",
    },
    "lj_huangjie_box": {
        "tags": "Structures,Storage",
        "summary": "A large 3×11 + 1×10 chest; Magic Cores add collection, sapphires add freshness and Magic Crystals unlock infinite stacking.",
        "detail": """
Can be destroyed with a hammer and burned by torches; destroying it returns 2 [images/inventoryimages1/boards.png] Boards, 1 [images/inventoryimages2/papyrus.png] Papyrus and 2 [images/inventoryimages1/cutstone.png] Cut Stone.

Stores 3×11 + 1×10 slots and behaves like a vanilla chest.

There is no open limit, so several players can have the same box open at once.

Extra features:
Top left "Sort" — adds a sorting function (sorting no longer dumps the excess of an infinitely stacked item onto the ground, and identical items are ordered by stack size, biggest first).
Bottom right "Seal" — closes the chest.
Lower right "Safe Deposit" — for items the chest already holds, clicking safe deposit puts everything of yours into the chest in one go.

Infusions:
Upgrading: hold the material and left-click the chest — one material is consumed per upgrade.

Giving it a Magic Core adds collection (the range can be set to 10 / 50 / 100 / 200 / 500 / All in the mod settings; the default is 10).
Giving it a sapphire adds freshness.
Giving it a Magic Crystal unlocks infinite stacking.

Craftable in the <Ethereal Realm>, <Structures> and <Containers> tabs.

[[图片:images/lingjie/anim/huangjie_box_ui.png|Chest interface: 3×11 slots on top plus a single 1×10 row below; the buttons are Sort, Collect, Fresh, Safe Deposit and Seal]]
""",
    },
    "lj_cuiju_box": {
        "tags": "Structures,Storage,Weapons",
        "summary": "A 7×7 + 1 weapon and armour cabinet; the first slot displays a weapon, and a Magic Crystal slowly repairs durability.",
        "detail": """
Can be destroyed with a hammer and burned by torches; destroying it returns 2 [images/inventoryimages1/boards.png] Boards, 1 [images/inventoryimages2/papyrus.png] Papyrus and 2 [images/inventoryimages1/cutstone.png] Cut Stone.

Stores weapons and armour, 7×7 + 1 slots. The first slot displays a weapon — putting a weapon in on its own shows it off.

Giving it a Magic Crystal slowly restores durability.

Craftable in the <Ethereal Realm>, <Structures> and <Containers> tabs.

[[图片:images/lingjie/anim/cuiju_box_ui.png|Weapon case interface: a 7×7 grid with a separate slot above it for displaying a weapon]]
""",
    },
    "lj_ordinary_sword": {
        "tags": "Weapons,Melee,Early Game",
        "summary": "45 attack and +10% movement speed while held; a transitional blade repaired with Magic Core Shards.",
        "detail": """
45 attack and +10% movement speed while held; its attack range matches other ordinary weapons.

100 durability (100 hits), repairable with Magic Core Shards — 1 shard restores 10 durability.

Role: an early-game portable melee cultivation weapon, the basic blade that carries you to mid-game artifacts, covering self-defence and light exploration.

Craftable in the <Ethereal Realm> and <Weapons> tabs.
""",
    },
    "lj_reiki_bow": {
        "tags": "Weapons,Ranged,Freeze,Artifact",
        "summary": "78 attack, 20% crit, plus Ice Erosion and 10 planar damage; right-click Ice Infusion deals 300 damage and freezes.",
        "detail": """
Cannot be destroyed or deconstructed. Exotic flames are awkward to keep in the inventory or a backpack, so open the Spirit Void Gourd while crafting — the game only needs to be able to see it.

Base stats
78 attack, 20% crit chance, crit damage ×1.8.
Hits apply the "Ice Erosion" debuff: 8 seconds, 16 damage every 0.5 seconds, refreshed on another hit. Adds 10 planar damage.
Range 10, durability 200. Attack interval matches ordinary weapons such as the spear. Each attack costs 1 durability.
At 0 durability it does not disappear and you can keep attacking, but damage drops to 10. Durability can be refilled with Magic Cores — 1 core fills 100.

Ice Erosion debuff: each hit adds one stack of freeze, and reaching the creature's freeze resistance threshold triggers Frozen.
　Small creatures: 2 stacks = frozen for 2 seconds
　Medium creatures: 3 stacks = frozen for 1.5 seconds
　Large creatures: 5 stacks = frozen for 1 second

Skill: Ice Infusion (right-click)
Costs 20 Reiki, fires one huge arrow for 300 damage and freezes the target for 3 seconds. 12-second cooldown.

Killing any creature restores 5 Reiki.

Craftable in the <Ethereal Realm> and <Weapons> tabs.
""",
    },
    "lj_star_sword": {
        "tags": "Weapons,Melee,Fire,Artifact",
        "summary": "88 attack, 22% crit, plus Scorch; it hits harder the longer you swing, and right-click Meteor Thrust dashes invulnerably for 150 damage.",
        "detail": """
Cannot be destroyed or deconstructed. Exotic flames are awkward to keep in the inventory or a backpack, so open the Spirit Void Gourd while crafting — the game only needs to be able to see it.

Base stats
88 attack, 22% crit chance, crit damage ×2.
Hits apply the "Scorch" debuff: 8 seconds, 16 fire damage every 0.5 seconds, refreshed on another hit. Adds 10 planar damage.
300 durability. Attack interval and attack range both match ordinary weapons such as the spear. Each attack costs 1 durability.
At 0 durability it does not disappear and you can keep attacking, but damage drops to 10. Durability can be refilled with Magic Cores — 1 core fills 100.

Charge mechanic
The weapon charges itself as you attack (25% every 5 attacks), and at 100% it enters the "Starfall state".
Stop attacking for 10 seconds and the charge drops back to 0.
In the Starfall state attacks hit harder, gaining 5 damage per hit.

Skill: Meteor Thrust (right-click)
Costs 10 Reiki and dashes forward a short distance (borrowed from the Wigfrid's charged spear), immune to damage during the dash (about 0.8 seconds of invulnerability), dealing 150 damage (140 base + 10 planar damage), with a 2-second cooldown.

[[图片:images/lingjie/anim/star_sword_charge.png|Blade effect at full charge]]

[[图片:images/lingjie/anim/star_sword_hit.png|Starfall hit effect]]

Killing any creature restores 5 Reiki.

Craftable in the <Ethereal Realm> and <Weapons> tabs.
""",
    },
    "lj_keel_armour": {
        "tags": "Armour,Defense,Durability",
        "summary": "1500 durability and 80% defence to start; out of combat it mends itself via Blood Mending.",
        "detail": """
Special crafting: unlocked near the restored Remains Altar, and every craft still needs you to be near it.

Base stats
1500 durability, 80% defence to start.
Each Magic Crystal given raises defence by 1%, up to 90.
1 planar defence, up to 10.
1 Blood Bat Essence restores full durability.

Blood Mending
Only triggers out of combat — that is, only when the player has taken no damage for 5 seconds.
Above 30% health: costs 1 health every 2 seconds and restores 10 durability.
Below 30% health: no health is spent and no durability is restored.
At 0 durability it does not disappear, but it offers no protection at all.

Craftable in the <Ethereal Realm> and <Armour> tabs.
""",
    },
    "lj_crystalcrown": {
        "tags": "Armour,Defense,Durability",
        "summary": "A head piece built to the same spec as Keel Armour; wearing both makes you immune to Mirror Confusion.",
        "detail": """
Special crafting: unlocked near the restored Remains Altar, and every craft still needs you to be near it.

Base stats
1500 durability, 80% defence to start.
Each Magic Crystal given raises defence by 1%, up to 90.
1 planar defence, up to 10.
1 Blood Bat Essence restores full durability.

Blood Mending
Only triggers out of combat — that is, only when the player has taken no damage for 5 seconds.
Above 30% health: costs 1 health every 2 seconds and restores 10 durability.
Below 30% health: no health is spent and no durability is restored.
At 0 durability it does not disappear, but it offers no protection at all.

Set bonus: wearing Keel Armour and the Crystal Crown together makes you immune to Mirror Confusion.

Craftable in the <Ethereal Realm> and <Armour> tabs.
""",
    },
    "lj_void_ring": {
        "tags": "Artifact,Tool,Starting Gift",
        "summary": "A ring you start with; one slot holds a Wasteland Flame or an exotic flame, and once equipped you can ignite targets from a distance.",
        "detail": """
Special crafting: unlocked near the restored Remains Altar, and every craft still needs you to be near it.

Cannot be destroyed, and cannot be deconstructed with a Deconstruction Staff.

You start with it. One slot holds a Wasteland Flame or an exotic flame. With a full exotic flame inside, equipping the ring lets you right-click a target to ignite it at range like a Fire Staff: it fires a fireball, range 8 to 10, costing 10 Reiki.
The hit works exactly like a Fire Staff: it ignites the target, or tops up a burnable fuel device by one fuel; it also thaws frozen targets, wakes sleeping ones and makes them hate you. It deals no damage of its own, and with no exotic flame inside there is no ignite action at all.

Craftable in the <Ethereal Realm> and <Tools> tabs.
""",
    },
    "zhenfa_overview": {
        "tags": "Formations,Mechanics",
        "summary": "A formation is made of flags and a pivot; the flags mark the area and the pivot takes a core to start it.",
        "detail": """
Design: a formation is made of a number of flags plus a pivot, and provides some practical effect inside its area.

Area (1 turf = 4 game units)
　At least 4 flags are needed to form a formation.
　Flags must be at least 3 turf (12 units) apart and at most 6 turf (24 units) apart.
　The bounding rectangle of the whole formation may not exceed 12 turf (48 units) on either side.
　The area follows how the flags connect — a circle, a square, a rectangle — like a dashed ring drawn on the map showing roughly where it reaches.

Starting it: the pivot needs a core to start it. The Spirit Formation Pivot has 4 slots, so several cores can be placed for multiple effects.
Duplicates of the same core do not stack their numbers; they just union the different effect slots.

There are currently 4 formations: Four Seasons Harmony, Vitality Rejuvenation, Spirit-Banishing Demon-Locking and Extreme Temperature Ward.
""",
    },
    "lj_flag": {
        "tags": "Structures,Formations",
        "summary": "Marks out a formation's area. Connects up to 3 tiles away.",
        "detail": """
Can be destroyed with a hammer, returning no materials.

Marks out a formation's area, connecting up to 3 tiles away.

The area follows how the flags connect — a circle, a square, a rectangle — like a dashed ring drawn on the map showing roughly where it reaches.

Craftable in the <Ethereal Realm> and <Structures> tabs.
""",
    },
    "lj_supernatural_power_pivot": {
        "tags": "Structures,Formations",
        "summary": "Powers a formation. 4 slots, so several cores can be placed for multiple effects.",
        "detail": """
Special crafting: unlocked near the restored Remains Altar, and every craft still needs you to be near it.

Can be destroyed with a hammer, returning every material; any core inside also drops on the ground.

Powers a formation — place a core in it to start the formation. 4 slots, so several cores can be placed for multiple effects.

Craftable in the <Ethereal Realm> and <Structures> tabs.
""",
    },
    "zhen_siji": {
        "tags": "Formations,Seasons,Farming",
        "summary": "Farm crops inside the area grow normally in all four seasons.",
        "detail": """
Area: at least 4 flags; the bounding rectangle may not exceed 12×12 turf.

Core: Seasons Nucleus ([images/inventoryimages1/deerclops_eyeball.png] Deerclops Eyeball 1, [images/inventoryimages3/thulecite.png] Thulecite 2, [images/inventoryimages2/greengem.png] Green Gem 1, [images/lingjie/icons/lj_magic_core.png] Magic Core 1).

Effect: season adaptation. Every farm crop inside the area grows normally in all four seasons; anything that is not a crop grows by the vanilla rules and is unaffected by the formation.
""",
    },
    "zhen_huichun": {
        "tags": "Formations,Farming,Light",
        "summary": "Lights the area so plants never wither and crops grow at night too.",
        "detail": """
Core: Plant Nucleus ([images/inventoryimages2/klaussackkey.png] Klaus Sack Key, [images/inventoryimages2/greengem.png] Green Gem 1, [images/inventoryimages2/nightmarefuel.png] Nightmare Fuel 5, [images/inventoryimages2/goldnugget.png] Gold Nugget 5, [images/lingjie/icons/lj_magic_core.png] Magic Core 1).

Effect: provides light inside the area; every plant and crop in the formation never withers, and withered ones come back to life; crops also grow normally at night.
""",
    },
    "zhen_quling": {
        "tags": "Formations,Defense",
        "summary": "Blocks creatures but not players: hostile creatures cannot get in, and ones inside cannot get out.",
        "detail": """
Core: Demon Subduing Nucleus ([images/inventoryimages3/shadowheart.png] Shadow Atrium 1, [images/inventoryimages3/thulecite.png] Thulecite 5, [images/inventoryimages2/nightmarefuel.png] Nightmare Fuel 10, [images/inventoryimages2/purplegem.png] Purple Gem 1, [images/inventoryimages2/livinglog.png] Living Log 2, [images/lingjie/icons/lj_magic_crystal.png] Magic Crystal 2).

Effect: blocks creatures but not players. No hostile creatures can spawn inside the area, or they are kept outside it; creatures already inside cannot leave.

Spawn eviction: a hostile creature that spawns inside the area is moved at once to the nearest valid spot outside it — land creatures only onto land, while aquatic and flying ones may land on the ocean, and never next to a cave entrance; it is then registered as a creature outside.
""",
    },
    "zhen_jiwen": {
        "tags": "Formations,Temperature,Sanity",
        "summary": "Fully neutralises extreme temperatures, cancels freeze and fire damage and slowly restores sanity.",
        "detail": """
Core: Constant Temperature Nucleus ([images/inventoryimages3/yellowstaff.png] Star Caller's Staff 1, [images/inventoryimages2/opalstaff.png] Moon Caller's Staff 1, [images/inventoryimages1/deerclops_eyeball.png] Deerclops Eyeball 1, [images/inventoryimages1/dragon_scales.png] Scales 1, [images/inventoryimages2/nightmarefuel.png] Nightmare Fuel 10, [images/lingjie/icons/lj_magic_crystal.png] Magic Crystal 2).

Effect: extreme temperatures are fully neutralised inside the area (no freezing or overheating); freeze and fire damage are cancelled, and nothing inside catches fire or freezes; the player's sanity slowly recovers, 30 sanity every 60 seconds.
""",
    },
    "lj_seasons_nucleus": {
        "tags": "Formations,Core,Magic",
        "summary": "The formation core of the Four Seasons Harmony Formation.",
        "detail": """
Formation core / pivot.

Used in the Four Seasons Harmony Formation: every farm crop inside the area grows normally in all four seasons.

Craftable in the <Ethereal Realm> and <Magic> tabs.
""",
    },
    "lj_plant_nucleus": {
        "tags": "Formations,Core,Magic",
        "summary": "The formation core of the Vitality Rejuvenation Formation.",
        "detail": """
Formation core / pivot.

Used in the Vitality Rejuvenation Formation: lights the area so plants never wither and crops grow at night too.

Craftable in the <Ethereal Realm> and <Magic> tabs.
""",
    },
    "lj_subdue_demons_nucleus": {
        "tags": "Formations,Core,Magic",
        "summary": "The formation core of the Spirit-Banishing Demon-Locking Formation.",
        "detail": """
Formation core / pivot.

Used in the Spirit-Banishing Demon-Locking Formation: blocks creatures but not players, locking hostile creatures both inside and outside the area.

Craftable in the <Ethereal Realm> and <Magic> tabs.
""",
    },
    "lj_constant_temperature_nucleus": {
        "tags": "Formations,Core,Magic",
        "summary": "The formation core of the Extreme Temperature Ward Formation.",
        "detail": """
Formation core / pivot.

Used in the Extreme Temperature Ward Formation: neutralises extreme temperatures, cancels freeze and fire damage and slowly restores sanity.

Craftable in the <Ethereal Realm> and <Magic> tabs.
""",
    },
    "lj_reiki_grass": {
        "tags": "Spirit Plants,Materials",
        "summary": "The basic herb of many pills. Grows on forest turf near spider nests, and on Butterfly Island beside Night Bat Nests.",
        "detail": """
Spawn (two sets, with different turf conditions)
　Mainland: grows on forest turf beside spider nests.
　Butterfly Island: grows on guano / cave turf beside Night Bat Nests, 1 to 3 per nest.

Harvesting: gives 1 [images/inventoryimages1/cutgrass.png] Cut Grass and 1 Spirit-Melting Grass, with a 5% chance of an extra Spirit-Melting Grass Root.

Its growth cycle matches vanilla saplings and it can be fertilised to speed it up.
⚠️ It does not grow in winter.

Can be burned and dug up; harvesting leaves the root behind, like vanilla grass.

Use: the basic herb of nearly every pill.
""",
    },
    "lj_red_magic_flower": {
        "tags": "Spirit Plants,Materials",
        "summary": "Grows beside predecessor skeletons; a skeleton left by a dead player also grows one after 1 day.",
        "detail": """
Spawn: beside predecessor skeletons, only 1 per skeleton. A skeleton left behind when a player dies grows a Dragon Claw Flower nearby after 1 day.

Harvesting: gives 1 [images/inventoryimages2/petals.png] Petals and 1 Dragon Claw Flower, with a 5% chance of an extra Dragon Claw Flower Root.

Its growth cycle matches vanilla saplings and it can be fertilised to speed it up.
⚠️ It does not grow in winter (same as Spirit-Melting Grass).

Can be burned and dug up; harvesting leaves the root behind, like vanilla grass.

Use: Invincible Pill, Nascent Union Pill.
""",
    },
    "yihuo_rules": {
        "tags": "Flames,Wasteland Flame,Mechanics",
        "summary": "A full flame can only be kept in the Spirit Void Gourd or the Void Ring; more than 10 seconds in a backpack burns items up.",
        "detail": """
Storage limits: a full Wasteland Flame / exotic flame can only be stored properly in the Spirit Void Gourd or the Void Ring. A split flame is a single-use item and cannot stack.

Burn risk: while a full flame sits in your inventory or a backpack it burns up 1 random burnable item every 10 seconds (world-unique items excepted, and other flames are never burned); if that item is a stack, only 1 is consumed. Several exotic flames in the same storage do NOT speed this up — the code rate-limits it to one burn per 10 seconds.

Light and fire-fighting: a full Wasteland Flame / exotic flame placed on the ground provides 20 range of light and puts out every ordinary fire nearby (exotic flames do not repel each other — two on the ground each give light and heat while still putting out other fires). A split flame placed on the ground simply disappears.

Splitting: an exotic flame absorbed by the Spirit Void Gourd can be split with a right-click, costing 10 Reiki. A split flame can go into a Reiki Table Lamp for light, adds 50% fuel, burns burnables and buildings, and can be put in the Alchemy Furnace to fuse.

Igniting with the Void Ring: with a full exotic flame inside, equipping the Void Ring and right-clicking a target ignites it at range (the same fireball as a Fire Staff, range 8 to 10), costing 10 Reiki; against burnable fuel devices it tops up fuel, and it deals no damage itself.

Flame ownership: a freshly dropped strong exotic flame (Frost Karma Flame, Dragon Flame Heartfire, Wildmane Flame, Spirit Dust Flame, Purple Scale Demon Flame) has no owner at all, so nobody can pick it up by hand — it can only be absorbed with a Spirit Void Gourd, and whoever's gourd absorbs it becomes its owner. From then on only the owner can pick it up by hand. A full day on the ground (8 minutes) turns it into "Lose Owner" again, after which any Spirit Void Gourd can absorb it. The Wasteland Flame is not a strong flame, so anyone can pick it up by hand.

Absorption cost: absorbing a flame with the Spirit Void Gourd sets you alight — it ignites you once, then costs 2 health per second for 60 seconds. It pauses while the gourd lies on the ground and resumes when picked back up (the remaining time is saved).

The remaining "Flame Backlash" time is shown on the HUD's negative effects panel, and only to whoever is holding the gourd; it pauses and disappears while the gourd lies on the ground.
""",
    },
    "lj_ordinary_flame": {
        "tags": "Wasteland Flame,Starting Gift,Flame",
        "summary": "The flame every character starts with, held inside the Void Ring.",
        "detail": """
Every character starts with it, held inside the Void Ring.

The Wasteland Flame is the starting flame; it can go into the furnace for alchemy, or be split to light a Reiki Table Lamp.

See "Flame Usage Rules" for the general storage, lighting and burn rules.
""",
    },
    "lj_ice_flame": {
        "tags": "Flames,Flame,Frost",
        "summary": "The exotic flame obtained by summoning Deerclops through the 'Frozen Log' clue; required to craft the Reiki Bow.",
        "detail": """
Exotic flame. Clue bosses roll their demonization level from the world day like anything else (see "Demonization Overview") and are not limited by season; clue items refresh every 20 days (each of the five keeps its own timer, see "Log").

Clue item: the "Frozen Log" (spawns at random in birch forests, unlocked by smashing it with a pickaxe).

How to get it: right-click the log to open it, and the note reads "a giant shadow under the moonlight; when it shatters the ice, a dancing light hides in the cold". A large suspicious mound then spawns somewhere on the ground; search every clue mound to spawn Deerclops. Killing it drops its normal loot plus the Frost Karma Flame.

Use: crafting the Reiki Bow needs a full Frost Karma Flame.
""",
    },
    "lj_dragon_flame": {
        "tags": "Flames,Flame,Fire",
        "summary": "The exotic flame obtained by summoning the Dragonfly through the 'Charred Scales' clue; required to craft Starfall.",
        "detail": """
Exotic flame.

Clue item: the "Charred Scales" (spawn near lava ponds, unlocked by dousing them with a watering can).

How to get it: right-click the log to open it, and the note reads "the rock nest stirs; a great beast guards its ground. Its rage burns the grass to ash; its shell hides a fire core that a sudden strike can crack". A Dragonfly spawns beside the pet nest; killing it drops its normal loot plus the Dragon Flame Heartfire.

Use: crafting Starfall needs a full Dragon Flame Heartfire.
""",
    },
    "lj_mighty_flame": {
        "tags": "Flames,Flame,Empower",
        "summary": "The exotic flame obtained by summoning the Bearger through the 'Rotten Backpack' clue; it empowers armour.",
        "detail": """
Exotic flame.

Clue item: the "Rotten Backpack" (spawns at random on forest terrain, unlocked by splitting it with an axe).

How to get it: right-click the log to open it, and the note reads "when it pushes over a pine, sparks rise from the roots; it fears water but loves honey". A Bee Queen hive is picked somewhere on the map and a bee box spawns near it, with the Bearger right beside the box; killing it drops its normal loot plus the Wildmane Flame.

Empower effects
Split Wildmane Flame: empowers any armour, doubling its durability.
Full Wildmane Flame: empowers any armour, granting 15 extra damage reduction and doubling its durability.

That extra 15 damage reduction applies after the armour's own defence.
For example: armour with 80 defence takes a 100 damage hit, so 20 damage gets through, minus 15 more, leaving 17 damage.
""",
    },
    "lj_dust_flame": {
        "tags": "Flames,Flame,Techniques",
        "summary": "The exotic flame obtained by summoning the Antlion through the 'Dried Camel Feathers' clue.",
        "detail": """
Exotic flame.

Clue item: the "Dried Camel Feathers" (picked up near the oasis).

How to get it: right-click the log to open it, and the note reads "there is a halo at the centre of the sandstorm — that is his breath". Going there shows the Antlion; killing it drops its normal loot plus the Spirit Dust Flame.

Use: put it in the Void Ring.
⚠️ Putting it in the Void Ring does not unlock anything yet (the technique gameplay is still in development — coming soon).
""",
    },
    "lj_purplemonster_flame": {
        "tags": "Flames,Flame,Soul Banner",
        "summary": "The exotic flame obtained by summoning the Soul-devouring Snake through the 'Swollen Scroll' clue; used to craft the Soul Banner.",
        "detail": """
Exotic flame.

Clue item: the "Swollen Scroll" (spawns at random beside swamp tentacles, unlocked by baking it with fire).

How to get it: right-click the log to open it, and the note reads "dusk is coming; purple firelight will be mirrored on the spirit vein's water". After reading the log the boss appears at dusk beside a pond on Butterfly Island. Going there shows the Soul-devouring Snake; killing it drops its normal loot plus the Purple Scale Demon Flame.

Use: it crafts the Soul Banner, and giving it to the banner unlocks the "Soul Refining" skill.
""",
    },
    "lj_log": {
        "tags": "Flames,Clues",
        "summary": "The journal used for exotic flame clues. Each of the five clues keeps its own timer and refreshes 20 game days after you take it.",
        "detail": """
The collective name for exotic flame clue items.

Clue bosses roll their demonization level from the world day like anything else (see "Demonization Overview") and are not limited by season.

Refresh rules
　The five clues each keep their own independent timer and never block one another.
　The timer starts the moment you take one: smashing, splitting, dousing, picking up and destroying all count.
　The next clue appears after a full 20 game days (the count includes the current day's progress).
　Only one clue of each kind exists in the world at a time; once you have taken it, even sitting in your backpack, it no longer affects the refresh timer.
　All five are placed when the world starts; your realm only gates reading them (Subtle), not their placement.

The clue item for each exotic flame: Frozen Log, Charred Scales, Rotten Backpack, Dried Camel Feathers and Swollen Scroll.
""",
    },
    "lj_frozen_log": {
        "tags": "Clue,Flames,Frost Karma Flame",
        "summary": "Spawns at random in birch forests and is unlocked by smashing it with a pickaxe. Points to the Frost Karma Flame.",
        "detail": """
Clue item pointing to the Frost Karma Flame.

Location: spawns at random in birch forests.
How to unlock: smash it with a pickaxe.

Breaking it open turns it into the 'Frost Log' — the note and everything that follows are written on the log's own entry (see "Frost Log").
""",
    },
    "lj_charred_scales": {
        "tags": "Clue,Flames,Dragon Flame Heartfire",
        "summary": "Spawns beside lava ponds and is unlocked by dousing it with a watering can. Points to the Dragon Flame Heartfire.",
        "detail": """
Clue item pointing to the Dragon Flame Heartfire.

Location: spawns beside lava ponds.
How to unlock: douse it with a watering can.

Dousing it turns it into the 'Dragonflame Log' — the note and everything that follows are written on the log's own entry (see "Dragonflame Log").
""",
    },
    "lj_rotten_backpack": {
        "tags": "Clue,Flames,Wildmane Flame",
        "summary": "Spawns at random on forest terrain and is unlocked by splitting it with an axe. Points to the Wildmane Flame.",
        "detail": """
Clue item pointing to the Wildmane Flame.

Location: spawns at random on forest terrain.
How to unlock: split it with an axe.

Splitting it open turns it into the 'Mighty Flame Log' — the note and everything that follows are written on the log's own entry (see "Mighty Flame Log").
""",
    },
    "lj_dried_camel_feathers": {
        "tags": "Clue,Flames,Spirit Dust Flame",
        "summary": "Picked up near the oasis. Points to the Spirit Dust Flame.",
        "detail": """
Clue item pointing to the Spirit Dust Flame.

Location: picked up near the oasis.

Use: an Alchemy Furnace material for refining the 'Dustflame Log' (high tier, 2 minutes — see that entry). The note's clue is read from the Dustflame Log itself.
""",
    },
    "lj_swollen_scroll": {
        "tags": "Clue,Flames,Purple Scale Demon Flame",
        "summary": "Spawns at random beside swamp tentacles and is unlocked by baking it with fire. Points to the Purple Scale Demon Flame.",
        "detail": """
Clue item pointing to the Purple Scale Demon Flame.

Location: spawns at random beside swamp tentacles.
How to unlock: bake it with fire.

Baking it turns it into the 'Purple Scale Log' — the note and everything that follows are written on the log's own entry (see "Purple Scale Log").
""",
    },
    "lj_ice_log": {
        "tags": "Logs,Flame Clues",
        "summary": "The clue obtained from the 'Frozen Log', pointing to Deerclops.",
        "detail": """
Matching exotic flame: Frost Karma Flame.
Clue item: Frozen Log.
Follow-up boss: Deerclops.

The note reads 'a giant shadow under the moonlight; when it shatters the ice, a dancing light hides in the cold'. A large suspicious mound then spawns at random on the ground, and searching every clue mound spawns Deerclops.

Reading it requires the Subtle realm.
""",
    },
    "lj_dragon_log": {
        "tags": "Logs,Flame Clues",
        "summary": "The clue obtained from the 'Charred Scales', pointing to the Dragonfly.",
        "detail": """
Matching exotic flame: Dragon Flame Heartfire.
Clue item: Charred Scales.
Follow-up boss: Dragonfly.

The note reads 'the rock nest stirs; a great beast guards its ground. Its rage burns the grass to ash; its shell hides a fire core that a sudden strike can crack'. A Dragonfly spawns beside the pet nest.

Reading it requires the Subtle realm.
""",
    },
    "lj_mighty_log": {
        "tags": "Logs,Flame Clues",
        "summary": "The clue obtained from the 'Rotten Backpack', pointing to the Bearger.",
        "detail": """
Matching exotic flame: Wildmane Flame.
Clue item: Rotten Backpack.
Follow-up boss: Bearger.

The note reads 'when it pushes over a pine, sparks rise from the roots; it fears water but loves honey'. A Bee Queen hive is picked somewhere on the map and a bee box spawns near it, with the Bearger right beside the box.

Reading it requires the Subtle realm.
""",
    },
    "lj_dust_log": {
        "tags": "Logs,Flame Clues",
        "summary": "The log that points to the Antlion; it can also be refined directly in the Alchemy Furnace.",
        "detail": """
Matching exotic flame: Spirit Dust Flame.
Clue item: Dried Camel Feathers.
Follow-up boss: Antlion.

The note reads 'there is a halo at the centre of the sandstorm — that is his breath'. Going there shows the Antlion.

Refining (high tier, refining time 2 minutes)

Reading it requires the Subtle realm.
""",
    },
    "lj_purplemonster_log": {
        "tags": "Logs,Flame Clues",
        "summary": "The clue obtained from the 'Swollen Scroll', pointing to the Soul-devouring Snake.",
        "detail": """
Matching exotic flame: Purple Scale Demon Flame.
Clue item: Swollen Scroll.
Follow-up boss: Soul-devouring Snake.

The note reads 'dusk is coming; purple firelight will be mirrored on the spirit vein's water'. After reading the log the boss appears at dusk beside a pond on Butterfly Island, and going there shows the Soul-devouring Snake.

Reading it requires the Subtle realm.
""",
    },
    "lj_butterfly_island": {
        "tags": "Terrain,Seasons,Demon Beasts,Demon Beast Forest",
        "summary": "A region split into four seasonal blocks, with the winter block open in the first release; a gathering place for the exotic flame clue bosses and demonic beasts.",
        "detail": """
You can also search for this place as "Demon Beast Forest" — the tag carries that alias, so either name finds it.

Inside it is split into four blocks matching the four seasons. In this first release the winter block is winter all year round; the other three blocks will have seasonal effects too, with content coming later. (Region barrier: you only feel the regional season once you are on the island.)

Winter region block
Core area (swamp turf): a frozen swamp pond (where the clue boss spawns); one perfectly ordinary tree surrounded by evil flowers; several gloomy thistles; several spiky trees and spiky bushes.
Satellite area (guano turf): in the corners of the region, 3 Night Bat Nests, each with 1 to 3 Spirit-Melting Grass spawning beside it.
Vanilla winter content: a few ice patches spawn at random (breaking some leaves a puddle of water behind), plus one penguin colony.

Easter egg
Each block spawns a predecessor skeleton at random, with items left over from the fall beside it.
　1. 1 to 5 Magic Cores (70% chance)
　2. 1 to 2 Magic Crystals (30% chance)

Several Night Bat Nests.

How Butterfly Island generates can be set in the mod settings: new and existing worlds / new worlds only / off.

Console command: c_ljhd() — if the map did not generate Butterfly Island, this command spawns it under your feet. Pick a reasonably open stretch of ocean, because it will displace the terrain there.
""",
    },
    "lj_remains_island": {
        "tags": "Terrain,Shallow Sea,Remains,Boss",
        "summary": "A small landform in the shallow sea; ancient remains, the Blazing Rock Scorpion Dragon and some ore spawn on it.",
        "detail": """
A small landform that generates in the shallow sea.

The island spawns:
　Ancient remains (which repair into the Remains Altar — see "Remains Altar").
　The Blazing Rock Scorpion Dragon (see "Blazing Rock Scorpion Dragon").
　Some ore.
""",
    },
    "lj_remains_altar": {
        "tags": "Structures,Special Crafting,Science Station",
        "summary": "The Ethereal Realm's own science station. Repairing it unlocks high-tier crafting, and every craft must be made beside it.",
        "detail": """
You need at least the Fasting realm to repair it, and finishing the repair costs one whole realm (nine stages) — that is the price of the repair, not a reward. Your realm keeps whatever death lock it already had.

Crafting unlocks nearby: every craft still needs you to be near the Remains Altar, so a recipe is never permanently unlocked just because you made it once.
Reiki Bow, Starfall, Soul Banner, Keel Armour, Crystal Crown, Seasons Nucleus, Plant Nucleus, Demon Subduing Nucleus, Constant Temperature Nucleus, Spirit Formation Pivot, Void Ring.

Science station: the Remains Altar is the Ethereal Realm's own science station. Basic cultivation facilities use tier-2 science (the Alchemy Engine) and unlock permanently; the high-tier recipes above must be crafted beside the Remains Altar.

The restored altar

[[图片:images/lingjie/showcase/lj_remains_altar_complete.png|Once repaired it turns from broken remains into a complete altar, and the high-tier constructs are all finished here]]
""",
    },
    "lj_chiyan_scorpion_dragon": {
        "tags": "Boss,Epic,Remains Altar",
        "summary": "The epic boss of the Remains Altar. 30000 health, 30 armour; immune to freeze, stagger and knockback, and it summons Venomous Scorpion Larvae after half health.",
        "detail": """
Spawns at the Remains Altar (an ancient ruins islet). Epic boss.

Base stats
30000 health, 15 armour, medium movement speed.

Core mechanics
Immune to freeze, stagger and knockback; when put to sleep it stays down for 8 seconds.
Every 5000 health lost summons 4 Venomous Scorpion Larvae (250 health, 40 attack, 3 poison damage per second for 8 seconds), with a 30-second cooldown; healing back up never re-triggers a stage that has already been recorded. The larvae stay around forever, and whether they die does not affect the next summon of 4.

Skills
Sweep (basic attack): a pincer swipe, 60 damage per pincer, 8-second cooldown. Attack range about 1 turf (4 units; 1 turf = 4 units). After 4 attacks the tail sweeps for 90 AOE damage and knocks players back 2 turf.

Meteor Crash: calls down a meteor that hurtles at the player, much like the rocks falling in a meteor field (destroying buildings and trees, same as a vanilla meteor field). 18-second cooldown. Deals 120 damage and knocks the player down (sending them flying and sprawling).

Grit Eruption: a 5-turf cone of sand in front of it, lasting 1.2 seconds, 20-second cooldown.
　The eruption lasts 1.2 seconds, covering a 5-turf cone 3 turf wide in front of it, continuously spawning grit that corrodes the terrain; the terrain lingers for 2 seconds after the eruption ends.
　⚠️ The grit's slow and damage come from the vanilla sand spikes themselves.

Scorpion Dragon Charge: charges up for 1 second, then charges in a straight line for 8 turf, dealing 100 damage and destroying buildings along the way, ending with a 2-second stagger; 30-second cooldown. Maximum straight-line distance is 8 turf.
　Building destruction: every wooden or stone wall, harvestable and small structure in the path is destroyed outright.

Drops on kill
Scorpion Dragon Bone 1, [images/inventoryimages2/monstermeat.png] Monster Meat 4, Magic Crystal 2, Magic Core 6, Magic Core Shard 10, [images/inventoryimages2/orangegem.png] Orange Gem 2, [images/inventoryimages2/greengem.png] Green Gem 2, [images/inventoryimages3/yellowgem.png] Yellow Gem 2.
""",
    },
    "lj_little_scorpion": {
        "tags": "Boss,Summon,Remains Altar",
        "summary": "Summoned 4 at a time whenever the Blazing Rock Scorpion Dragon loses 10000 health. 250 health, 40 attack, with poison damage.",
        "detail": """
Summoned 4 at a time by the Blazing Rock Scorpion Dragon every 10000 health it loses.

250 health, 40 attack, 3 poison damage per second for 8 seconds.

The larvae stay around forever, and whether they die does not affect the next summon of 4.
""",
    },
    "lj_bat_nest": {
        "tags": "Terrain,Butterfly Island,Spawns",
        "summary": "Each nest spawns 6 Demon Bats and 1 Shadow Blood Bat, active at dusk and at night.",
        "detail": """
Several spawn on Butterfly Island. Each nest spawns 6 Demon Bats (1 respawns every 5 minutes, up to 6) and 1 Shadow Blood Bat (1 respawns every 45 minutes, up to 1).

Active at dusk and at night (behaving much like vanilla bats).

1 to 3 Spirit-Melting Grass spawns at random beside each nest.
""",
    },
    "lj_blood_bat": {
        "tags": "Demon Beast,Butterfly Island,Bat",
        "summary": "A lesser demonic beast. 300 health and 25 damage, and it always drops Monster Meat.",
        "detail": """
300 health, 25 attack damage, 1-second attack period.

Attacks: it bites within 1 turf, and charges when you are further away. A charge hit staggers you briefly, which you can dodge by moving up or down early.

On death it always drops [images/inventoryimages2/monstermeat.png] Monster Meat 1 (Magic Core Shards, Magic Cores and Magic Crystals drop according to its current demonization tier). It is not a large demonic beast.

Spawned by Night Bat Nests, 6 per nest, 1 respawning every 5 minutes, up to 6.
""",
    },
    "lj_demon_bat": {
        "tags": "Demon Beast,Butterfly Island,Bat,Elite",
        "summary": "An elite demonic beast with 2000 health. Its sound wave staggers in an area, and below half health it keeps summoning Demon Bats.",
        "detail": """
2000 health, medium movement speed.

Attacks: bite and sound wave.
55 attack damage; it bites within 1 turf and uses the sound wave at longer range.

Sound wave: releases a dark red wave, an area attack centred on itself with radius 8, pulsing every 0.5 seconds, staggering anyone inside continuously for 9 seconds. Step out of the area to end it. 30-second cooldown.

Summoning: below 50% health it starts summoning 1 Demon Bat every 15 seconds with no limit. Out of combat they all return to the nest; the cap is 6, and any extra ones that enter the nest count as dead.

On death it always drops Blood Bat Essence 1 and [images/inventoryimages2/monstermeat.png] Monster Meat 2 (Magic Core Shards, Magic Cores and Magic Crystals drop according to its current demonization tier).

Spawned by Night Bat Nests, 1 per nest, 1 respawning every 45 minutes, up to 1.
""",
    },
    "lj_soul_devouring_snake": {
        "tags": "Boss,Epic,Hidden,Butterfly Island",
        "summary": "A hidden boss with 12000 health. It drops scales every 2000 damage taken, and below half health it eats them to heal 1000.",
        "detail": """
Hidden boss, epic tier.

Base stats
12000 health, a 50 damage bite as its basic attack with a poison effect, 15% armour, medium movement speed.

Core mechanics
Venom immunity: the Soul-devouring Snake's own kind is unaffected by its venom and bog, so several bosses on the field will not poison or slow each other.
Every 2000 health of damage taken it drops Soul Snake Scales, which players cannot pick up but can burn with an exotic flame.
Once the Soul-devouring Snake first falls to 50% health it actively seeks out and eats the scales to heal itself, 1000 health each.

Skills
Bite: a snake head bite for 50 damage, non-stacking, and it can refresh the poison timer.
Venom Bog: spits venom at the target to create a poison bog that lasts 4 minutes, slowing anyone inside by 60% and poisoning them on contact; 15-second cooldown.
Petrifying Bind: within a circle of radius 16 centred on itself, binds the target in place for 3 seconds; 30-second cooldown. (Circular area, players only.)
Venom Lock: slams its tail into the ground and spawns a snake body like a shadow creature that coils around the target for 5 seconds, during which the boss closes in and basic-attacks the bound target. (Players only.)

Drops on kill
Soul Snake Skin 3, [images/inventoryimages2/monstermeat.png] Monster Meat 5, Magic Crystal 2, Magic Core 6, Magic Core Shard 10, [images/inventoryimages3/redgem.png] Red Gem 2, Purple Scale Demon Flame 1.
""",
    },
    "lj_moon_lion": {
        "tags": "Boss,Epic,Amethyst Form Flower",
        "summary": "An epic boss with 24000 health. It heals from nearby flowers, and standing near a Mandrake puts it to sleep.",
        "detail": """
Spawns beside an Amethyst Form Flower. Epic boss.

Base stats
24000 health, 15% armour, medium movement speed.

Core mechanics
Disengage and return: once it leaves the area around its flower it stops chasing and goes home, using one roar as the transition; it gives up entirely past 40 distance.
With flowers within 5 turf it heals 60 health per flower every 10 seconds (an Amethyst Form Flower counts as one flower unit and spawns butterflies like petals do).
Destroying or harvesting nearby flowers interrupts the healing and forces a Lion's Roar within 10 seconds (harvesting petals within those 10 seconds still triggers it only once).
Standing near a Mandrake — planted ones included — puts it to sleep for 8 seconds, and that sleep can only trigger once per minute.

Skills (used in rotation: claw → scale powder missiles → roar → earth-rending step; anything unavailable or still cooling down is skipped)
Crystal Claw Smash: a single-target melee heavy blow. 70 damage, 5-second cooldown, range about 1 turf (3 units), knocks small creatures down, and staggers a hit player for 0.6 seconds. If the player is closer than 1 turf, there is a 60% chance of one swing with each claw for 70 damage each (140 total), and a 40% chance of a single swing.
Scale Powder Missiles (ranged): fans one wing to fire 3 scale powder orbs in a triangular spread. 40 damage each, 120 for all three. Blast radius about 0.4 turf (1.5 units), and each blast leaves a petal at the impact point. 18-second cooldown, up to 10 turf flight distance, exploding on contact with an obstacle.
Lion's Roar (control): a screen-wide sound wave with 6 turf of range. No damage, but it staggers the player for 1.2 seconds and forces their weapon to drop.
Earth-Rending Step: the lion raises one front paw, sinks its body to gather power, the ground trembles faintly and dust kicks up at its feet, with a small screen shake warning players to move.
　Spawn area: centred on itself with 8 turf (32 units) of radius, it spawns one temporary pit under every player in range; pits never overlap, and no pit spawns where the ground is impassable.
　The pit does not destroy buildings, turf, walls or crops, and when it first appears only cracks show as a warning for 1 second.
　It then advances one collapse stage per second, 3 stages in all: stages 1 and 3 each deal 60 area damage, and stage 2 is effects only.
　From the second second on it deals an extra 1 area damage per second; the collapse and damage radius are both 2.5 units (about 0.6 turf).
　When stage 3 ends the pit is removed immediately, so it exists for about 3 seconds in total (unlike the Antlion's permanent sinkholes).
　⚠️ The pit only deals damage and does not slow you.
　18-second cooldown.

Drops on kill
Amethyst Shell 1, Lion Bone 1, [images/inventoryimages2/monstermeat.png] Monster Meat 4, Magic Crystal 2, Magic Core 6, Magic Core Shard 10, [images/inventoryimages3/redgem.png] Red Gem 2, [images/inventoryimages1/bluegem.png] Blue Gem 2, [images/inventoryimages2/purplegem.png] Purple Gem 2.
""",
    },
}

SITE = [
    # modinfo.lua 里是 name = "灵界"，author = "犹如黑夜星光、喵大仙BigXian"。
    # 顶栏作者名按作者要求单独写（跟 modinfo 不必一致）。
    {"网站标题": "灵界", "网站英文名": "Spirit Realm", "网站版本": "v0.6", "作者": "犹如黑夜星光JinYan、喵大仙BigXian"},
]

SECTIONS = [
    # 「短名」用于窄屏菜单：整排卷目按钮放不下时改用短名，省一半宽度。
    # 「英文名 / 英文短名」用于站点中英切换（英文短名同样是给窄屏菜单用的）。
    {"分类id": "jingjie", "分类名": "境界", "短名": "境界", "英文名": "Realms", "英文短名": "Realms", "排序值": "1", "是否展示": "true"},
    {"分类id": "rumo", "分类名": "生物入魔", "短名": "入魔", "英文名": "Demonization", "英文短名": "Demons", "排序值": "2", "是否展示": "true"},
    {"分类id": "danyao", "分类名": "丹药与炼制", "短名": "丹药", "英文名": "Pills & Alchemy", "英文短名": "Pills", "排序值": "3", "是否展示": "true"},
    {"分类id": "cailiao", "分类名": "精炼材料", "短名": "材料", "英文名": "Refined Materials", "英文短名": "Materials", "排序值": "4", "是否展示": "true"},
    {"分类id": "jianzhu", "分类名": "建筑", "短名": "建筑", "英文名": "Structures", "英文短名": "Buildings", "排序值": "5", "是否展示": "true"},
    {"分类id": "wuqi", "分类名": "武器与盔甲", "短名": "武器", "英文名": "Weapons & Armour", "英文短名": "Gear", "排序值": "6", "是否展示": "true"},
    {"分类id": "fabao", "分类名": "法宝与工具", "短名": "法宝", "英文名": "Artifacts & Tools", "英文短名": "Tools", "排序值": "7", "是否展示": "true"},
    {"分类id": "zhenfa", "分类名": "阵法灵技", "短名": "阵法", "英文名": "Formations", "英文短名": "Forms", "排序值": "8", "是否展示": "true"},
    {"分类id": "lingzhi", "分类名": "灵植", "短名": "灵植", "英文名": "Spirit Plants", "英文短名": "Plants", "排序值": "9", "是否展示": "true"},
    {"分类id": "yihuo", "分类名": "墟火与异火", "短名": "墟火", "英文名": "Flames", "英文短名": "Flames", "排序值": "10", "是否展示": "true"},
    {"分类id": "ditu", "分类名": "地形与Boss", "短名": "地形", "英文名": "Terrain & Bosses", "英文短名": "Terrain", "排序值": "11", "是否展示": "true"},
    # 「人物」是占位卷目：人物还没设计完，排在最后（更新日志之前），暂无条目。
    {"分类id": "renwu", "分类名": "人物", "短名": "人物", "英文名": "Characters", "英文短名": "People", "排序值": "12", "是否展示": "true"},
    {"分类id": "log", "分类名": "更新日志", "短名": "日志", "英文名": "Changelog", "英文短名": "Log", "排序值": "99", "是否展示": "true"},
]

TELE = [
    ("lj_magic_debris", "魔核碎片"),
    ("lj_magic_core", "魔核"),
    ("lj_magic_crystal", "魔晶"),
    ("realm_system", "境界体系,经验值表,属性提升,升阶经验"),
    ("reiki_value", "灵力值"),
    ("corruption_overview", "入魔"),
    ("corruption_light", "轻度入魔"),
    ("corruption_medium", "中度入魔"),
    ("corruption_deep", "深度入魔"),
    ("alchemy_rules", "炼丹"),
    ("pill_tiers", "丹劫"),
    ("lj_ordinary_flame", "墟火"),
    ("yihuo_rules", "异火"),
    ("lj_ice_flame", "冰霜业火"),
    ("lj_dragon_flame", "龙炎心火"),
    ("lj_mighty_flame", "狂鬃焰"),
    ("lj_dust_flame", "灵煊尘火"),
    ("lj_purplemonster_flame", "紫鳞妖焰"),
    ("lj_reiki_grass", "融灵草"),
    ("lj_red_magic_flower", "龙爪花"),
    ("lj_purple_magic_flower", "紫晶塑体花"),
    ("lj_wudao_chair", "悟道淬体台,淬体台"),
    ("lj_alchemy_furnace", "炼丹炉,丹炉"),
    ("lj_reiki_gourd", "灵虚葫"),
    ("lj_soul_banner", "魂幡"),
    ("lj_void_ring", "虚空戒"),
    ("zhenfa_overview", "阵法"),
    ("lj_butterfly_island", "蝴蝶岛,魔兽森林"),
    ("lj_soul_devouring_snake", "噬魂蛇"),
    ("lj_moon_lion", "月蚀晶翼狮,月狮,翼狮"),
    ("lj_chiyan_scorpion_dragon", "炽岩蝎龙,蝎龙"),
    ("lj_stillness_pill", "清心丸"),
    ("lj_disaster_pill", "破劫丹"),
    ("lj_bat_blood", "血蝠精血"),
    ("lj_scorpion_dragon_bone", "蝎龙骨"),
    ("lj_amethyst_shell", "紫晶壳"),
    ("lj_soul_snake_skin", "噬魂蛇皮"),
    ("lj_remains_altar", "残骸祭坛,祭坛"),
]

ITEMS = []
_ORDER = {}


def item(sec, iid, name, tags, summary, detail, recipe="", image="", visible=True):
    """visible=False 的条目仍保留在 data.json 里供维护者查阅，但前台不显示。

    用于「文档写了、mod 里没实装」的内容，避免玩家查到用不了的东西。

    英文版内容（标签 / 简介 / 详情）统一写在文件开头的 EN_CONTENT 里，
    按条目 id 归档；哪一段没翻就留空，英文模式下自动退回中文。
    """
    if iid in _ORDER:
        raise SystemExit("重复 id: %s" % iid)
    _ORDER[iid] = True
    if not image:
        # 卡片图优先用「展示图」（idle 动画第一帧），没有才退回物品图标。
        image = SHOWCASE_INDEX.get(iid) or icon_path(iid) or ""
    en = EN_CONTENT.get(iid, {})
    ITEMS.append({
        "id": iid,
        "分类id": sec,
        "名称": name,
        "英文名": NAME_EN.get(iid, ""),
        "标签": tags,
        "英文标签": en.get("tags", ""),
        "图片": image,
        "制作配方": recipe,
        "英文配方": recipe_en(recipe),
        "需祭坛": "true" if iid in ALTAR_RECIPES else "",
        "简介": summary,
        "英文简介": en.get("summary", ""),
        "详情": detail.strip(),
        "英文详情": en.get("detail", "").strip(),
        "排序值": str(len(_ORDER)),
        "是否展示": "true" if visible else "false",
    })


# ===========================================================================
# 卷目 1：境界
# ===========================================================================
item(
    "jingjie", "realm_system", "境界体系", "境界,修炼,升阶,经验,属性",
    "九大境界，每境九阶。靠击杀生物积累经验升阶，死亡会掉一阶。含每阶经验门槛与每境属性加成。",
    """
新增境界值与灵力值，类似三维显示。

[[图片:images/lingjie/anim/realm_badge.png|游戏内的境界徽章（境界越高，中间的图标会换成对应数字）]]

境界共 9 个：凡境、淬体、炼筋、辟谷、引气、入微、超凡、合婴、具灵。每个境界分 9 阶，如淬体一阶、二阶……九阶。

升阶方式
　击杀生物获得经验；在 15 个地皮范围内、30 秒内参与过攻击就算参与。阿比盖尔的攻击，以及薇洛技能火焰造成的击杀，都算它们主人的参战（其他随从不算）。
　经验获取量 = 目标的最大生命 × 5%（mod 设置里可选 5% / 8% / 12%）；按代码取的是当前最大生命，被入魔抬高的那部分也算在内。

瓶颈与打坐
　第 1 到 3 阶无瓶颈；第 3 阶升第 4 阶、第 6 阶升第 7 阶、第 9 阶升入下一个境界，都需要打坐。
　瓶颈会把经验卡在门槛前一点：例如引气三阶、经验 8000 时，哪怕击杀能拿 4000 经验的 Boss，也只能升到 8499，差的那 1 点必须靠打坐补上。

突破
　从炼筋升辟谷开始，之后每一次跨大境界（辟谷、引气、入微、超凡、合婴、具灵）都要服用对应丹药并打坐 10 秒。共 6 种突破丹药。

死亡惩罚
　死亡一次掉一阶。掉阶后必须服用清心丸才能继续修炼，否则会止步不前。

每阶经验门槛（按一阶 → 九阶顺序，数字是该阶的累计经验门槛）
凡境　50 · 100 · 150 · 200 · 250 · 300 · 350 · 450 · 500
淬体　500 · 600 · 700 · 800 · 900 · 1000 · 1100 · 1200 · 1300
炼筋　1300 · 1500 · 1700 · 1900 · 2100 · 2300 · 2500 · 2700 · 2900
辟谷　2900 · 3300 · 3700 · 4100 · 4500 · 4900 · 5300 · 5700 · 6100
引气　6100 · 6900 · 7700 · 8500 · 9300 · 10100 · 10900 · 11700 · 12500
入微　12500 · 14000 · 15500 · 17000 · 18500 · 20000 · 21500 · 23000 · 24500
超凡　24500 · 27000 · 29500 · 32000 · 34500 · 37000 · 39500 · 42000 · 44500
合婴　44500 · 48500 · 52500 · 56500 · 60500 · 64500 · 68500 · 72500 · 76500
具灵　76500 · 82500 · 88500 · 94500 · 100500 · 106500 · 112500 · 118500 · 124500
　凡境前七阶每阶 +50，第 8、9 阶是 450 和 500；其余境界每境内部的每阶增幅固定：淬体 +100、炼筋 +200、辟谷 +400、引气 +800、入微 +1500、超凡 +2500、合婴 +4000、具灵 +6000。

每境属性加成（达到该境界后生效）
凡境　生命 +0，移速 ×1.00，灵力 +0，攻击 ×1.00
淬体　生命 +10，移速 ×1.05，灵力 +5，攻击 ×1.25
炼筋　生命 +15，移速 ×1.10，灵力 +10，攻击 ×1.50
辟谷　生命 +25，移速 ×1.15，灵力 +15，攻击 ×1.75
引气　生命 +40，移速 ×1.20，灵力 +20，攻击 ×2.00
入微　生命 +55，移速 ×1.25，灵力 +30，攻击 ×2.25
超凡　生命 +70，移速 ×1.30，灵力 +40，攻击 ×2.50
合婴　生命 +80，移速 ×1.35，灵力 +50，攻击 ×2.75
具灵　生命 +100，移速 ×1.40，灵力 +70，攻击 ×3.00
　加成不会累加，提升境界时直接换成新境界的数值；生命与灵力是加在上限上的固定值，移速与攻击是倍率（攻击 ×1.25 即伤害 +25%）。
""",
    image="images/lingjie/anim/realm_badge.png",
)

item(
    "jingjie", "reiki_value", "灵力值", "境界,灵力,数值",
    "初始 50、上限 120；每分钟回复 3.3；低于 5 会衰弱 10 秒。",
    """
[[图片:images/lingjie/anim/spirit_badge.png|游戏内的灵力徽章（火焰图标 + 液面就是当前灵力）]]

灵力值初始为 50，通过提升境界增加，上限 120。

每分钟回复 3.3 点灵力值。

灵力枯竭时（低于 5）会进入 10 秒的虚弱状态：按原版规则叠加睡意与昏沉，甚至直接昏睡；虚弱解除后恢复 10 点灵力。

灵力值会被多种灵技与法宝消耗，例如灵韵的玄冰灌注消耗 20 点、星陨的陨火刺消耗 10 点。
""",
    image="images/lingjie/anim/spirit_badge.png",
)

item(
    "jingjie", "timed_effects", "限时状态", "界面,状态,增益,负面",
    "HUD 上的限时状态面板：增益与负面分开显示，可按住右键拖动并保存位置，跟随 HUD 缩放。",
    """
两个独立面板，互不影响，也不会跟着状态栏一起移动或缩放：

　负面状态：默认在左上角。
　增益状态：默认在右下角。

拖动与保存：按住右键拖动面板，松开即保存位置；位置跟原版 HUD 坐标记录一起存档。

缩放：跟随原版 HUD 缩放设置。

可见范围：只显示自己的状态，别的玩家看不到你的限时状态。

负面状态（9 种）：星火灼烧、冰蚀、蝎毒、蛇毒、石化、束缚、异火焚身、丹劫、祭天雷劫。
增益状态（6 种）：赤焰丹、冷焰丹、防潮丹、爆裂丸、不灭丹、复灵丹。

另外：玩家头像弹窗里新增了「灵界介绍页」入口。
""",
)

item(
    "jingjie", "tribulation_rules", "雷劫", "境界,雷劫,丹劫,祭天",
    "深度入魔死亡时的「祭天雷劫」与炼丹时的「丹劫」的完整规则。",
    """
游戏里一共有两种雷劫：深度入魔生物被玩家杀死时降下的「祭天雷劫」，以及炼丹时的「丹劫」。

一、祭天雷劫（深度入魔生物死亡）

触发：被玩家杀死的深度入魔生物，死亡时召唤天劫（随从、虚空戒等造成的击杀同样算玩家的）。
时长：持续 60 秒，每 6 秒落雷一次；第一轮的落点标识立即出现，不必再等 6 秒。
目标：以尸体为中心约 25 格范围内随机落点，先出标识，再降落天雷，劈中任意玩家都会造成伤害。
伤害：普通深度入魔生物扣 10% 最大生命；史诗 Boss 则是必杀（100% 最大生命），无视无敌与伤害吸收。
预警：标识出现 1.5 秒后落地；25 范围内的玩家会收到台词「天道有感，雷劫将至！」，并在 HUD 上看到「祭天雷劫」倒计时，走出范围自动消失。

二、丹劫（炼丹雷劫）

触发：只有中阶与高阶丹药会触发丹劫，触发概率 50%（另外 50% 不触发，那一次必然失败，只得废丹）。
节奏：中阶每 10 秒落雷一轮，第一轮的落点标识在第 9 秒出现；高阶每 8 秒一轮，第一轮标识在第 7 秒。
落点：先出现落点标识，1 秒后落雷，判定半径 1.75。
持续：整场丹劫 120 秒，期间必须一直待在炉子旁边躲避，躲完才能收丹。
落雷伤害：直接清空当前生命（必杀）。
被劈中：炼丹炉当场炸毁，只留下 5 个木炭和 1 颗废丹，材料不返还。
免劫：服用破劫丹后免疫丹劫，没有时间限制，但死亡后失效；只带在背包里不生效。
提示：炼丹期间，负面状态面板上会显示「丹劫」倒计时；被丹劫劈死的死亡原因记为「丹劫天雷」。
不触发丹劫的炼制：使用异火炼丹仍然要应劫；但「特殊炼制」（魂幡、月魄凝液瓶、尘火日志等）必成，且完全不触发丹劫。
""",
)

# ===========================================================================
# 卷目 2：生物入魔
# ===========================================================================
item(
    "rumo", "corruption_overview", "入魔总览", "入魔,机制,开局",
    "开局的生物会随机入魔，入魔天数可调；到达设定天数后，史诗 Boss 必定深度入魔。",
    """
生物生成时随机抽入魔等级。游玩天数可调节为 30 / 60 / 90 天，默认为 60 天。

抽取概率
　未到设定天数：轻度 47.5%、中度 47.5%、深度 5%。
　已到设定天数：史诗 Boss 必定深度入魔；其他生物 轻度 50%、中度 25%、深度 25%。

所有入魔生物均为敌对目标（切斯特这类中立生物除外；玩家的特定属性关系也除外，比如蜘蛛不会攻击蜘蛛人）。

入魔分三档，游戏内显示为「入魔程度：轻度 / 中度 / 深度」：
轻度入魔、中度入魔、深度入魔。

不会被入魔的：影怪系（爬行梦魇、恐怖喙、梦魇、废墟梦魇、影骑士、影主教、影车、海上的影怪等）、被动小动物、玩家、同伴、墙体、装备展示模型。被玩家雇佣的生物会立即清除全部入魔效果。
""",
)

item(
    "rumo", "corruption_light", "轻度入魔", "入魔,轻度",
    "入魔血量按 1.60 倍打折计算（血量越高越接近满倍率）；会给玩家挂上魔气环绕、饥饿诅咒、暗影迟缓。",
    """
游戏内显示为「轻度」。

核心强化 —— 生命值
　　最大生命 = 未入魔时的最大生命 × (1.60 − 65 ÷ (未入魔时的最大生命 + 110))

实际结果：

　　基础 100 → 129.05（×1.290）
　　基础 500 → 746.72（×1.493）
　　基础 2000 → 3138.39（×1.569）
　　基础 24000 → 38335.30（×1.597）

倍率固定 1.60；血量越低，被 65 ÷ (血量 + 110) 扣掉的越多，所以小血量生物吃亏，大体型接近满倍率。没有可调的衰减阈值。

人物负面
魔气环绕：5 范围内玩家理智每 5 秒流失 1 点。
饥饿诅咒：玩家受到生物攻击时 30% 概率触发，饥饿值消耗加快 20%，持续 30 秒。
暗影迟缓：玩家受到生物攻击时 20% 概率触发，移速 -20%，持续 10 秒。

击杀后掉落魔核碎片 1 到 3 个 + 生物原生材料。
原始生命不超过 149 的弱小生物只保留轻度强化，不追加入魔材料（什么魔核材料都不掉）。
""",
)

item(
    "rumo", "corruption_medium", "中度入魔", "入魔,中度",
    "入魔血量按 1.95 倍打折计算（血量越高越接近满倍率）；带 12% 减伤、半血触发 5 秒无敌护盾、2% 魔气反弹。",
    """
游戏内显示为「中度」。

核心强化 —— 生命值
　　最大生命 = 未入魔时的最大生命 × (1.95 − 65 ÷ (未入魔时的最大生命 + 110))

实际结果：

　　基础 100 → 164.05（×1.640）
　　基础 500 → 921.72（×1.843）
　　基础 2000 → 3838.39（×1.919）
　　基础 24000 → 46735.30（×1.947）

核心强化 —— 护甲
受到的所有外部伤害 ×0.88（即减免 12% 物理伤害）。

人物负面
魔气环绕：10 范围内玩家理智每 5 秒流失 3 点。
饥饿诅咒：玩家受到生物攻击时 30% 概率触发，饥饿值消耗加快 20%，持续 30 秒。
暗影迟缓：玩家受到生物攻击时 20% 概率触发，移速 -20%，持续 10 秒。
魔气反弹：生物受到玩家伤害时 10% 概率触发，反射 2% 伤害。

生物强化
限定易伤：生命值降到 50% 及以下会触发护盾，期间不受伤害（无敌），持续 5 秒，冷却 5 分钟。护盾表现为红色力场。

击杀后掉落魔核 1 到 2 个、魔核碎片 1 到 3 个 + 生物原生材料。
""",
)

item(
    "rumo", "corruption_deep", "深度入魔", "入魔,深度",
    "入魔血量按 2.35 倍打折计算（血量越高越接近满倍率）；无视减速、毒入骨髓、镜像混淆、魔化狂暴、祭天雷劫。",
    """
游戏内显示为「深度」。

核心强化 —— 生命值
　　最大生命 = 未入魔时的最大生命 × (2.35 − 65 ÷ (未入魔时的最大生命 + 110))

实际结果：

　　基础 100 → 204.05（×2.040）
　　基础 500 → 1121.72（×2.243）
　　基础 2000 → 4638.39（×2.319）
　　基础 24000 → 56335.30（×2.347）

核心强化 —— 护甲与体型
受到的所有外部伤害 ×0.8（即减免 20% 物理伤害），并额外获得 +5 点恒温/位面防御。
移动速度 +10%，体型放大到 1.2 倍。（月蚀晶翼狮、炽岩蝎龙、噬魂蛇这三只史诗 Boss 保留原外观，不放大）

核心强化 —— 无视减速
无视一切减速：只接受大于 1 的移速倍率。

人物负面
魔气环绕：10 范围内玩家理智每 5 秒流失 5 点。
饥饿诅咒：玩家受到生物攻击时 30% 概率触发，饥饿值消耗加快 20%，持续 30 秒。
暗影迟缓：玩家受到生物攻击时 20% 概率触发，移速 -20%，持续 10 秒。
魔气反弹：生物受到玩家伤害时 10% 概率触发，反射 5% 伤害，单次最多反弹 75 点。
镜像混淆：攻击时 10% 概率触发「镜像」，玩家接下来 5 秒内移动方向反转 180°。

生物强化
限定易伤：生命值在 30% 与 50% 之间（>30% 且 ≤50%）时触发无敌护盾 12 秒，冷却 5 分钟。护盾表现为红色力场。
毒入骨髓：普通攻击附带蚀骨毒。单次中毒 240 秒，不可叠加（可重置时间，上限 240 秒），命中当刻立即结算一跳。
　0 到 80 秒：每 10 秒造成 6 点伤害
　80 到 160 秒：每 10 秒造成 10 点伤害
　160 到 240 秒：每 10 秒造成 14 点伤害
　解毒：可用清心丸，也可用腺体。腺体解毒实际扣除「50 + 腺体原本治疗量」，血量不足时保底保留 5 点。
影灵随行：唤醒时额外召唤一个影体，生命值为该生物基础最大生命的一半。影体不携带任何魔化效果、无护甲保护，魂幡可直接炼化。每个本体只召唤一次。
吸食残骸：每当有玩家死亡，若死亡点 40 距离内有已深度入魔的 Boss，该 Boss 恢复自身损失生命值的 10%。
魔化狂暴：生命值降到 30% 及以下时进入狂暴——伤害 +30%、减伤与位面防御加成失效（移除受伤乘数与 +5 位面防御）、期间完全无法回血（任何治疗都被拦下）。
　　只有史诗 Boss 会额外获得技能冷却减半。
　　狂暴持续 300 秒（5 分钟），结束后才可能再次触发。
祭天雷劫：死亡后召唤天劫，持续 60 秒，每 6 秒落雷一次。以尸体为中心约 25 格范围内随机落点，先出标识，再降落天雷，劈中任意玩家都会造成伤害（随从、虚空戒等造成的击杀同样算玩家击杀，会照常触发雷劫）。伤害：普通深度入魔扣除 10% 最大生命，史诗 Boss 则必杀（100% 最大生命，无视无敌与伤害吸收）。标识出现 1.5 秒后落地，第一轮标识立即出现（不必再等 6 秒）。
　预警：落点 25 范围内的玩家会收到台词「天道有感，雷劫将至！」并在 HUD 上看到「祭天雷劫」倒计时；走出范围自动消失。

击杀后追加 1 个魔晶 + 生物原生材料，且原生掉落量翻倍。
　　例外：月蚀晶翼狮、炽岩蝎龙、噬魂蛇这三只自带完整掉落的史诗 Boss 不会翻倍、也不会追加魔晶。
""",
)

item(
    "rumo", "corruption_drops", "入魔掉落规则", "入魔,掉落,材料",
    "轻度掉魔核碎片、中度掉魔核、深度掉魔晶；原版生物按入魔程度掉落。",
    """
魔核碎片：击杀轻度入魔生物掉落魔核碎片 1 到 3 不等（原始生命不超过 149 的弱小生物不追加）。

魔核：击杀 Boss 生物、魔兽掉落；99 个魔核碎片合成；中度入魔生物掉落魔核 1 到 2 不等。无法摧毁、分解。

魔晶：击杀魔兽掉落；20 个魔核合成；深度入魔生物掉落魔晶 1。无法摧毁、分解。

原版生物按入魔程度掉落魔核碎片、魔核。原版生物深度入魔只会掉落魔晶 1，大型魔兽生物掉落魔晶 2。
""",
)

# ===========================================================================
# 卷目 3：丹药与炼制
# ===========================================================================
item(
    "danyao", "alchemy_rules", "炼丹总则", "炼制,丹药,规则",
    "用墟火炼丹基础成功率 50%，异火可提升至 100%；失败成废丹不返还材料。",
    """
使用墟火炼丹。不触发雷劫的丹药炼制概率均为 50%，无论成功与否，炼丹时间不变。

能触发丹劫的丹药：50% 概率不触发丹劫，炼丹必然失败成为废丹；50% 概率触发雷劫，躲避成功则炼制成功。服用破劫丹可跳过雷劫判定。

炼制材料须按照数量放入炼丹炉，可多不可少。炼制失败成为废丹，不返还材料，炼丹须谨慎。

使用异火炼丹可把炼制概率提高至 100%——强异火必定成功，而且不会改变丹劫判定（该应劫的照常应劫）。

另外，用异火本体炼丹不会消耗它（异火本体只当炉火）；只有分裂出来的火焰才是消耗品，会消耗 1 个。
""",
)

item(
    "danyao", "pill_tiers", "丹药品阶与丹劫", "炼制,丹药,丹劫,数值",
    "低阶黄 / 中阶玄 / 高阶地 / 天阶天 四档的炼制时间、产量与丹劫参数。",
    """
丹药分四阶：低阶（黄）、中阶（玄）、高阶（地）、天阶（天）。

低阶（炼制时间 2 分钟）
使用墟火炼制，不触发丹劫的丹药概率为 50%；使用异火炼制概率为 100%。
一次 99% 概率可制作 3 枚，1% 概率制作出 5 枚。

中阶（炼制时间 4 分钟）
使用墟火炼制，概率为 50%，失败则会炼制出废丹；使用异火炼制，概率为 100%。
一次 99% 概率可制作 1 枚，1% 概率可制作 2 枚。
中阶丹劫：每 10 秒触发一次雷击，一击必杀，会有标识；第 9 秒出现标识，1 秒后落地，持续 120 秒，玩家须躲避，否则炼丹失败。丹劫躲避失败会导致丹炉炸毁，留下 5 个木炭、1 个废丹。

高阶（炼制时间 8 分钟）
使用墟火炼制，概率为 20%，失败则会炼制出废丹；使用异火炼制，概率为 100%。
一次只能制作出 1 枚。
高阶丹劫：每 8 秒触发一次雷击，一击必杀，会有标识；第 7 秒出现标识，1 秒后落地，持续 120 秒，玩家须躲避，否则炼丹失败。丹劫躲避失败会导致丹炉炸毁，留下 5 个木炭、1 个废丹。

丹劫提示：炼丹期间 HUD 上会显示「丹劫」倒计时（按炉子剩余应劫时间走）；被丹劫劈死时死亡原因记为「丹劫天雷」。

天阶（天）
未实装。
""",
)

item(
    "fabao", "lj_moon_vase", "月魄凝液瓶", "法宝,特殊炼制,炼制",
    "不触发丹劫、100% 成功；用于灵玉台夜晚吸收天地灵气。",
    """
特殊炼制（不触发丹劫，炼制概率 100%）

炼丹炉炼制：""" + R(("鳞片", 1), ("玻璃碎片", 5), ("绿宝石", 1), ("魔晶", 1)) + """，炼制时间 4 分钟。

不能正常摧毁，可使用分解法杖分解。

祈雨：右键选择「祈雨」，消耗 20 点灵液，让世界持续下雨；10 分钟后自动恢复，再次祈雨会重新计时。灵液上限 100，不足时会提示「灵液不足。」""",
    recipe=R(("鳞片", 1), ("玻璃碎片", 5), ("绿宝石", 1), ("魔晶", 1)),
)

item(
    "fabao", "lj_reiki_gourd", "灵虚葫", "法宝,储物,异火",
    "吸收异火、存放丹药的 8 格葫芦；可跟随玩家并自动吸收 16 码内没有主人的异火。",
    """
特殊炼制（不触发丹劫，炼制概率 100%）

炼丹炉炼制：""" + R(("魔核", 2), ("铥矿", 4), ("蓝宝石", 1), ("红宝石", 1)) + """，炼制时间 4 分钟。

不能摧毁，无法用分解法杖分解。

吸收异火、存放丹药，8 格空间。

吸收异火时「异火焚身」的剩余时间会显示在 HUD 的负面状态面板上；只显示给当前持有葫芦的人，葫芦掉在地上时暂停并移除显示。
在物品栏里就能右键打开 / 关闭（容器只有一份，跟随葫芦打开的也是它）。打开状态下会一直在，不会因打开其他箱子类物品而自动关闭葫芦。
可鼠标拿起放置地面跟随；跟随状态下 16 码范围内有没有主人的异火，会自动飞进葫芦，吸收后归葫芦主人所有。
从物品栏 / 背包里用鼠标拿起葫芦后再放下，会优先放回原来的格子；原格不能用时才随意放置。
跟随状态下：左键是跟随状态葫芦的打开 / 关闭，右键跟随状态的葫芦就回收。
""",
    recipe=R(("魔核", 2), ("铥矿", 4), ("蓝宝石", 1), ("红宝石", 1)),
)

item(
    "fabao", "lj_soul_banner", "魂幡", "法宝,影怪,炼魂",
    "插入地面自动吸收影怪并转化为魔核；给予紫鳞妖焰可解锁「炼魂」。",
    """
特殊炼制（不触发丹劫，炼制概率 100%）

炼制（特殊炼制，必成、不触发丹劫）：""" + R(("噩梦燃料", 5), ("芦苇", 5), ("树枝", 5), ("魔晶", 2)) + """。

炼制时间 4 分钟。\n\n无法摧毁，可分解。

给予紫鳞妖焰可解锁技能「炼魂」。
插在地上会自动吸收原版的 4 种影怪，以及深度入魔产生的影体分身；每吸进一只化成一颗魔核，直接掉在魂幡下方。
　　其他影怪（影骑士、影主教、影车等）不会被吸入。
""",
    recipe=R(("噩梦燃料", 5), ("芦苇", 5), ("树枝", 5), ("魔晶", 2)),
)

item(
    "danyao", "lj_failed_pill", "废丹", "丹药,低阶,负面",
    "炼制失败的产物。使用后扣理智 30、生命 30，恢复 30 饱腹。",
    """
炼制失败的丹药。

使用后扣除理智 30、生命 30，恢复 30 饱腹。

炼丹失败必定产出废丹，且不返还材料，请谨慎开炉。
""",
)

item(
    "danyao", "lj_ningqi_pill", "凝气丸", "丹药,低阶,食物",
    "低阶丹药，恢复 50 饱食度；猪人也爱吃。",
    """
低阶丹药（黄），炼制时间 2 分钟。

材料：""" + R(("融灵草", 3), ("蜂蜜", 3)) + "、" + R(("橡果", 3, "acorn")) + " 或 " + R(("松果", 3, "pinecone")) + "、" + R(("魔核", 1)) + """。

效果：恢复 50 饱食度，猪人也爱吃。
""",
    recipe=R(("融灵草", 3), ("蜂蜜", 3)) + "、" + R(("橡果", 3, "acorn")) + " 或 " + R(("松果", 3, "pinecone")) + "、" + R(("魔核", 1)),
)

item(
    "danyao", "lj_warming_pill", "赤焰丹", "丹药,低阶,温度",
    "低阶丹药，升温效果，持续 2 天不会过冷。",
    """
低阶丹药（黄），炼制时间 2 分钟。

材料：""" + R(("融灵草", 3), ("硝石", 2), ("蝴蝶翅膀", 2), ("魔核", 1)) + """。

效果：升温效果，不会过冷，持续 2 天。
""",
    recipe=R(("融灵草", 3), ("硝石", 2), ("蝴蝶翅膀", 2), ("魔核", 1)),
)

item(
    "danyao", "lj_cooling_pill", "冷焰丹", "丹药,低阶,温度",
    "低阶丹药，降温效果，持续 2 天不会过热。",
    """
低阶丹药（黄），炼制时间 2 分钟。

材料：""" + R(("融灵草", 3), ("硝石", 2), ("月娥翅膀", 2), ("魔核", 1)) + """。

效果：降温效果，不会过热，持续 2 天。
""",
    recipe=R(("融灵草", 3), ("硝石", 2), ("月娥翅膀", 2), ("魔核", 1)),
)

item(
    "danyao", "lj_stillness_pill", "清心丸", "丹药,低阶,境界",
    "死亡掉阶后服用，可稳固心神、继续修炼。",
    """
低阶丹药（黄），炼制时间 2 分钟。

材料：""" + R(("魔核", 1), ("腺体", 2), ("格罗姆粘液", 1), ("融灵草", 3)) + """。

效果：死亡后掉阶后服用，可稳固心神，继续修炼。

这是死亡掉阶后恢复修炼资格的必要丹药，否则会止步不前。

额外用途：可以解毒——服用后直接解除噬魂蛇毒（详见「深度入魔」的毒入骨髓）。
""",
    recipe=R(("魔核", 1), ("腺体", 2), ("格罗姆粘液", 1), ("融灵草", 3)),
)

item(
    "danyao", "lj_reiki_pill", "回灵丹", "丹药,中阶,灵力",
    "中阶丹药，回复 30 灵力值。",
    """
中阶丹药（玄），炼制时间 4 分钟。

材料：""" + R(("绿蘑菇", 1), ("融灵草", 1), ("高脚鸟蛋", 1), ("魔核", 1)) + """。

效果：回复 30 灵力值。
""",
    recipe=R(("绿蘑菇", 1), ("融灵草", 1), ("高脚鸟蛋", 1), ("魔核", 1)),
)

item(
    "danyao", "lj_explosion_pill", "爆裂丸", "丹药,中阶,增伤",
    "中阶丹药，短时间内提高 30% 伤害，持续 3 分钟。",
    """
中阶丹药（玄），炼制时间 4 分钟。

材料：""" + R(("辣椒", 1), ("噩梦燃料", 1), ("蜂刺", 5), ("魔核", 1)) + """。

效果：短时间内提高 30% 伤害，持续 3 分钟。
""",
    recipe=R(("辣椒", 1), ("噩梦燃料", 1), ("蜂刺", 5), ("魔核", 1)),
)

item(
    "danyao", "lj_drying_pill", "防潮丹", "丹药,中阶,防潮",
    "中阶丹药，免疫潮湿，持续 5 天。",
    """
中阶丹药（玄），炼制时间 4 分钟。

材料：""" + R(("融灵草", 1), ("橙宝石", 1), ("硝石", 5), ("魔核", 1)) + """。

效果：免疫潮湿，持续 5 天。
""",
    recipe=R(("融灵草", 1), ("橙宝石", 1), ("硝石", 5), ("魔核", 1)),
)

item(
    "danyao", "lj_invincible_pill", "不灭丹", "丹药,中阶,保命",
    "中阶丹药，30 秒内生命值最低为 1。",
    """
中阶丹药（玄），炼制时间 4 分钟。

材料：""" + R(("融灵草", 5), ("龙爪花", 2), ("告密的心", 1), ("魔晶", 1)) + """。

效果：30 秒「不灭」状态，30 秒内生命值最低为 1，其他数值不受影响。
""",
    recipe=R(("融灵草", 5), ("龙爪花", 2), ("告密的心", 1), ("魔晶", 1)),
)

item(
    "danyao", "lj_bigu_pill", "辟谷丹", "丹药,中阶,境界",
    "中阶丹药，配合悟道淬体台打坐 10 秒，提升炼筋至辟谷境界。",
    """
中阶丹药（玄），炼制时间 4 分钟。

材料：""" + R(("猪皮", 2), ("蕨类植物", 5), ("蓝宝石", 2), ("魔核", 2)) + """。

效果：服用此丹药，在悟道淬体台打坐 10 秒，提升炼筋至辟谷境界。
""",
    recipe=R(("猪皮", 2), ("蕨类植物", 5), ("蓝宝石", 2), ("魔核", 2)),
)

item(
    "danyao", "lj_yinqi_pill", "引气丹", "丹药,中阶,境界",
    "中阶丹药，配合悟道淬体台打坐 10 秒提升境界。",
    """
中阶丹药（玄），炼制时间 4 分钟。

材料：""" + R(("铥矿", 2), ("兔毛", 5), ("红宝石", 2), ("魔核", 5)) + """。

效果：服用此丹药，在悟道淬体台打坐 10 秒，辟谷境界提升至入微。
""",
    recipe=R(("铥矿", 2), ("兔毛", 5), ("红宝石", 2), ("魔核", 5)),
)

item(
    "danyao", "lj_ruwei_pill", "入微丹（丹劫）", "丹药,中阶,境界,丹劫",
    "中阶丹劫丹药，助引气强者突破晋升入微。",
    """
中阶丹药（玄），炼制时间 4 分钟。可触发丹劫。

材料：""" + R(("藤壶", 5), ("饼干切割机壳", 5), ("暗影心房", 1), ("魔晶", 1)) + """。

效果：服用此丹药，在悟道淬体台打坐 10 秒，助引气强者突破晋升入微的界限，提升实力。
""",
    recipe=R(("藤壶", 5), ("饼干切割机壳", 5), ("暗影心房", 1), ("魔晶", 1)),
)

item(
    "danyao", "lj_restore_pill", "复灵丹（丹劫）", "丹药,中阶,灵力,丹劫",
    "中阶丹劫丹药，灵气充盈，每 2 秒回复 1 点灵力值，持续 1 天。",
    """
中阶丹药（玄），炼制时间 4 分钟。可触发丹劫。

材料：""" + R(("融灵草", 5), ("蘑菇皮", 1), ("发光浆果", 2), ("魔晶", 1)) + """。

效果：灵气充盈，每 2 秒回复 1 点灵力值，持续 1 天。
""",
    recipe=R(("融灵草", 5), ("蘑菇皮", 1), ("发光浆果", 2), ("魔晶", 1)),
)

item(
    "danyao", "lj_extraordinary_pill", "超凡丹（丹劫）", "丹药,高阶,境界,丹劫",
    "高阶丹劫丹药，助入微强者提升至超凡级别。",
    """
高阶丹药（地），炼制时间 8 分钟。可触发丹劫。

材料：""" + R(("活木", 5), ("噬魂蛇皮", 2), ("血蝠精血", 1), ("魔晶", 3)) + """。

效果：服用此丹药，在悟道淬体台打坐 10 秒，助入微提升超凡级别强者的实力。
""",
    recipe=R(("活木", 5), ("噬魂蛇皮", 2), ("血蝠精血", 1), ("魔晶", 3)),
)

item(
    "danyao", "lj_heying_pill", "合婴丹（丹劫）", "丹药,高阶,境界,丹劫",
    "高阶丹劫丹药，配合悟道淬体台打坐 10 秒，提升合婴级别强者的实力。",
    """
高阶丹药（地），炼制时间 8 分钟。可触发丹劫。

材料：""" + R(("龙爪花", 3), ("黄宝石", 2), ("紫晶壳", 1), ("魔晶", 5)) + """。

效果：服用此丹药，在悟道淬体台打坐 10 秒，提升合婴级别强者的实力。
""",
    recipe=R(("龙爪花", 3), ("黄宝石", 2), ("紫晶壳", 1), ("魔晶", 5)),
)

item(
    "danyao", "lj_disaster_pill", "破劫丹（丹劫）", "丹药,高阶,丹劫,保命",
    "高阶丹药，服用后免疫丹劫雷击，直至消亡。",
    """
高阶丹药（地），炼制时间 8 分钟。

材料：""" + R(("羊奶", 2), ("黄油", 2), ("蜂王浆", 2), ("魔晶", 2)) + """。

效果：服用后免疫丹劫雷击，直至消亡。

用于跳过炼制其他丹药时的雷劫判定——不触发丹劫则炼丹必然失败成为废丹，服用破劫丹可跳过雷劫判定直接成功。
""",
    recipe=R(("羊奶", 2), ("黄油", 2), ("蜂王浆", 2), ("魔晶", 2)),
)

item(
    "danyao", "lj_juling_pill", "具灵丹（丹劫）", "丹药,高阶,境界,丹劫",
    "高阶丹劫丹药，极为稀有，能突破具灵境界。",
    """
高阶丹药（地），炼制时间 8 分钟。可触发丹劫。

材料：""" + R(("彩虹宝石", 1), ("格罗姆翅膀", 1), ("蝎龙骨", 1), ("魔晶", 10)) + """。

效果：服用此丹药，在悟道淬体台打坐 10 秒，极为稀有，能突破具灵境界。
""",
    recipe=R(("彩虹宝石", 1), ("格罗姆翅膀", 1), ("蝎龙骨", 1), ("魔晶", 10)),
)

# ===========================================================================
# 卷目 4：精炼材料
# ===========================================================================
item(
    "cailiao", "lj_magic_debris", "魔核碎片", "材料,魔气",
    "最低阶的魔气结晶，轻度入魔生物掉落，可合成魔核。",
    """
来源：击杀轻度入魔生物掉落，1 到 3 不等。

高阶用途：99 个魔核碎片可合成 1 个魔核；也是淬铁灵剑的主要材料。

无法摧毁、分解。
""",
)

item(
    "cailiao", "lj_magic_core", "魔核", "材料,魔气,合成",
    "99 个魔核碎片合成。Boss、魔兽与中度入魔生物掉落。",
    """
合成：99 个魔核碎片合成。

来源：击杀 Boss 生物、魔兽掉落；中度入魔生物掉落魔核 1 到 2 不等。

无法摧毁、分解。

可在 <灵界>、<魔法>、<精炼> 栏位制作。

高阶用途：20 个魔核可合成 1 个魔晶；也是多种丹药、建筑与法宝的核心材料。
""",
    recipe=R(("魔核碎片", 99)),
)

item(
    "cailiao", "lj_magic_crystal", "魔晶", "材料,魔气,合成",
    "20 个魔核合成。魔兽与深度入魔生物掉落，高阶丹药与盔甲的必需品。",
    """
合成：20 个魔核合成。

来源：击杀魔兽掉落；深度入魔生物掉落魔晶 1。

无法摧毁、分解。

原版生物深度入魔只会掉落魔晶 1，大型魔兽生物掉落魔晶 2。

可在 <灵界>、<魔法>、<精炼> 栏位制作。
""",
    recipe=R(("魔核", 20)),
)

item(
    "cailiao", "lj_scorpion_dragon_bone", "蝎龙骨", "材料,Boss掉落",
    "远古遗迹（残骸小岛）史诗 Boss 炽岩蝎龙的骨骼，用于制作骸龙甲与具灵丹。",
    """
来源：击杀残骸祭坛（远古遗迹）的史诗级 Boss「炽岩蝎龙」掉落 1 个。

用途：骸龙甲、具灵丹的核心材料。
""",
)

item(
    "cailiao", "lj_amethyst_shell", "紫晶壳", "材料,Boss掉落",
    "月蚀晶翼狮的晶壳，用于制作晶羽冠与合婴丹。",
    """
来源：击杀史诗级 Boss「月蚀晶翼狮」掉落 1 个。

用途：晶羽冠、合婴丹的核心材料。
""",
)

item(
    "cailiao", "lj_lion_bone", "狮骨", "材料,Boss掉落",
    "月蚀晶翼狮的骨骼。",
    """
来源：击杀史诗级 Boss「月蚀晶翼狮」掉落 1 个。
""",
)

item(
    "cailiao", "lj_bat_blood", "血蝠精血", "材料,魔兽掉落",
    "暗影血蝠的精血，用于制作骸龙甲、晶羽冠与超凡丹；也可直接补满盔甲耐久。",
    """
来源：击杀蝴蝶岛中的暗影血蝠固定掉落 1 个。

用途：骸龙甲、晶羽冠、超凡丹。

血蝠精血 1 个可恢复骸龙甲 / 晶羽冠的满耐久。

堆叠上限 20。
""",
)

item(
    "cailiao", "lj_soul_snake_skin", "噬魂蛇皮", "材料,Boss掉落",
    "噬魂蛇的蛇皮，用于制作超凡丹。",
    """
来源：击杀隐藏 Boss「噬魂蛇」掉落 3 个。

用途：超凡丹。
""",
)

item(
    "cailiao", "lj_snake_skin", "噬魂蛇鳞片", "材料,Boss机制",
    "噬魂蛇每受 2000 伤害掉落的鳞片；玩家无法拾取，可用异火烧毁。",
    """
来源：噬魂蛇每受 2000 血量伤害会掉落，玩家无法拾取，可用异火烧毁。

机制相关：噬魂蛇血量首次掉到 50% 后，会主动找寻并吞食鳞片恢复自身血量，每个回复 1000 血量。所以要及时用异火烧掉地上的鳞片。
""",
)

# —— 灵植的「采集产物」：与植物本身是不同的预制体，代码里炼丹用的是这些 ——
item(
    "cailiao", "lj_reiki_cutgrass", "采下的融灵草", "材料,灵植,炼丹",
    "从融灵草上采下来的部分，几乎所有丹药的基础材料。",
    """
来源：采集「融灵草」获得，一次得 草 1 + 采下的融灵草 1。

用途：除少数几种外，几乎所有丹药都要用它——凝气丸、赤焰丹、冷焰丹、清心丸、回灵丹、防潮丹、不灭丹、辟谷丹、复灵丹，以及修复残骸祭坛。

注意：游戏里「融灵草」是长在地上的植物，「采下的融灵草」才是放进炼丹炉的材料，两者是不同的物品。
""",
)

item(
    "cailiao", "lj_reiki_dug_grass", "融灵草根", "材料,灵植",
    "挖走融灵草留下的根，可以重新种回去。",
    """
来源：采集「融灵草」时有 5% 概率额外获得。

用途：把融灵草移植到别处。
""",
)

item(
    "cailiao", "lj_red_magic_cutflower", "采下的龙爪花", "材料,灵植,炼丹",
    "从龙爪花上采下来的部分，用于中高阶丹药。",
    """
来源：采集「龙爪花」获得，一次得 花瓣 1 + 采下的龙爪花 1。

用途：不灭丹、合婴丹。
""",
)

item(
    "cailiao", "lj_red_magic_dug_flower", "龙爪花根", "材料,灵植",
    "挖走龙爪花留下的根。",
    """
来源：采集「龙爪花」时有 5% 概率额外获得。

用途：把龙爪花移植到别处。
""",
)

item(
    "cailiao", "lj_purple_magic_bloom", "紫晶塑体花瓣", "材料,灵植,修复",
    "从紫晶塑体花上砍下来的花瓣，用于修复残骸祭坛。",
    """
来源：砍伐「紫晶塑体花」获得。旁边通常有月蚀晶翼狮守着；狮王在场时砍伐不会掉落。

用途：修复残骸祭坛需要 1 个。
""",
)

# ===========================================================================
# 卷目 5：建筑
# ===========================================================================
item(
    "jianzhu", "lj_alchemy_furnace", "炼丹炉", "建筑,炼制",
    "炼丹核心建筑。5 格空间，4 格材料 + 1 格火种。",
    """
制作：""" + R(("木板", 5), ("砖块", 5), ("绳子", 5), ("硝石", 10)) + """。

可使用锤子摧毁，摧毁后返还 2 木板、2 砖块、5 硝石。

5 个格子：4 格材料，1 格燃料（墟火 / 异火），增加炼制按钮。

可在 <灵界>、<建筑> 栏位制作。
""",
    recipe=R(("木板", 5), ("砖块", 5), ("绳子", 5), ("硝石", 10)),
)

item(
    "jianzhu", "lj_wudao_chair", "悟道淬体台", "建筑,境界,打坐",
    "闭关打坐的专属建筑。稳固境界、回精神与灵力、停止消耗饥饿，每 10 秒获得 1 经验。",
    """
制作：""" + R(("草", 12), ("石头", 12), ("噩梦燃料", 6), ("魔核", 1)) + """。

可使用锤子摧毁，摧毁后返还 草 6、石头 6、噩梦燃料 3。

提升阶段、境界所需的闭关专属建筑类物品。打坐可稳固境界，每 3 秒回复 1 点精神值、1 点灵力值，停止消耗饥饿。

挂机神器，每 10 秒获得 1 经验。

所有境界的 3 / 6 / 9 阶都需要打坐提升；引气以上境界需要额外服用特定丹药才可配合打坐提升。

可在 <灵界>、<建筑> 栏位制作。
""",
    recipe=R(("草", 12), ("石头", 12), ("噩梦燃料", 6), ("魔核", 1)),
)

item(
    "jianzhu", "lj_huangjie_box", "荒界纳物箱", "建筑,储物",
    "3×11 + 1×10 的大箱子，可注入魔核收集、蓝宝石返鲜、魔晶无限堆叠。",
    """
制作：""" + R(("魔核", 1), ("木板", 5), ("莎草纸", 2), ("石砖", 5)) + """。

可使用锤子摧毁，可被火把燃烧，摧毁后返还 木板 2、莎草纸 1、石砖 2。

存放物品 3×11 + 1×10 格，具备原版箱子效果。

没有开启人数限制，多名玩家可以同时打开同一个箱子。

附加功能：
左上角「整理」——增加整理功能（整理时不会再把无限堆叠里超出的部分掉到地上；同一种物品会按数量从多到少排）。
右下角「封」——关闭箱子。
右下方「安全入库」——箱子内已存在的物品，点击安全入库，自身的东西会一键放入箱子。

注入强化：
升级方式：把材料拿在手上，左键点箱子即可升级，一次只消耗 1 份材料。

给予魔核，增加收集功能（收集范围可在 mod 设置里改成 10 / 50 / 100 / 200 / 500 / 全部，默认 10）。
给予蓝宝石，增加返鲜功能。
给予魔晶，解锁无限堆叠。

可在 <灵界>、<建筑>、<储存方案> 栏位制作。

[[图片:images/lingjie/anim/huangjie_box_ui.png|箱子界面：上方 3×11 格、下方单独一行 1×10 格；按钮是整理、收纳、返鲜、安全入库、封]]
""",
    recipe=R(("魔核", 1), ("木板", 5), ("莎草纸", 2), ("石砖", 5)),
)

item(
    "jianzhu", "lj_cuiju_box", "聚气淬具匣", "建筑,储物,武器",
    "7×7 + 1 格的武器防具柜，第一格可展示武器，注入魔晶可缓慢修复耐久。",
    """
制作：""" + R(("魔核", 1), ("木板", 5), ("莎草纸", 2), ("石砖", 5)) + """。

可使用锤子摧毁，可被火把燃烧，摧毁后返还 木板 2、莎草纸 1、石砖 2。

存放武器防具，7×7 + 1 格子。第一个格子是可以展示武器的，单独放入武器有展示效果。

给予魔晶，提供缓慢恢复耐久的效​果。

可在 <灵界>、<建筑>、<储存方案> 栏位制作。

[[图片:images/lingjie/anim/cuiju_box_ui.png|淬具匣界面：7×7 格，上方单独一格用来展示武器]]
""",
    recipe=R(("魔核", 1), ("木板", 5), ("莎草纸", 2), ("石砖", 5)),
)

item(
    "jianzhu", "lj_reiki_tablelamp", "灵虚光盏", "建筑,光源",
    "2 格空间的光源。放入分裂的火焰加 10 码照明维持 8 分钟，放入异火则永久照明。",
    """
制作：""" + R(("魔核", 2), ("木板", 5)) + """。

可使用锤子摧毁，不返还材料。

2 格空间。放入分裂出的火焰可增加照明范围，一个加 10 码范围，维持 8 分钟；放入异火本体则永久提供照明。

可在 <灵界>、<建筑>、<光源> 栏位制作。
""",
    recipe=R(("魔核", 2), ("木板", 5)),
)

item(
    "jianzhu", "lj_reiki_table", "灵玉台", "建筑,灵气",
    "二本科技建筑。夜晚放入月魄凝液瓶，吸收天地灵气（至少 30 秒）。",
    """
制作：""" + R(("金块", 5), ("木头", 5), ("石砖", 10)) + """。

可使用锤子摧毁，二本制作，摧毁后返还 金块 2、木头 2、石砖 5。

夜晚放入月魄凝液瓶，吸收天地灵气；PS：至少吸取 30 秒。
""",
    recipe=R(("金块", 5), ("木头", 5), ("石砖", 10)),
)

item(
    "jianzhu", "lj_reiki_cultivatepool", "玄灵培育池（未实装）", "建筑,灵植,未实装",
    "mod 源码中未实装，前台暂不展示。",
    """
⚠️ 该内容在 mod 源码中未实装，本条目已隐藏，不会出现在前台。

核对依据（2026 对照 lj_mod 源码）：
- 全代码搜索不存在预制体 `lj_reiki_cultivatepool`
- `scripts/main/config/prefab_groups.lua` 的建筑分类里没有登记
- `scripts/main/localization/language_zh.lua` 里没有任何相关中文名
- 仅 `scripts/prefabs/alchemy/lj_moon_vase.lua` 有一句注释：「妖树培育用途尚未接入，消耗比例待玩法确定后统一。」

原定描述如下（供后续实装后启用）：

制作：""" + R(("魔晶", 1), ("石砖", 10), ("燧石", 10)) + """。
可使用锤子摧毁。
放入魂元妖树根，供其生长。
""",
    recipe=R(("魔晶", 1), ("石砖", 10), ("燧石", 10)),
    visible=False,
)

item(
    "jianzhu", "lj_flag", "阵旗", "建筑,阵法",
    "给阵法划分范围。最远 3 格范围相互连接。",
    """
制作：""" + R(("莎草纸", 1), ("木头", 5), ("绳子", 2), ("魔核", 1)) + """。

可使用锤子摧毁，摧毁后不返还材料。

给阵法划分范围，最远 3 格范围相互连接。

阵法范围根据阵旗相连划分，例如一个圆形、正 / 长方形，类似在地图上围一圈虚线，显示大概范围。

可在 <灵界>、<建筑> 栏位制作。
""",
    recipe=R(("莎草纸", 1), ("木头", 5), ("绳子", 2), ("魔核", 1)),
)

item(
    "jianzhu", "lj_supernatural_power_pivot", "玄阵枢纽", "建筑,阵法",
    "为阵法提供能量。4 个格子，可放入多个阵眼提供多重效果。",
    """
特殊制作：靠近修复的残骸祭坛解锁，每次制作都需要靠近残骸祭坛。

制作：""" + R(("魔晶", 1), ("树枝", 2), ("电子元件", 2)) + """。

可使用锤子摧毁，摧毁后返还全部材料，放入的核心也会掉落在地上。

为阵法提供能量，放入阵眼启动。4 个格子，可放入多个阵眼提供多重效果。

可在 <灵界>、<建筑> 栏位制作。
""",
    recipe=R(("魔晶", 1), ("树枝", 2), ("电子元件", 2)),
)

# ===========================================================================
# 卷目 6：武器与盔甲
# ===========================================================================
item(
    "wuqi", "lj_ordinary_sword", "淬铁灵剑", "武器,近战,前期",
    "攻击 45、手持加 10% 移速，可用魔核碎片修复的过渡兵刃。",
    """
制作：""" + R(("魔核碎片", 20), ("树枝", 5), ("绳子", 2), ("燧石", 2)) + """。

攻击 45，手持增加 10% 移动速度；攻击范围与其他普通武器一致。

耐久 100（可攻击 100 下），可用魔核碎片修复，1 个魔核碎片回复 10 点耐久。

定位：前期近战便携型修仙武器，过渡到中期法宝的基础兵刃，兼顾防身与轻度探索需求。

可在 <灵界>、<武器> 栏位制作。
""",
    recipe=R(("魔核碎片", 20), ("树枝", 5), ("绳子", 2), ("燧石", 2)),
)

item(
    "wuqi", "lj_reiki_bow", "灵韵", "武器,远程,冰冻,法宝",
    "攻击 78、暴击 20%、附带冰蚀与 10 点位面伤害；右键「玄冰灌注」造成 300 伤害并冻结。",
    """
制作：""" + R(("魔晶", 5), ("伏特羊角", 2), ("冰霜业火本体", None), ("活木", 5), ("噩梦燃料", 10)) + """。

无法摧毁、分解。因异火不好放入物品栏 / 背包，制作时打开灵虚葫，系统能检查到即可。

基础属性
攻击力 78，暴击率 20%，暴击伤害 ×1.8。
攻击命中后附加「冰蚀」减益：持续 8 秒，每 0.5 秒造成 16 点伤害，再次命中会重置时间。增加 10 点位面伤害。
射程 10，耐久 200。攻击间隔与长矛等普通武器一致。攻击一次减 1 点耐久。
耐久为 0 不消失，可继续攻击，但伤害降为 10。可用魔核填充耐久，1 个魔核填充 100。

「冰蚀」debuff：命中敌方后施加 1 层冰冻效果，叠加至对应生物冰冻抗性阈值时触发「冻结」。
　小型生物 2 层 = 冻结 2 秒
　中型生物 3 层 = 冻结 1.5 秒
　大型生物 5 层 = 冻结 1 秒

技能：玄冰灌注（右键主动）
消耗 20 点灵力值，释放一只巨箭，造成 300 伤害，并冻结目标 3 秒。冷却 12 秒。

击杀任意生物，恢复 5 点灵力值。

可在 <灵界>、<武器> 栏位制作。
""",
    recipe=R(("魔晶", 5), ("伏特羊角", 2), ("冰霜业火本体", None), ("活木", 5), ("噩梦燃料", 10)),
)

item(
    "wuqi", "lj_star_sword", "星陨", "武器,近战,火焰,法宝",
    "攻击 88、暴击 22%、附带焚灼；越打越痛，右键「陨火刺」无敌突进 150 伤害。",
    """
制作：""" + R(("魔晶", 5), ("一角鲸的角", 1), ("龙炎心火本体", None), ("活木", 5), ("噩梦燃料", 10)) + """。

无法摧毁、分解。因异火不好放入物品栏 / 背包，制作时打开灵虚葫，系统能检查到即可。

基础属性
攻击力 88，暴击率 22%，暴击伤害 ×2。
攻击命中后附加「焚灼」减益：持续 8 秒，每 0.5 秒造成 16 点火焰伤害，再次命中会重置时间。增加 10 点位面伤害。
耐久 300。攻击间隔与攻击距离都与长矛等普通武器一致。攻击一次减 1 点耐久。
耐久为 0 不消失，可继续攻击，但伤害降为 10。可用魔核填充耐久，1 个魔核填充 100。

充能机制
攻击时武器自动充能（每攻击 5 次充能 25%），充能满 100% 后进入「星陨状态」。
停止攻击 10 秒充能状态掉为 0。
星陨状态下，攻击会增伤，每攻击一下增加 5 点伤害。

技能：陨火刺（右键主动）
消耗 10 点灵力值，往前冲刺一段距离（借鉴女武神奔雷矛），过程中免疫伤害（约 0.8 秒无敌帧），造成 150 点伤害（基础 140 + 10 点位面伤害），冷却 2 秒。

[[图片:images/lingjie/anim/star_sword_charge.png|满充能时的剑身特效]]

[[图片:images/lingjie/anim/star_sword_hit.png|星陨命中特效]]

击杀任意生物，恢复 5 点灵力值。

可在 <灵界>、<武器> 栏位制作。
""",
    recipe=R(("魔晶", 5), ("一角鲸的角", 1), ("龙炎心火本体", None), ("活木", 5), ("噩梦燃料", 10)),
)

item(
    "wuqi", "lj_keel_armour", "骸龙甲", "盔甲,防御,回耐久",
    "1500 耐久、初始 80% 防御；脱战时「以血修甲」自动回耐久。",
    """
特殊制作：靠近修复的残骸祭坛解锁，每次制作都需要靠近残骸祭坛。

制作：""" + R(("蝎龙骨", 1), ("血蝠精血", 4), ("魔晶", 3)) + """。

基础属性
1500 耐久，初始防御 80%。
给予魔晶 1 个提升 1% 防御，最高 90。
1 点位面防御，最高 10。
血蝠精血 1 个可恢复满耐久。

「以血修甲」机制
仅在脱战状态下触发，即只有在玩家 5 秒内未受到任何伤害时。
血量大于 30% 时：每 2 秒扣除 1 点血量，恢复 10 点耐久。
血量低于 30% 时：不会扣血，也不会恢复护甲耐久。
耐久为 0 不消失，但不提供任何保护。

可在 <灵界>、<盔甲> 栏位制作。
""",
    recipe=R(("蝎龙骨", 1), ("血蝠精血", 4), ("魔晶", 3)),
)

item(
    "wuqi", "lj_crystalcrown", "晶羽冠", "盔甲,防御,回耐久",
    "与骸龙甲同规格的头部防具；两件同时穿戴可免疫镜像混淆。",
    """
特殊制作：靠近修复的残骸祭坛解锁，每次制作都需要靠近残骸祭坛。

制作：""" + R(("紫晶壳", 1), ("血蝠精血", 4), ("魔晶", 3)) + """。

基础属性
1500 耐久，初始防御 80%。
给予魔晶 1 个提升 1% 防御，最高 90。
1 点位面防御，最高 10。
血蝠精血 1 个可恢复满耐久。

「以血修甲」机制
仅在脱战状态下触发，即只有在玩家 5 秒内未受到任何伤害时。
血量大于 30% 时：每 2 秒扣除 1 点血量，恢复 10 点耐久。
血量低于 30% 时：不会扣血，也不会恢复护甲耐久。
耐久为 0 不消失，但不提供任何保护。

套装效果：骸龙甲、晶羽冠同时穿戴可免疫镜像混淆。

可在 <灵界>、<盔甲> 栏位制作。
""",
    recipe=R(("紫晶壳", 1), ("血蝠精血", 4), ("魔晶", 3)),
)

# ===========================================================================
# 卷目 7：法宝与工具
# ===========================================================================
item(
    "fabao", "lj_void_ring", "虚空戒", "法宝,工具,开局自带",
    "开局自带的戒指，一格空间可放墟火 / 异火，装备后可远程点燃目标。",
    """
特殊制作：靠近修复的残骸祭坛解锁，每次制作都需要靠近残骸祭坛。

制作：""" + R(("魔晶", 1), ("红宝石", 1), ("蓝宝石", 1), ("紫宝石", 1), ("黄宝石", 1), ("橙宝石", 1), ("绿宝石", 1)) + """。

不能摧毁，无法用分解法杖分解。

开局自带，一格空间，可放入墟火 / 异火。戒内放有异火本体时，装备后右键目标就能像火魔杖一样远程点燃：射出火球，射程 8 到 10，消耗 10 点灵力值。
命中效果与火魔杖相同：点燃目标，或给可燃燃料装置补一份燃料；顺带解冻目标、叫醒睡眠中的目标，并让它仇恨你。本身不造成伤害；戒内没有异火时不会出现点燃动作。

可在 <灵界>、<工具> 栏位制作。
""",
    recipe=R(("魔晶", 1), ("红宝石", 1), ("蓝宝石", 1), ("紫宝石", 1), ("黄宝石", 1), ("橙宝石", 1), ("绿宝石", 1)),
)

# ===========================================================================
# 卷目 8：阵法灵技
# ===========================================================================
item(
    "zhenfa", "zhenfa_overview", "阵法总览", "阵法,机制",
    "阵法由阵旗与阵眼组成；阵旗划分范围，阵眼放入玄阵枢纽启动。",
    """
设定：阵法由不同数量阵旗、阵眼组成，提供范围内一定的实用效果。

范围（1 地皮 = 4 游戏单位）
　最少需要 4 面阵旗才能成阵。
　阵旗之间最少相隔 3 地皮（12 单位），最远相连 6 地皮（24 单位）。
　整个阵法的外接矩形长、宽均不得超过 12 地皮（48 单位）。
　阵法范围根据阵旗相连划分，比如一个圆形、正 / 长方形，类似在地图上围一圈虚线，显示大概范围。

启动：阵眼需放入玄阵枢纽启动。玄阵枢纽有 4 个格子，可放入多个阵眼提供多重效果。
多个相同阵眼不会叠加数值，只是把不同的效果位并集起来。

目前共 4 座阵法：四季调和阵、生机回春阵、驱灵锁魔阵、极温庇护阵。
""",
)

item(
    "zhenfa", "zhen_siji", "四季调和阵", "阵法,季节,农业",
    "范围内农田作物春夏秋冬都正常生长。",
    """
范围：最少 4 面阵旗；阵法外接矩形不超过 12×12 地皮。

阵眼：四季核心（""" + R(("巨鹿眼球", 1), ("铥矿", 2), ("绿宝石", 1), ("魔核", 1)) + """）。

效果：适应季节。范围内农田所有作物春夏秋冬都正常生长；除农作物外其他的东西正常生长（按饥荒原版的正常生长规则），不受阵法影响。
""",
)

item(
    "zhenfa", "zhen_huichun", "生机回春阵", "阵法,农业,光照",
    "范围内提供光照，植物不枯萎、夜晚也能生长。",
    """
阵眼：灵植核心（""" + R(("克劳斯袋钥匙", None), ("绿宝石", 1), ("噩梦燃料", 5), ("金块", 5), ("魔核", 1)) + """）。

效果：范围内提供一定光照；阵法内所有植物作物不会枯萎，枯萎的会恢复生机；夜晚农作物也会正常生长。
""",
)

item(
    "zhenfa", "zhen_quling", "驱灵锁魔阵", "阵法,防御",
    "只拦生物不拦玩家：阵外敌对生物进不来，阵内生物出不去。",
    """
阵眼：镇魔枢核（""" + R(("暗影心房", 1), ("铥矿", 5), ("噩梦燃料", 10), ("紫宝石", 1), ("活木", 2), ("魔晶", 2)) + """）。

效果：只拦生物不拦玩家。范围内无法生成敌对生物，或把敌对生物拦截在阵外；已经在阵内的生物无法出去。

出生驱逐：敌对生物如果直接出生在阵内，会被立刻送到阵外最近的可站立位置——陆生生物只能落陆地，水生与飞行生物可以落海面，而且不会落到洞穴口旁边；送到之后才按阵外生物登记。
""",
)

item(
    "zhenfa", "zhen_jiwen", "极温庇护阵", "阵法,温度,理智",
    "完全中和极端温度、抵消冰火伤害，并缓慢恢复理智。",
    """
阵眼：恒温晶核（""" + R(("唤星法杖", 1), ("唤月法杖", 1), ("巨鹿眼球", 1), ("鳞片", 1), ("噩梦燃料", 10), ("魔晶", 2)) + """）。

效果：范围内完全中和极端温度（无冻伤 / 中暑）；抵消冰火伤害，范围内无自燃 / 冻结；玩家精神值缓慢恢复，每 60 秒恢复 30 点理智。
""",
)

item(
    "zhenfa", "lj_seasons_nucleus", "四季核心", "阵法,阵眼,魔法",
    "四季调和阵的阵眼。",
    """
阵法核心 / 阵眼。

制作：""" + R(("巨鹿眼球", 1), ("铥矿", 2), ("绿宝石", 1), ("魔核", 1)) + """。

用于四季调和阵：范围内农田所有作物春夏秋冬都正常生长。

可在 <灵界>、<魔法> 栏位制作。
""",
    recipe=R(("巨鹿眼球", 1), ("铥矿", 2), ("绿宝石", 1), ("魔核", 1)),
)

item(
    "zhenfa", "lj_plant_nucleus", "灵植核心", "阵法,阵眼,魔法",
    "生机回春阵的阵眼。",
    """
阵法核心 / 阵眼。

制作：""" + R(("克劳斯袋钥匙", None), ("绿宝石", 1), ("噩梦燃料", 5), ("金块", 5), ("魔核", 1)) + """。

用于生机回春阵：范围内提供光照，植物不枯萎、夜晚也能生长。

可在 <灵界>、<魔法> 栏位制作。
""",
    recipe=R(("克劳斯袋钥匙", None), ("绿宝石", 1), ("噩梦燃料", 5), ("金块", 5), ("魔核", 1)),
)

item(
    "zhenfa", "lj_subdue_demons_nucleus", "镇魔枢核", "阵法,阵眼,魔法",
    "驱灵锁魔阵的阵眼。",
    """
阵法核心 / 阵眼。

制作：""" + R(("暗影心房", 1), ("铥矿", 5), ("噩梦燃料", 10), ("紫宝石", 1), ("活木", 2), ("魔晶", 2)) + """。

用于驱灵锁魔阵：只拦生物不拦玩家，阵内外的敌对生物都被锁住。

可在 <灵界>、<魔法> 栏位制作。
""",
    recipe=R(("暗影心房", 1), ("铥矿", 5), ("噩梦燃料", 10), ("紫宝石", 1), ("活木", 2), ("魔晶", 2)),
)

item(
    "zhenfa", "lj_constant_temperature_nucleus", "恒温晶核", "阵法,阵眼,魔法",
    "极温庇护阵的阵眼。",
    """
阵法核心 / 阵眼。

制作：""" + R(("唤星法杖", 1), ("唤月法杖", 1), ("巨鹿眼球", 1), ("鳞片", 1), ("噩梦燃料", 10), ("魔晶", 2)) + """。

用于极温庇护阵：中和极端温度、抵消冰火伤害、缓慢恢复理智。

可在 <灵界>、<魔法> 栏位制作。
""",
    recipe=R(("唤星法杖", 1), ("唤月法杖", 1), ("巨鹿眼球", 1), ("鳞片", 1), ("噩梦燃料", 10), ("魔晶", 2)),
)

# ===========================================================================
# 卷目 9：灵植
# ===========================================================================
item(
    "lingzhi", "lj_reiki_grass", "融灵草", "灵植,材料",
    "多种丹药的基础药材。森林地皮蜘蛛巢与蝴蝶岛夜蝠巢穴附近生成。",
    """
生成（两批，地皮条件不同）
　主大陆：长在森林地皮的蜘蛛巢旁。
　蝴蝶岛：长在鸟粪 / 洞穴地皮上的夜蝠巢穴旁，每个巢穴 1 到 3 株。

采摘：可获得 草 1、融灵草 1；5% 概率额外获得 融灵草根 1。

生长周期同原版树枝，可催熟。
⚠️ 冬季不生长。

可烧毁、可挖掘，采集后会留下根部，类似原版草。

用途：几乎所有丹药的基础药材。
""",
)

item(
    "lingzhi", "lj_red_magic_flower", "龙爪花", "灵植,材料",
    "生长在前辈骨架旁，玩家死亡留下的骨架 1 天后也会长出来。",
    """
生成：前辈骨架旁，每个骨架只生成 1 朵。玩家死亡后留下的骨架会在 1 天后附近生长龙爪花。

采摘：可获得 花瓣 1、龙爪花 1；5% 概率额外获得 龙爪花根 1。

生长周期同原版树枝，可催熟。
⚠️ 冬季不生长（与融灵草一样）。

可烧毁、可挖掘，采集后会留下根部，类似原版草。

用途：不灭丹、合婴丹。
""",
)

item(
    "lingzhi", "lj_purple_magic_flower", "紫晶塑体花", "灵植,材料,Boss",
    "生长在曼德拉草原附近，每日在 4 格内生成一朵花；旁边必有月蚀晶翼狮守护。",
    """
生成：曼德拉草原附近，每个世界只会生成一朵。系统会记录这朵花有没有生成过：老存档进入世界后会补种一朵，花异常消失时也会补回来（生成状态会存档）。

特性：每日在自身 4 格范围内生成一朵花。

无法烧毁，需用斧头砍伐。旁边会存在月蚀晶翼狮。无法移植。
采集后 10 天重新生长。

狮王存在的情况下，紫晶塑体花无法被砍伐掉落。想采花就得先解决月蚀晶翼狮。
月狮死亡后紫花立刻可以采一次；月狮按 20 天独立计时重生（面板显示「月狮重生剩余」），月狮回来时紫花直接恢复。

用途：修复残骸祭坛。
""",
)

# ===========================================================================
# 卷目 10：墟火与异火
# ===========================================================================
item(
    "yihuo", "yihuo_rules", "火焰使用规则", "异火,墟火,机制",
    "火焰本体只能放在灵虚葫或虚空戒；放背包超过 10 秒会焚毁物品。",
    """
存放限制：墟火 / 异火本体只能正常放在灵虚葫、虚空戒中。分裂的火焰为单次消耗物品，无法堆叠。

焚毁危险：放在物品栏 / 背包里，每 10 秒随机焚毁 1 件可烧物品（世界唯一物品除外，异火本体也不会被烧）；如果那件是可堆叠的，一次只消耗 1 个。同一存储空间里放多个异火不会加速——代码里有 10 秒限流，多个异火只算一次。

照明与灭火：墟火 / 异火本体放置地上会提供 20 码范围照明，并熄灭周围所有普通火焰（异火之间不互相排斥，比如两个异火都放在地上，各自发光发热，还是会熄灭其他火焰）。分裂出来的放置地上会消失。

分裂：灵虚葫吸收的异火可右键分裂，消耗 10 灵力值。分裂的火焰可放入灵虚光盏提供光照，添加燃料 50%，燃烧可燃物、焚烧建筑，可以放入炼丹炉融合。

虚空戒点燃：戒内放有异火本体时，装备虚空戒右键目标即可远程点燃（火魔杖同款火球，射程 8 到 10），消耗 10 灵力值；对可燃燃料装置是补燃料，本身不造成伤害。

异火主人：刚掉落的强异火（冰霜业火、龙炎心火、狂鬃焰、灵煊尘火、紫鳞妖焰）是无主的，谁都徒手捡不起来，只能用灵虚葫吸收——吸收它的人（也就是葫芦的主人）成为它的主人；之后只有主人能徒手拾取。落地满 1 天（8 分钟）会变成「丢失主人」，此后任何灵虚葫都能吸收。墟火不属于强异火，任何人都能徒手拿。

吸收代价：使用灵虚葫吸收异火时火焰焚身——第一次会点燃你，之后每秒扣 2 点生命值，持续 60 秒；葫芦掉在地上会暂停，收回背包继续计时（剩余秒数会存档）。
""",
)

item(
    "yihuo", "lj_ordinary_flame", "墟火", "墟火,开局自带,火焰",
    "所有人物出生自带的火焰，存在于虚空戒中。",
    """
所有人物出生自带，存在于虚空戒中。

墟火是人物出生自带的火焰，可放入丹炉炼丹，也可分裂后用于灵虚光盏照明。

存放、照明、焚毁等通用规则见「火焰使用规则」。
""",
)

item(
    "yihuo", "lj_ice_flame", "冰霜业火", "异火,火焰,冰霜",
    "通过「冻僵的日志」线索召唤独眼巨鹿获得的异火，是制作灵韵的必需材料。",
    """
异火。线索 Boss 的入魔等级同样按世界天数抽取（见「入魔总览」），不受季节限制；线索物品 20 天一刷新（五种各自计时，详见「日志」）。

线索物品：「冻僵的日志」（桦树林随机刷新，需要用镐子敲碎解锁）。

获取流程：获取日志后右键打开，纸条记载着「月光下的巨影，踏碎冰面时，寒气中藏着跳动的光」。地面会随机生成一个大型可疑的土堆，翻找所有线索土堆，会生成独眼巨鹿。击杀会掉落正常掉落物，并额外掉落冰霜业火。

用途：制作灵韵需要冰霜业火本体。
""",
)

item(
    "yihuo", "lj_dragon_flame", "龙炎心火", "异火,火焰,火焰属性",
    "通过「焦黑鳞片」线索召唤龙蝇获得的异火，是制作星陨的必需材料。",
    """
异火。

线索物品：「焦黑鳞片」（岩浆池旁边刷新，需要用水壶浇灭）。

获取流程：获取日志后右键打开，纸条记载着「岩巢灵醒，有巨兽守其领地。其怒则焚尽草木，壳藏火核，骤击可破之。」宠物巢穴旁刷新龙蝇，击杀会掉落正常掉落物，并额外掉落龙炎心火。

用途：制作星陨需要龙炎心火本体。
""",
)

item(
    "yihuo", "lj_mighty_flame", "狂鬃焰", "异火,火焰,赋能",
    "通过「腐烂的背包」线索召唤熊獾获得的异火，可给防具赋能。",
    """
异火。

线索物品：「腐烂的背包」（森林地形随机刷新，需要用斧头劈开解锁）。

获取流程：获取日志后右键打开，纸条记载着「它推倒松树时，树根下会冒出火星，怕水却爱蜂蜜」。地图上会找一处蜂后巢穴，在它附近生成一个蜂箱，熊獾就在蜂箱旁边；击杀会掉落正常掉落物，并额外掉落狂鬃焰。

赋能效果
分裂的狂鬃焰：可给任意防具赋能，使此防具耐久度翻倍。
狂鬃焰本体：可给任何防具赋能，获得额外 15 免伤，并使此防具耐久度翻倍。

这个额外 15 免伤是在受到伤害的基础上防御。
举例：护甲初始防御 80，受到攻击 100，造成 20 点伤害，再吃 15 免伤，实际造成 17 点伤害。
""",
)

item(
    "yihuo", "lj_dust_flame", "灵煊尘火", "异火,火焰,灵技",
    "通过「风干的羽毛」线索召唤蚁狮获得的异火。",
    """
异火。

线索物品：「风干的羽毛」（绿洲附近拾取）。

获取流程：获取日志后右键打开，纸条记载着「沙暴中心有一道光晕，那是他的呼吸」。过去会看到蚁狮，击杀会掉落正常掉落物，并额外掉落灵煊尘火。

用途：放入虚空戒。
⚠️ 放入虚空戒目前不会解锁任何东西（灵技玩法开发中，敬请期待）。
""",
)

item(
    "yihuo", "lj_purplemonster_flame", "紫鳞妖焰", "异火,火焰,魂幡",
    "通过「泡胀的卷轴」线索召唤噬魂蛇获得的异火，可用于制作魂幡。",
    """
异火。

线索物品：「泡胀的卷轴」（沼泽触手旁随机刷新，需要火焰烘烤解锁）。

获取流程：获取日志后右键打开，纸条记载着「薄暮将至，灵脉水面会倒映出紫色火光」。查看日志后，Boss 会在黄昏时分出现在蝴蝶岛的池塘旁边。过去会看到噬魂蛇，击杀会掉落正常掉落物，并额外掉落紫鳞妖焰。

用途：可制作魂幡；给予魂幡可解锁技能「炼魂」。
""",
)

item(
    "yihuo", "lj_log", "日志", "异火,线索",
    "异火线索所用的日志。五种线索各自独立计时，拿到后满 20 个游戏日刷新下一件。",
    """
异火线索物品的统称。

线索 Boss 的入魔等级同样按世界天数抽取（见「入魔总览」），不受季节限制。

刷新规则
　五种线索各自独立计时，互不影响。
　从「拿到」那一刻起算：敲碎、劈开、浇灭、拾取、损毁都算拿到。
　满 20 个游戏日后刷新下一件（算上当天进度，是完整的 20 天）。
　同一时间世界上只会有一件同种线索；拿到手之后（哪怕放在背包里）也不会影响后续刷新计时。
　五种线索开局各自投放一件；境界只卡「阅读」（入微），不卡投放。

各类异火对应的具体线索物品：冻僵的日志、焦黑鳞片、腐烂的背包、风干的羽毛、泡胀的卷轴。
""",
)

item(
    "yihuo", "lj_frozen_log", "冻僵的日志", "线索,异火,冰霜业火",
    "桦树林随机刷新，需用镐子敲碎解锁。指向冰霜业火。",
    """
线索物品，指向冰霜业火。

位置：桦树林随机刷新。
解锁方式：需要用镐子敲碎。

弄开后变成「冰霜日志」——纸条内容与后续线索都写在日志条目里（见「冰霜日志」）。
""",
)

item(
    "yihuo", "lj_charred_scales", "焦黑鳞片", "线索,异火,龙炎心火",
    "岩浆池旁边刷新，需要用水壶浇灭解锁。指向龙炎心火。",
    """
线索物品，指向龙炎心火。

位置：岩浆池旁边刷新。
解锁方式：需要用水壶浇灭。

弄开后变成「龙炎日志」——纸条内容与后续线索都写在日志条目里（见「龙炎日志」）。
""",
)

item(
    "yihuo", "lj_rotten_backpack", "腐烂的背包", "线索,异火,狂鬃焰",
    "森林地形随机刷新，需要用斧头劈开解锁。指向狂鬃焰。",
    """
线索物品，指向狂鬃焰。

位置：森林地形随机刷新。
解锁方式：需要用斧头劈开。

弄开后变成「狂鬃日志」——纸条内容与后续线索都写在日志条目里（见「狂鬃日志」）。
""",
)

item(
    "yihuo", "lj_dried_camel_feathers", "风干的羽毛", "线索,异火,灵煊尘火",
    "绿洲附近拾取。指向灵煊尘火。",
    """
线索物品，指向灵煊尘火。

位置：绿洲附近拾取。

用途：炼丹炉材料，用于炼制「尘火日志」（高阶，炼制时间 2 分钟；见「尘火日志」）。纸条上的线索要在「尘火日志」里阅读。
""",
)

item(
    "yihuo", "lj_swollen_scroll", "泡胀的卷轴", "线索,异火,紫鳞妖焰",
    "沼泽触手旁随机刷新，需要火焰烘烤解锁。指向紫鳞妖焰。",
    """
线索物品，指向紫鳞妖焰。

位置：沼泽触手旁随机刷新。
解锁方式：需要火焰烘烤。

弄开后变成「紫鳞日志」——纸条内容与后续线索都写在日志条目里（见「紫鳞日志」）。
""",
)

# —— 5 本线索日志：读完线索物品后得到的可读物 ——
item(
    "yihuo", "lj_ice_log", "冰霜日志", "日志,异火线索",
    "从「冻僵的日志」得到的线索，指向独眼巨鹿。",
    """
对应异火：冰霜业火。
线索物品：冻僵的日志。
后续 Boss：独眼巨鹿。

纸条记载着「月光下的巨影，踏碎冰面时，寒气中藏着跳动的光」。随后地面会随机生成一个大型可疑的土堆，翻找所有线索土堆会生成独眼巨鹿。

阅读需要境界达到 入微。
""",
)

item(
    "yihuo", "lj_dragon_log", "龙炎日志", "日志,异火线索",
    "从「焦黑鳞片」得到的线索，指向龙蝇。",
    """
对应异火：龙炎心火。
线索物品：焦黑鳞片。
后续 Boss：龙蝇。

纸条记载着「岩巢灵醒，有巨兽守其领地。其怒则焚尽草木，壳藏火核，骤击可破之。」宠物巢穴旁会刷新龙蝇。

阅读需要境界达到 入微。
""",
)

item(
    "yihuo", "lj_mighty_log", "狂鬃日志", "日志,异火线索",
    "从「腐烂的背包」得到的线索，指向熊獾。",
    """
对应异火：狂鬃焰。
线索物品：腐烂的背包。
后续 Boss：熊獾。

纸条记载着「它推倒松树时，树根下会冒出火星，怕水却爱蜂蜜」。地图上会找一处蜂后巢穴，在它附近生成一个蜂箱，熊獾就在蜂箱旁边。

阅读需要境界达到 入微。
""",
)

item(
    "yihuo", "lj_dust_log", "尘火日志", "日志,异火线索",
    "指向蚁狮的日志；可以用炼丹炉直接炼制出来。",
    """
对应异火：灵煊尘火。
线索物品：风干的羽毛。
后续 Boss：蚁狮。

纸条记载着「沙暴中心有一道光晕，那是他的呼吸」。过去会看到蚁狮。

炼制（高阶，炼制时间 2 分钟）
""" + R(("仙人掌", 3), ("风干的羽毛", 1)) + """

阅读需要境界达到 入微。
""",
    recipe=R(("仙人掌", 3), ("风干的羽毛", 1)),
)

item(
    "yihuo", "lj_purplemonster_log", "紫鳞日志", "日志,异火线索",
    "从「泡胀的卷轴」得到的线索，指向噬魂蛇。",
    """
对应异火：紫鳞妖焰。
线索物品：泡胀的卷轴。
后续 Boss：噬魂蛇。

纸条记载着「薄暮将至，灵脉水面会倒映出紫色火光」。查看日志后，Boss 会在黄昏时分出现在蝴蝶岛的池塘旁边，过去会看到噬魂蛇。

阅读需要境界达到 入微。
""",
)

# ===========================================================================
# 卷目 11：地形与 Boss
# ===========================================================================
item(
    "ditu", "lj_remains_island", "残骸小岛", "地形,浅海,残骸,Boss",
    "浅海区的小地形，岛上生成远古残骸、炽岩蝎龙与一些矿石。",
    """
小地形，生成在浅海区。

岛上生成：
　远古残骸（修复后成为残骸祭坛，见「残骸祭坛」）。
　炽岩蝎龙（见「炽岩蝎龙」）。
　一些矿石。
""",
)

item(
    "ditu", "lj_remains_altar", "残骸祭坛", "建筑,特殊制作,科技站",
    "灵界专属科技站。修复后解锁高阶制作，每件都要在祭坛旁制作。",
    """
建造修复残骸：""" + R(("木板", 10), ("融灵草", 3), ("紫晶塑体花", 1), ("化石碎片", 3)) + """。
须至少辟谷境才可以修复；修复完成会下降一个大境界（损失九阶）——这是修复的代价，不是奖励。境界会保留原有的死亡锁定状态。

靠近解锁制作：每次制作都需要靠近残骸祭坛，不会因只做过一次就永久解锁配方。
灵韵、星陨、魂幡、骸龙甲、晶羽冠、四季核心、灵植核心、镇魔枢核、恒温晶核、玄阵枢纽、虚空戒。

科技站说明：残骸祭坛是灵界专属科技站。基础修炼设施用二本科技（炼金引擎）且永久解锁；
上面这些高阶配方必须在残骸祭坛旁制作。

修复完成的祭坛

[[图片:images/lingjie/showcase/lj_remains_altar_complete.png|修复后从破碎残骸变成完整的祭坛，高阶造物都在这里完成]]
""",
    recipe=R(("木板", 10), ("融灵草", 3), ("紫晶塑体花", 1), ("化石碎片", 3)),
)

item(
    "ditu", "lj_chiyan_scorpion_dragon", "炽岩蝎龙", "Boss,史诗,残骸祭坛",
    "残骸祭坛史诗级 Boss。血量 30000、护甲 30；不吃冰冻僵直击退，半场后召唤毒蝎幼虫。",
    """
生成在残骸祭坛（远古遗迹小岛）。史诗级 Boss。

基础属性
血量 30000，护甲 15，移速中等。

核心机制
不吃冰冻、僵直、击退效果；被催眠时昏睡 8 秒。
每损失 5000 点生命就召唤 4 只毒蝎幼虫（250 血，攻击 40，毒伤 3/秒，持续 8 秒），冷却 30 秒；回血不会让已经记过的阶段重复触发。毒蝎幼虫会一直存在，不死亡也不影响下一次技能召唤 4 只。

技能
横扫（普攻）：钳子挥击，每钳 60 伤，冷却 8 秒。攻击范围约 1 格（4 码，1 格 = 4 码）。攻击 4 下后尾巴横扫造成 90 点 AOE 范围伤害，并对玩家造成 2 格击退效果。

陨石崩击：召唤一个从天而降的陨石，飞速砸向玩家，类似陨石区的石头坠落（破坏建筑及树木，同原版陨石区）。冷却 18 秒。造成 120 点伤害，并击倒玩家（让玩家击飞摔倒的样子）。

沙砾喷发：身前 5 格锥形喷沙，持续 1.2 秒，冷却 20 秒。
　喷发持续释放时长 1.2 秒，身前 5 格锥形区域，宽 3 格，持续生成沙砾腐蚀地形，喷发结束后地形留存 2 秒。
　⚠️ 沙砾的减速与伤害来自原版沙刺本身。

蝎龙冲撞：蓄力 1 秒，直线冲锋 8 格，100 伤害 + 摧毁路径建筑，结束后眩晕 2 秒，冷却 30 秒。直线最大距离 8 格。
　建筑破坏：路径内所有木、石制墙体、采集物、小型建筑直接摧毁。

击杀掉落
蝎龙骨 1、怪物肉 4、魔晶 2、魔核 6、魔核碎片 10、橙宝石 2、绿宝石 2、黄宝石 2。
""",
)

item(
    "ditu", "lj_little_scorpion", "毒蝎幼虫", "Boss,召唤物,残骸祭坛",
    "炽岩蝎龙每掉 10000 血召唤 4 只。血量 250、攻击 40、附带毒伤。",
    """
由炽岩蝎龙每掉落 10000 血量时召唤 4 只。

血量 250，攻击 40，毒伤 3/秒，持续 8 秒。

毒蝎幼虫会一直存在，不死亡也不影响下一次技能召唤 4 只。
""",
)

item(
    "ditu", "lj_butterfly_island", "蝴蝶岛", "地形,季节,魔兽,魔兽森林",
    "分四个季节板块的地域，首版开放冬季板块；异火线索 Boss 与魔兽的聚集地。",
    """
搜索这个位置也可以用「魔兽森林」——标签里放了这个别名，两种叫法都能搜到。

进入后分为四个板块，对应四个季节（春夏秋冬）。首版冬季板块为全天数冬天，剩下三个板块一样会有季节效应，内容后续更新。（地域结界：上岛才可以感受地域季节）

冬季地域板块
核心区域（沼泽地皮）：有一个冰封沼泽池塘（线索 Boss 刷新处）；一棵完全正常的树，围着一些邪恶花；若干阴郁之棘；若干针刺树，若干尖刺灌木。
附属区域（鸟粪地皮）：在地域的边角地块，3 处夜蝠巢穴，每个巢穴旁随机生成 1 到 3 个融灵草。
原版冬季小内容：随机生成几处冰矿（敲了一些也会留存在一滩水，然后再慢慢生成冰矿），再有一处企鹅的地盘。

彩蛋
每个板块随机刷新前辈的骷髅，旁边会有陨落后留下的物品。
　1. 魔核 1 到 5 随机（几率 70%）
　2. 魔晶 1 到 2 随机（几率 30%）

夜蝠巢穴若干。

蝴蝶岛生成方式可在 mod 设置里调整：新旧世界 / 仅新世界 / 关闭。

指令代码：c_ljhd()　如果地图没有生成蝴蝶岛，可以用这个代码在自己脚下生成，注意找一个空一点的海域，因为会挤掉地形。
""",
)

item(
    "ditu", "lj_bat_nest", "夜蝠巢穴", "地形,蝴蝶岛,刷怪",
    "每个巢穴生成 6 只妖蝠与 1 只暗影血蝠，黄昏夜晚出没。",
    """
蝴蝶岛生成若干。每个巢穴生成 6 只妖蝠（5 分钟刷新 1 只，最多 6 只）、1 只暗影血蝠（45 分钟刷新 1 只，最多 1 只）。

黄昏夜晚出没（特性类似原版蝙蝠）。

每个巢穴旁随机生成 1 到 3 个融灵草。
""",
)

item(
    "ditu", "lj_demon_bat", "暗影血蝠", "魔兽,蝴蝶岛,蝙蝠,精英",
    "血量 2000 的精英魔兽。音波范围僵直，半血后不断召唤妖蝠。",
    """
初始血量 2000，移速中等。

攻击方式：撕咬 / 发射音波。
攻击伤害 55，1 格地皮内撕咬，超范围音波攻击。

音波攻击：释放暗红色音波，以自身为中心 半径 8 的范围攻击，每 0.5 秒一次脉冲，范围内持续僵直，持续 9 秒。走出范围即可解除。冷却 30 秒。

召唤机制：血量 50% 以后开始召唤 1 只妖蝠，冷却 15 秒，无上限。脱离战斗后都会回归巢穴；上限只有 6 只，多的进入巢穴后 = 死亡。

击杀固定掉落 血蝠精血 1、怪物肉 2（魔核碎片、魔核、魔晶根据当前入魔程度掉落）。

由夜蝠巢穴生成，每个巢穴 1 只，45 分钟刷新 1 只，最多 1 只。
""",
)

item(
    "ditu", "lj_blood_bat", "妖蝠", "魔兽,蝴蝶岛,蝙蝠",
    "小魔兽。血量 300、伤害 25，固定掉落怪物肉。",
    """
初始血量 300，攻击伤害 25，攻击周期 1 秒。

攻击方式：1 格地皮内撕咬，超范围冲刺攻击。冲刺击中会有短暂的僵直效果，可提前上下走动躲避。

击杀只固定掉落 怪物肉 1（魔核碎片、魔核、魔晶根据当前入魔程度掉落）。非大型魔兽生物。

由夜蝠巢穴生成，每个巢穴 6 只，5 分钟刷新 1 只，最多 6 只。
""",
)

item(
    "ditu", "lj_soul_devouring_snake", "噬魂蛇（隐藏 Boss）", "Boss,史诗,隐藏,蝴蝶岛",
    "血量 12000 的隐藏 Boss。每受 2000 伤掉鳞片，半血后会吞鳞回血 1000。",
    """
隐藏 Boss，史诗级。

基础属性
血量 12000，普攻撕咬 50 伤害，附加中毒效果，护甲 15%，移速中等。

核心机制
毒性免疫：噬魂蛇同类不会被它自己的毒液与毒沼影响（多个首领同时上场时不会互相中毒减速）。
每受 2000 血量伤害会掉落噬魂蛇鳞片，玩家无法拾取，可用异火烧毁。
噬魂蛇血量首次掉到 50% 后，会主动找寻吞食鳞片恢复自身血量，每个回复 1000 血量。

技能
撕咬：蛇头咬击，50 伤害，不可叠加，可重置中毒时间。
毒沼喷涌：朝目标喷射毒液生成毒沼，毒沼区域持续 4 分钟，区域内减速 60%，踩中附加中毒效果，冷却 15 秒。
定身石化：以自身为中心、半径 16 的圆形范围内，定身目标 3 秒，冷却 30 秒。（圆形范围，只对玩家生效）
剧毒禁锢：蛇尾猛砸向地面，生成一个影怪一样的蛇身缠住目标 5 秒，期间 Boss 会向禁锢目标靠近普攻。（只对玩家生效）

击杀掉落
噬魂蛇皮 3、怪物肉 5、魔晶 2、魔核 6、魔核碎片 10、红宝石 2、紫鳞妖焰 1。
""",
)

item(
    "ditu", "lj_moon_lion", "月蚀晶翼狮", "Boss,史诗,紫晶塑体花",
    "血量 24000 的史诗 Boss。靠附近花朵回血，靠近曼德拉草会昏睡。",
    """
生成在紫晶塑体花附近。史诗级 Boss。

基础属性
血量 24000，护甲 15%，移速中等。

核心机制
脱战回归：离开守护花所在范围后会停止追击并返回花旁，用一次狮吼作为过渡；追出 40 距离就彻底放弃。
周围 5 格地皮内有花朵的状态下，每朵每 10 秒恢复 60 血量（紫晶塑体花属于一个花单位，会跟花瓣一样生成蝴蝶）。
玩家摧毁、采集附近花朵会打断回血，10 秒内强制触发一次狮吼震慑（10 秒内采集花瓣，只会强制触发一次）。
靠近曼德拉草会陷入昏睡 8 秒，昏睡状态 1 分钟内只会触发一次（已种下的曼德拉草同样有效）。

技能（按顺序轮转：爪击 → 鳞粉飞弹 → 狮吼 → 裂地囚步；条件不满足或还在冷却的技能会跳过）
晶爪猛击：单体近战重击。伤害 70，冷却 5 秒，范围约 1 格（3 码），击倒小型生物，玩家受击硬直 0.6 秒。如果玩家距离小于 1 格，则 60% 概率左右手各挥一次、每下 70 伤（合计 140），40% 概率只挥一下。
鳞粉飞弹（远程消耗）：扇动单侧翅膀发射 3 枚蝶粉光球，呈三角散射。单发伤害 40，三发全中 120。爆炸半径约 0.4 格（1.5 码），爆炸后会在爆炸点生成一个花瓣。冷却 18 秒，最大飞行距离 10 格，遇障碍物直接爆炸。
狮吼震慑（控制技能）：全屏 6 格范围声波冲击。无伤害，但玩家僵直 1.2 秒，武器强制掉落地面。冷却 20 秒。
裂地囚步：狮子抬起单侧前爪，身躯下沉蓄力，地面轻微持续震动，脚下扬起细碎沙尘特效，屏幕小幅抖动提示玩家规避。
　生成范围：以自身 8 个地皮（32 单位）为中心，给范围内每名玩家在脚下各生成一个临时陷坑；坑与坑之间互不重叠，脚下不可通行的位置不生成。
　陷坑不摧毁建筑、地皮、墙体、作物，出现后先只露裂纹预警 1 秒。
　随后每秒推进一段塌陷，共 3 段：第 1 段与第 3 段各造成 60 点范围伤害，第 2 段只有特效。
　从第 2 秒起，每秒额外造成 1 点范围伤害；塌陷与伤害半径均为 2.5 单位（约 0.6 格）。
　第 3 段结束后陷坑立刻移除，总共存在约 3 秒（区别于蚁狮的永久塌陷坑）。
　⚠️ 陷坑只造成伤害，不造成减速。
　冷却 18 秒。

击杀掉落
紫晶壳 1、狮骨 1、怪物肉 4、魔晶 2、魔核 6、魔核碎片 10、红宝石 2、蓝宝石 2、紫宝石 2。
""",
)

# === CHUNK4 ===

# ===========================================================================
# 输出
# ===========================================================================
DATA = {
    "site": SITE,
    "sections": SECTIONS,
    "items": ITEMS,
    # 更新日志 = 游戏（mod）自己的版本更新记录，不是网站的施工记录。
    # 一条日志的「内容」用 ； 或换行可拆成多条：
    #   {"日志版本": "v0.2", "日期": "2026-XX-XX",
    #    "内容": "新增 XXX；修复 XXX；调整 XXX", "是否展示": "true"},
    "changelog": [
        {"日志版本": "v0.3", "日期": "2026-09-20",
         "内容":
             "新增「限时状态」面板（增益 / 负面分开、可拖动，跟随 HUD 缩放）\n"
             "玩家头像弹窗新增「灵界介绍页」入口\n"
             "祭天雷劫新增预警：落点 25 范围内提示 + HUD 倒计时\n"
             "丹劫：炼丹时 HUD 显示倒计时，死亡原因记为「丹劫天雷」\n"
             "入魔调整：中度护盾 25 → 5 秒、反弹 5% → 2%；深度护盾 25 → 12 秒、反弹 2% → 5%\n"
             "月蚀晶翼狮：技能改轮转、爪击冷却 8 → 5 秒、飞弹射程 8 → 10 格、已种曼德拉草生效、新增脱战回归\n"
             "噬魂蛇：石化与禁锢只对玩家生效；毒液与毒沼对同类无效\n"
             "荒界纳物箱：升级改为左键用材料，一次只消耗 1 份\n"
             "灵虚葫：异火焚身倒计时显示在 HUD，掉地暂停\n"
             "蝴蝶岛：地图缩小（陆地约原来一半），固定实体精简（夜蝠巢穴 4 → 3、正常的树 2 → 1）\n"
             "配方：清心丸粘液 3 → 1；入微丹犀牛角 → 暗影心房\n"
             "其它：灵韵弓箭矢调整、龙爪花计时持久化、异火线索提示文案调整\n"
             "版本号 0.1 → 0.3；补充服务器筛选标签\n",
         "英文内容":
             "Added the \"Timed Effects\" panel (buffs and negative effects shown separately, draggable, follows the HUD scale)\n"
             "The player avatar popup now has an \"Ethereal Realm Guide\" entry\n"
             "Sacrificial Tribulation now warns players within 25 of the landing spot, with a HUD countdown\n"
             "Alchemy Tribulation: HUD countdown while refining, and the death cause is now \"Alchemy Tribulation Lightning\"\n"
             "Demonization tuning: moderate shield 25 → 5s, reflection 5% → 2%; deep shield 25 → 12s, reflection 2% → 5%\n"
             "Eclipsed Crystalwing Lion: skills now rotate, claw cooldown 8 → 5s, missile range 8 → 10 turf, planted mandrakes take effect, and it now disengages and returns home\n"
             "Soul-devouring Snake: petrify and bind now affect players only; its venom and bog no longer affect its own kind\n"
             "Wild Realm Storage Box: upgrading now uses left-click with a material, consuming a single item\n"
             "Spirit Void Gourd: the Flame Backlash countdown now shows on the HUD and pauses when dropped\n"
             "Butterfly Island: smaller map (about half the land) with fewer fixed props (Night Bat Nests 4 → 3, ordinary trees 2 → 1)\n"
             "Recipes: Stillness Pill Glommer's Goop 3 → 1; Subtle Realm Pill Guardian's Horn → Shadow Atrium\n"
             "Also: Reiki Bow arrow tweaks, Dragon Claw Flower timer persistence, and new wording for the exotic flame clue hint\n"
             "Version 0.1 → 0.3; added server filter tags\n",
         "是否展示": "true"},
        {"日志版本": "v0.6", "日期": "2026-09-22",
         "内容":
             "版本号更新到 0.6\n"
             "彼岸花改名为龙爪花\n"
             "祭天雷劫重做：改为范围内随机落雷，不再只劈击杀者（随从、虚空戒等击杀也算）；普通深度入魔扣 10% 最大生命，史诗 Boss 必杀；第一轮预警立即出现\n"
             "炽岩蝎龙：护甲 30% → 15%；改为每损失 5000 点生命召唤一批幼虫；沙砾喷发 1.2 秒；被催眠昏睡 8 秒\n"
             "魂幡炼制时间 4 分钟\n"
             "血蝠精血的堆叠上限改为 20\n"
             "荒界纳物箱：不再限制同时开启的人数；整理时不会把多出来的堆叠物掉在地上\n"
             "灵虚葫：优化葫芦部署后的视觉逻辑\n"
             "驱灵锁魔阵：敌对生物出生在阵内会被立刻送到阵外最近的可站立位置\n"
             "境界经验：阿比盖尔的攻击与薇洛技能火焰的击杀，也算它们主人的参战\n"
             "紫晶塑体花：保证每个世界有一朵；老存档进世界会补种，花异常消失也会补回来\n"
             "入魔：深度入魔的魔气反弹单次最多 75 点；不会被入魔的名单加上海上的影怪\n"
             "优化视觉（祭天雷劫的落点预警图标）\n",
         "英文内容":
             "Version updated to 0.6\n"
             "Spider Lily renamed to Dragon Claw Flower\n"
             "Sacrificial Tribulation reworked: the strikes are now random within the area and no longer single out the killer (kills by followers or the Void Ring count too); an ordinary deeply demonized creature costs you 10% of your maximum health, while an epic boss kills outright, and the first warning appears right away\n"
             "Blazing Rock Scorpion Dragon: armour 30% → 15%; it now summons a batch of larvae every 5000 health it loses; its grit eruption lasts 1.2 seconds; it sleeps for 8 seconds when put to sleep\n"
             "Soul Banner refining time is 4 minutes\n"
             "Blood Bat Essence stack limit is now 20\n"
             "Wild Realm Storage Box: no longer limits how many players can open it at once; sorting no longer drops the extra items of an over-stacked pile on the ground\n"
             "Spirit Void Gourd: improved how the gourd looks right after it is deployed\n"
             "Demon-Locking Formation: hostile creatures that spawn inside are moved at once to the nearest valid spot outside\n"
             "Realm experience: Abigail's attacks and kills made by Willow's fire now count for their owner\n"
             "Amethyst Form Flower: every world is guaranteed one; an older save grows one when you enter it, and a flower that vanishes abnormally is put back\n"
             "Demonization: deep demonization's reflection now caps at 75 damage per hit, and ocean shadow creatures are added to the never-demonized list\n"
             "Visual polish (Sacrificial Tribulation landing marker icon)\n",
         "是否展示": "true"},
    ],
    "tele": [{"导向id": t[0], "字段": t[1], "说明": "", "是否展示": "true"} for t in TELE],
}


# 详情行首的说明性标签，例如「材料：」「制作：」「炼丹炉炼制：」
RECIPE_LABEL_RE = re.compile(r"^\s*[^：:\n]{1,22}[：:]\s*")


# ---------------------------------------------------------------------------
# 正文里的材料自动补图标
# ---------------------------------------------------------------------------
# R() 拼出来的配方行本来就带图标，但正文里**手写的清单**（击杀掉落、摧毁返还…）经常只有名字，
# 于是同一行里 mod 物品有图标（前台自动加）、原版材料没有，看着一高一低。
# 这里在生成 data.json 时就补上：名字紧挨着数量（`蝎龙骨 1` / `返还 2 木板` / `5 个木炭`）
# 才补图标，纯叙述里的名字不动；前面已经有图标的不重复补；
# 本身是 wiki 条目的名字跳过（前台会自动加链接和小图标，不用写死路径）。
_QUANTITY_AFTER = re.compile(r"^\s*\d")
_QUANTITY_BEFORE = re.compile(r"\d+\s*个?\s*$")
_ICON_BEFORE = re.compile(r"\]\s*$")


def material_name_re(extra_names=()):
    """材料名正则：**最长的名字优先**，并且把 wiki 条目名一起放进去。

    后者是为了「吃掉」更长的匹配：正文里的「融灵草 1」如果不放进去，
    就会在「融」后面匹配到短名「草」并插一个草图标，变成「融灵[图标] 草 1」。
    """
    names = sorted(
        set(MATERIAL_ICON) | set(MOD_MATERIAL_ID) | set(extra_names),
        key=len,
        reverse=True,
    )
    return re.compile("|".join(re.escape(n) for n in names))


def decorate_material_icons(text, rx, skip_names):
    """给正文里「名字 + 数量」形式的材料补上 [图标路径]，返回新文本。"""
    if not text:
        return text
    out = []
    last = 0
    for m in rx.finditer(text):
        name = m.group(0)
        if name in skip_names:
            continue
        before, after = text[: m.start()], text[m.end():]
        if _ICON_BEFORE.search(before):
            continue
        if not (_QUANTITY_AFTER.match(after) or _QUANTITY_BEFORE.search(before)):
            continue
        path = icon_path(icon_for(name))
        if not path:
            continue
        out.append(text[last:m.start()])
        out.append("[%s] " % path)
        last = m.start()
    if not out:
        return text
    out.append(text[last:])
    return "".join(out)



def strip_recipe_from_detail(detail, recipe):
    """详情里不要再重复一遍材料清单。

    「制作配方」字段已经带图标显示了一次材料，如果详情里再写一遍，
    点开卡片的弹窗里就会出现两份物品信息（用户反馈的问题）。
    """
    if not recipe:
        return detail
    out = []
    for line in detail.split("\n"):
        if recipe not in line:
            out.append(line)
            continue
        rest = line.replace(recipe, "", 1)
        rest = RECIPE_LABEL_RE.sub("", rest, count=1)
        rest = rest.strip().lstrip("，,、").strip()
        if rest in ("", "。", ".", "；", ";", "，", ","):
            continue
        out.append(rest)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    for _it in DATA["items"]:
        _it["详情"] = strip_recipe_from_detail(_it["详情"], _it["制作配方"])

    _wiki_names = {_it["名称"] for _it in DATA["items"] if _it.get("名称")}
    _material_rx = material_name_re(_wiki_names)
    for _it in DATA["items"]:
        _it["详情"] = decorate_material_icons(_it["详情"], _material_rx, _wiki_names)

    if WARNINGS:
        sys.stderr.write("警告 %d 条：\n" % len(WARNINGS))
        for w in sorted(set(WARNINGS)):
            sys.stderr.write("  - %s\n" % w)
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(DATA, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    sys.stdout.write("已生成 %s\n" % OUT_JSON)
    sys.stdout.write("  sections: %d\n" % len(SECTIONS))
    sys.stdout.write("  items   : %d\n" % len(ITEMS))
    sys.stdout.write("  tele    : %d\n" % len(TELE))
    by_sec = {}
    for it in ITEMS:
        by_sec[it["分类id"]] = by_sec.get(it["分类id"], 0) + 1
    for sec in SECTIONS:
        sid = sec["分类id"]
        sys.stdout.write("    %-10s %-8s %d 条\n" % (sid, sec["分类名"], by_sec.get(sid, 0)))


if __name__ == "__main__":
    main()
