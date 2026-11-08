---
name: lj-wiki-maintainer
description: 维护「灵界」DST mod 资料站（D:\Users\huan\Documents\GitHub\lingjie）。用于同步 mod 新版本、改卡片文案、改卷目顺序、修图片与字体、发布前校验。守住「代码为准、卡面只写现状、不许瞎编」这三条底线。
---

# 灵界 wiki 维护规程

站点：`index.html` + `site/styles.css` + `site/app.js` + `site/js/sheetsContent.js`，内容真相在 `tools/build_content.py`。

## 0. 三条底线

1. **代码为准**：卡片写的数值必须是打开 mod 源码读出来的，不是旧文档、不是记忆、不是推测。
2. **卡面只写现状**：卡片描述「现在是什么样」；哪版改了什么只进更新日志。
3. **不许瞎编**：没读过的文件不说它写了什么，没跑过的命令不说它输出了什么。不确定就说不确定，没验证就说没验证。

## 1. 数据源只有一个

```
tools/build_content.py  →  python tools/build_content.py  →  data.json  →  站点
```

- **只改 `build_content.py`**。手改 `data.json` 会在下一次构建时被覆盖（历史事故：「奶奶岛的垃圾堆」整张卡被冲掉）。
- `build_content.py` 现在会**先比对**现有 `data.json`：发现源码里没有的条目就报警，并列名/ID/分类、备份到 `.work/orphaned_items.json`。看到这个警告**先停下来**，把丢的条目补回源码再重建。
- `item(sec, iid, name, tags, summary, detail, recipe="", image="", visible=True, layout="")`
  - `layout="竖版"` → 卡片改成图在上、满宽、文字在下。
  - 英文写在文件开头的 `EN_CONTENT`（按 id 归档，缺翻译自动退回中文）。
- 卷目顺序在 `SECTIONS` 的「排序值」里定，改顺序只改数字。

## 2. 卡面写法

**要**：陈述规则与数值，一格一个事实，用「你」指玩家。
**不要**：

| 禁 | 例 |
|---|---|
| 口头话 | 「不用靠猜」「融不出东西」「一看就知道」 |
| 推测 | 「大概」「应该」「好像」 |
| 实现细节 / 内部代号 | 函数名、变量名、prefab id、文件路径、「沿用」「豁免」「原版引导动作」 |
| 版本标记 | 「本版新增」「不再…」「现在改成…」→ 这些只进更新日志 |
| Markdown 加粗 | `**` 会原样显示，用「」或分行表达重点 |
| 重复的「会」 | 「它会随机带哪种词条会显示…」 |

小节标题独立成行；正文用全角缩进「　」。详情里出现的**卡片名会自动变链接**，写到别的小节名/别名时必须在 `TELE` 登记。

## 3. 每次改完的验证链（一条都不能省）

```powershell
$env:PYTHONUTF8="1"
python tools/build_content.py        # 重建 + 丢失条目护栏
python tools/validate_content.py     # 无错误；会报 ** 误用、空卷目
node   tools/verify_site.js          # 没有失败项；查配方图标/正文插图/卡片图缺失
python tools/check_fonts.py          # 三款字体不缺字
```

任何一条不绿都不算改完。

## 4. 同步 mod 新版本（七步）

0. **归档基线**：把新包复制进 `.work/lj_mod_<日期>.zip`，下次才能 diff。`.rar` 用 `tar -xf` 解（Windows 自带 libarchive 能读）。
1. **列改动**：对比上一版 zip，按内部 mtime 找出新增/改动文件，报出「新增 N 个、改动 M 个、版本号」。
2. **逐文件读**：只读改动过的文件；语言表 diff 是最快拿到玩家可见文案的入口。**不要**读旧盘点文档当结论。
3. **跑对账**：`python tools/audit_mod.py`（缺省挑最新 `lj_mod*.zip`，也会扫 `.work/`）。查配方 23 条、原版材料名、材料英文名，并 dump 改动脚本里的数字常量供人工落卡。
4. **逐条落地**：每个新系统/新数值都要在卡片里有位置；新系统就开新卡。
5. **反向核对**：写进卡片的每个数字回源码再确认一次；名字用官方译名。
6. **跑 §3 四件套**（含 `audit_mod.py`）。
7. **出报告**：改了哪些卡、依据是什么、哪些**没验证**要说清楚。

