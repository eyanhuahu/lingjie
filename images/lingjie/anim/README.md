# 补充动画帧

这里放**不是物品卡片图、但在卡片正文里用到的动画帧**：技能特效、状态徽章这类。
它们用 `[[图片:路径|说明]]` 独占一段插进 `data.json` 的 `详情` 里；
徽章两张同时也当「境界体系」「灵力值」的**卡片预览图**（写在 `图片` 字段里）。

| 文件 | 内容 | 来源（dst-app 导出） | 用在哪张卡 |
| --- | --- | --- | --- |
| `star_sword_charge.png` | 满充能时的剑身特效 | `swap_lj_star_sword` / `sword_charge4` 第 31 帧 | 星陨 |
| `star_sword_hit.png` | 星陨命中特效 | `fx_sword_hit` / `fx_sword_hit` 第 3 帧 | 星陨 |
| `realm_badge.png` | 境界徽章（深蓝打坐人形图标） | `realm_value_ui` / `anim` 第 1 帧，默认 `brain` 符号 | 境界体系（兼卡片图）|
| `spirit_badge.png` | 灵力徽章（火焰 + 液面进度） | `spirit_value_ui` / `anim` 第 10 帧 | 灵力值（兼卡片图）|
| `huangjie_box_ui.png` | 荒界纳物箱的箱子界面（上方 3×11、下方 1×10 的架子 **+ 5 个按钮**） | `lj_huangjie_box_ui` / `open` 最后一帧，再用 `tools/compose_box_ui.py` 把按钮合成上去 | 荒界纳物箱 |
| `cuiju_box_ui.png` | 聚气淬具匣的面板界面（7×7 格 + 上方展示格） | `lj_cuiju_box_ui_7x7` / `open` 最后一帧 | 聚气淬具匣 |

> 纳物箱那张为什么要合成按钮：按钮在游戏里是**独立的 UI 贴图**（来自
> `images/ethereal_realm_ui` 图集，用 `tools/extract_mod_icons.py` 切出来），
> 不属于箱体的动画帧，单导出的箱体图上是没有按钮的。
>
> ⚠️ **坐标要按「上沿对齐」算，不是按中心**：
> `containers.lua` 里 `HUANGJIE_BUTTONS.pos` 是**容器控件坐标系**的坐标。
> 正确映射是 **导出的面板 PNG 上沿对应 `pos.y`、水平居中对应 `pos.x`**：
> `X = 面板宽/2 + 控件x`、`Y = pos.y − 控件y`。
> 反推依据：按这个映射，4 行槽位落在图上 y = 95 / 175 / 255 / 340，
> 跟箱子图上三层架子的实际位置（≈100 / 180 / 255）完全对得上 —— 槽位必须摆在架子上。
> 之前按「面板中心 = pos」算过一版，结果两个按钮飘到箱子外面（用户指正过两次）。
> 有按钮会压在面板上沿之外（游戏里不裁剪），所以画布会自动向外扩到刚好包住全部内容。
> **唯一一处手工微调**：「封」源码坐标 (400,-85) 按映射算会压在箱子右沿外面，
> 用户要求「不许露出来」，所以改成 (372,-150)（往下、往里）。
> 脚本：`tools/compose_box_ui.py`。

> 两张 UI 图是**例外**：它们天生就大（957×578 与 809×765），上面那条「长边 ≤200px」的规矩
> 只管技能特效那类，容器界面本来就是要看清格子的，详情里会自动缩到栏宽显示。
> 另外这两个包的 `close` 动画导出来是 **1×1 空图**（关闭帧没有可见元件），别导错。

> 尺寸：正文插图**长边一律不超过 200px**。技能特效那种按原尺寸导出会有 400px 高，
> 在详情里显得又大又占地方（试过毒沼喷涌 / 鳞粉飞弹弹体 / 爆炸特效三张，
> 又大又没多大意义，已经删掉了）。

> ⚠️ **两个徽章的源素材本来就小**：`realm_badge` 135×115、`spirit_badge` 90×115
> （mod 的 UI 图集就这么大；dst-app 的 `max_dimension` 只是**上限、不会放大**）。
> 所以卡片图区（172px 高）里不能用 `object-fit` 拉满，否则放大 1.5 倍发虚 ——
> `styles.css` 里有一条 `.card-media img[src*="badge"]` 把它们限制在 118px 高并居中，
> 等于按原始像素显示。想更清晰只能让作者把游戏里的徽章素材画大，没有别的办法。

## ⚠️ 两个徽章**必须各自单独导入**

这几个包里的符号名是**一样**的（`bg`、`frame_circle`、`brain`…），而 dst-app 是**跨 build 按名字
找符号**的。更要命的是：**导入过的资源会在多次调用之间留在文档里**。所以如果先导了灵力、
再导境界，两张图会从同一个图集取图 —— 结果就是两个徽章**渲染成完全一样**（踩过这个坑）。

正确做法是每个包单独跑一次，跑之前先清空文档：

```lua
-- reset.lua：清空工作区（命令排队到脚本提交后执行）
tool:reset_workspace()
```

```powershell
<dst-app> script --bypass --file .work/reset.lua          # 先清空
<dst-app> script --bypass --file .work/badge_realm.lua    # 只导入 realm_value_ui.zip
<dst-app> script --bypass --file .work/reset.lua          # 再清空
<dst-app> script --bypass --file .work/badge_spirit.lua   # 只导入 spirit_value_ui.zip
```

另外：徽章中间那个图标在游戏里是**按境界换的**
（`lj_realm_value_badge.lua:20` `OverrideSymbol("brain", "realm_value_ui", "number"..major)`，
凡境用默认 `brain`、淬体以上显示数字），所以想导别的境界可以加覆盖：
`{ override_symbols = { brain = "number3" } }`。

## 导不出来的两个

| 想导的 | 为什么不行 |
| --- | --- |
| 打坐动作（`lj_meditate`） | 它挂在玩家的 `wilson` 骨架上，而 mod 里只有 `anim.bin`、没有玩家本体的 `build.bin`。单独导出时符号会**跨 build 串味**，渲染出「金冠 + 红身 + 石腿」的拼装怪 |
| 淬铁灵剑命中特效（`fx_lj_ordinary_sword_hit`） | 同样是 `AddOverrideBuild` 挂到玩家身上的特效，缺玩家 build，无法独立出图 |

另有两个动画（妖蝠音波 `lj_bat_sprint`、`flame_laser`）能导出，但抽出来的帧几乎全透明、
看不出形状，暂时没用。

素材版权归 mod 原作者，请勿用于其他用途。
