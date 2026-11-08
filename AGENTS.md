# 灵界 wiki 维护规程

本仓库是「灵界」DST mod 的玩家向资料站。**完整规程见 [skills/lj-wiki-maintainer/SKILL.md](skills/lj-wiki-maintainer/SKILL.md)，动这个仓库前先读它。**

以下是每次都必须守住的硬约束。

## 三条底线

1. **代码为准** — 卡片里的数值必须来自 mod 源码，不能来自旧文档、记忆或推测。
2. **卡面只写现状** — 哪版改了什么只进「更新日志」，卡片正文不出现版本标记。
3. **不许瞎编** — 没读过的文件不说它写了什么，没跑过的命令不说它输出了什么；未验证的要明说未验证。

## 数据源只有一个

```
tools/build_content.py  →  python tools/build_content.py  →  data.json  →  站点
```

- **只改 `tools/build_content.py`。绝不手改 `data.json`** —— 它会在下一次构建时被覆盖（历史事故：「奶奶岛的垃圾堆」整张卡消失）。
- 构建前会比对现有 `data.json`：一旦发现源码里没有的条目就报警并备份到 `.work/orphaned_items.json`。看到警告先停手，把条目补回源码再重建。

## 卡面写法

- 只陈述规则与数值；用「你」指玩家。
- **禁**：口头话（「不用靠猜」「一看就知道」）、推测（「大概」「应该」）、实现细节与内部代号（函数名、prefab id、文件路径、「沿用」「豁免」）、版本标记（「本版新增」「不再…」）、Markdown `**`（会原样显示）、重复的「会」。
- 正文里提到的**卡片名会自动变链接**；写到某张卡里的小节名/别名时，必须登记到 `build_content.py` 的 `TELE` 表，否则点不动。

## 每次改完必须跑的四条校验

```powershell
$env:PYTHONUTF8="1"
python tools/build_content.py
python tools/validate_content.py
node   tools/verify_site.js
python tools/check_fonts.py
```

任一不绿都不算改完。同步 mod 新版本时再加 `python tools/audit_mod.py`。

## 同步 mod 新版本：七步

归档基线 → 列改动文件 → 逐文件读（语言表 diff 最快）→ 跑 `audit_mod.py` → 逐条落地到卡片 → 反向核对数字与名词 → 跑校验并出报告（含未验证项）。

## 官方译名

中文名以游戏 `chinese_s.po` 为准（**同一 msgid 可能重复，取第一条**）；英文名必须存在于 `scripts/strings.lua` 的 `STRINGS.NAMES`。查不到就写「待确认」，不要自己翻。

## 字体

标题字体是子集，新卡标题出现新字就会缺字；按 `check_fonts.py` 的提示重做子集（字符集要用 UTF-8 写，PowerShell `>` 重定向会写成 UTF-16）。

## 提交

- **只在本地提交，不推送**；推送由作者执行。每次报告结尾写清「待推送 N 个」。
- 提交前先看 `git log --oneline -3` 与 `git status`，确认没有别的会话在改同一仓库。
- 推送报 `schannel: failed to receive handshake` / `Connection was reset` 是线路问题，重试或换网络，不要改仓库。