## 5. 官方译名

- 中文名：游戏 `chinese_s.po`（在 `scripts.zip` 里，路径 `scripts/languages/chinese_s.po`）。**同一 msgid 可能重复**（皮肤名会撞物品名），取**第一条**。事故：「辣椒」被误改成「佩珀」。
- 英文名必须能在 `scripts/strings.lua` 的 `STRINGS.NAMES` 里找到。
- 不确定就写「待确认」，不要自己翻。

## 6. 跳转与图片

- **自动链接**：所有卡片名（含 `TELE` 别名）在正文里会自动变 `<a>`。
- **别名**：`TELE = [("目标id", "词1,词2")]`。写到卡里的小节名、招式名、别名都要在这里登记，否则点不动（事故：五个神通名在更新日志里不可点）。
- **卡片图**：`images/lingjie/showcase/<id>.png`（`图片` 字段）；没有则 `icon_path(id)`。
- **正文插图**：`[[图片:路径|说明]]`。
- **导出展示图**：`python tools/extract_mod_showcase.py <zip>` + `tools/run_dst_app.ps1 -LuaFile .work/batch_export.lua`（需要本机 DST）。

## 7. 字体

标题字体是**子集**，新卡标题出现新字就会缺字。

```powershell
python tools/check_fonts.py --print-text > .work/tmp.txt   # 注意：重定向写的是 UTF-16，不能直接用
```

正确做法：用 Python 以 UTF-8 写字符集，再

```powershell
python -m fontTools.subset ".work/font/NotoSerifSC-Black.otf" `
  --text-file=".work/font/chars.txt" --flavor=woff2 --no-hinting `
  --output-file="site/fonts/lingjie-titles-heavy.woff2"
```

源字体：`https://github.com/notofonts/noto-cjk/raw/main/Serif/OTF/SimplifiedChinese/NotoSerifCJKsc-Black.otf`（22.9 MB，放 `.work/font/`，不提交）。

## 8. 提交与发布

- **本地提交，不推送**。推送由作者自己做。每次报告结尾写清「待推送 N 个」。
- 提交信息格式：`内容：<一句话>`，正文写清改动与依据。
- 提交前先 `git log --oneline -3` + `git status` —— 可能有别的会话在改同一个仓库。
- 推送失败常见 `schannel: failed to receive handshake` / `Connection was reset` = 线路问题，不是代码问题；重试或换网络即可，**不要**改仓库。

## 9. 当前卷目顺序

```
0 人物 → 1 境界 → 2 五行灵根 → 3 生物入魔 → 4 墟火与异火 → 5 丹药与炼制
→ 6 精炼材料 → 7 建筑 → 8 武器与盔甲 → 9 法宝与工具 → 10 阵法灵技
→ 11 灵植 → 12 地形与Boss → 100 更新日志
```

## 10. 常用工具一览

| 工具 | 用途 |
|---|---|
| `tools/build_content.py` | 唯一内容源 → 生成 `data.json`（含丢失条目护栏） |
| `tools/validate_content.py` | 结构/文案校验（`**` 误用、空卷目、缺图） |
| `tools/verify_site.js` | 渲染校验（配方图标、正文插图、卡片图） |
| `tools/check_fonts.py` | 标题字体子集覆盖检查 |
| `tools/audit_mod.py` | mod ↔ wiki 对账（版本、配方、材料名、英文名、数字常量） |
| `tools/extract_mod_showcase.py` | 导出 mod 展示图（需本机 DST） |
| `tools/verify_cursor_fx.js` | 鼠标特效脚本自检 |

本地预览：`python -m http.server 8123 --bind 127.0.0.1 --directory .`，改完 `app.js`/`styles.css`/字体后必须 **Ctrl+F5**。
