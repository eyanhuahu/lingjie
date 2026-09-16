# 补充动画帧

这里放**不是物品卡片图、但在卡片正文里用到的动画帧**：技能特效、状态徽章这类。
它们用 `[[图片:路径|说明]]` 独占一段插进 `data.json` 的 `详情` 里；
徽章两张同时也当「境界体系」「灵力值」的**卡片预览图**（写在 `图片` 字段里）。

| 文件 | 内容 | 来源（dst-app 导出） | 用在哪张卡 |
| --- | --- | --- | --- |
| `poison_swamp.png` | 毒沼喷涌特效 | `fx_poison_swamp_erupt` / `level4_loop_90s` 第 19 帧 | 噬魂蛇 |
| `moon_lion_missile.png` | 鳞粉飞弹的弹体 | `lj_moon_lion_fx` / `missile` 第 5 帧 | 月蚀晶翼狮 |
| `moon_lion_blast.png` | 鳞粉飞弹的爆炸特效 | `lj_moon_lion_fx` / `blast` 第 8 帧 | 月蚀晶翼狮 |
| `star_sword_charge.png` | 满充能时的剑身特效 | `swap_lj_star_sword` / `sword_charge4` 第 31 帧 | 星陨 |
| `star_sword_hit.png` | 星陨命中特效 | `fx_sword_hit` / `fx_sword_hit` 第 3 帧 | 星陨 |
| `realm_badge.png` | 境界徽章（绿色打坐人形图标） | `realm_value_ui` / `anim` 第 1 帧，默认 `brain` 符号 | 境界体系 |
| `spirit_badge.png` | 灵力徽章（火焰 + 液面进度） | `spirit_value_ui` / `anim` 第 10 帧 | 灵力值 |

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
