# 补充动画帧

这里放**不是物品卡片图、但用在卡片正文里的动画帧**：技能特效、状态徽章这类。
它们用 `[[图片:路径|说明]]` 独占一段插进 `data.json` 的 `详情` 里，
不会当作卡片预览图（卡片图只看 `images/lingjie/showcase/` 与 `images/lingjie/icons/`）。

| 文件 | 内容 | 来源（dst-app 导出） | 用在哪张卡 |
| --- | --- | --- | --- |
| `poison_swamp.png` | 毒沼喷涌特效 | `fx_poison_swamp_erupt` / `level4_loop_90s` 第 19 帧 | 噬魂蛇 |
| `moon_lion_missile.png` | 鳞粉飞弹的弹体 | `lj_moon_lion_fx` / `missile` 第 5 帧 | 月蚀晶翼狮 |
| `moon_lion_blast.png` | 鳞粉飞弹的爆炸特效 | `lj_moon_lion_fx` / `blast` 第 8 帧 | 月蚀晶翼狮 |
| `star_sword_charge.png` | 满充能时的剑身特效 | `swap_lj_star_sword` / `sword_charge4` 第 31 帧 | 星陨 |
| `star_sword_hit.png` | 星陨命中特效 | `fx_sword_hit` / `fx_sword_hit` 第 3 帧 | 星陨 |
| `realm_badge.png` | 游戏内的境界徽章 | `realm_value_ui` / `anim` 第 20 帧 | 境界体系 |
| `spirit_badge.png` | 游戏内的灵力徽章 | `spirit_value_ui` / `anim` 第 20 帧 | 灵力值 |

导出方式与展示图相同（`dst-app script`，**必须先断网**，见 `../showcase/README.md`），
再用 Pillow 裁掉透明边。挑选帧的办法：同一动画导出 25% / 50% / 75% 三帧，
取内容包围盒最大的那帧（特效峰值）。

## 导不出来的两个

| 想导的 | 为什么不行 |
| --- | --- |
| 打坐动作（`lj_meditate`） | 它挂在玩家的 `wilson` 骨架上，而 mod 里只有 `anim.bin`、没有玩家本体的 `build.bin`。单独导出时符号会**跨 build 串味**，渲染出「金冠 + 红身 + 石腿」的拼装怪 |
| 淬铁灵剑命中特效（`fx_lj_ordinary_sword_hit`） | 同样是 `AddOverrideBuild` 挂到玩家身上的特效，缺玩家 build，无法独立出图 |

另有两个动画（妖蝠音波 `lj_bat_sprint`、`flame_laser`）能导出，但抽出来的帧几乎全透明、
看不出形状，暂时没用。

素材版权归 mod 原作者，请勿用于其他用途。
