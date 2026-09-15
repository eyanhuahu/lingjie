# 展示图

这里放**灵界 mod 物品的展示图**：从物品 `idle` 动画的第一帧导出的图，用于卡片预览。

## 来源与生成方式

动画在 mod 的 `anim/*.zip` 里（`anim.bin` + `build.bin` + `atlas-0.tex`），
这是饥荒编译过的动画格式，需要用 **DST Mod Tool**（`dst-app`）来渲染导出。

```bash
# ① 解出动画包并生成两份 Lua 脚本
python tools/extract_mod_showcase.py <mod的zip包>

# ② 先看配对结果（不写文件）
"<dst-app路径>" script --bypass --file .work/batch_dryrun.lua

# ③ 正式导出到本目录，文件名 = 物品预制体 id
"<dst-app路径>" script --bypass --file .work/batch_export.lua
```

导出参数：`max_dimension = 512`（最长边不超过 512 像素，保持透明背景）。

## 已知特例

| 物品 | 情况 |
| --- | --- |
| 17 种丹药 | 共用 `lj_pill` 的 `idle` 动画，靠 **符号覆盖** 区分：导出时带 `override_symbols = { swap_food = "<丹药 id>" }`，对应代码 `lj_pill.lua:142` 的 `OverrideSymbol("swap_food", "lj_pill", name)` |
| `lj_crystalcrown` | 动画名是 `anim`，不是 `idle` |
| `lj_cuiju_box` / `lj_huangjie_box` | 没有 `idle`，取 `closed`（关闭状态） |
| `lj_blood_bat` / `lj_demon_bat` | 飞行生物，没有 `idle`，取 `fly_loop_side` |
| 5 本线索日志 | 借用 `lj_log` 的 bank（同一个模型） |
| `lj_soul_devouring_snake` | 借用 `lj_three_headed_snake` 的 bank（模型名不同） |
| 蝴蝶岛 / 融灵草根 / 彼岸花根 | 没有动画，卡片沿用图标 |

目前共 78 张（61 个独立动画的物品 + 17 种丹药的符号覆盖图，**17 张丹药图内容各不相同**）。

## 与 `icons/` 的区别

| 目录 | 内容 | 用途 |
| --- | --- | --- |
| `../icons/` | 64×64 的物品图标（从图集切出） | **配方**里的材料图标 |
| 本目录 | 物品的 idle 第一帧（尺寸按原图） | **卡片预览图** |

卡片图优先用展示图，没有展示图的物品自动回退到图标。

素材版权归 mod 原作者，请勿用于其他用途。
