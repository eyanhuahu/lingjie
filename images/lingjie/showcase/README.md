# 展示图

这里放**灵界 mod 物品的展示图**：从物品 `idle` 动画的第一帧导出的图，用于卡片预览。

## 来源与生成方式

动画在 mod 的 `anim/*.zip` 里（`anim.bin` + `build.bin` + `atlas-0.tex`），
这是饥荒编译过的动画格式，需要用 **DST Mod Tool**（`dst-app`）来渲染导出。

> ⚠️ **跑之前先把工具断网。** dst-app 每次启动都会去 gitee 拉更新清单，
> 而它用的 reqwest 尊重标准代理环境变量，所以这样设置即可让它发不出任何外部请求：
>
> ```powershell
> $env:DST_UPDATE_MANIFEST_URL = "http://127.0.0.1:9/none.json"
> $env:HTTP_PROXY  = "http://127.0.0.1:9"
> $env:HTTPS_PROXY = "http://127.0.0.1:9"
> $env:ALL_PROXY   = "http://127.0.0.1:9"
> $env:NO_PROXY    = "127.0.0.1,localhost"
> ```
>
> （9 是 discard 端口，本地连接立刻被拒；`NO_PROXY` 保留本地地址以免影响它自己的 IPC。）
> 更彻底可以用管理员权限加防火墙出站规则。

```bash
# ① 找出动画包并生成两份 Lua 脚本（参数可以是 mod 目录，也可以是 mod 的 zip）
python tools/extract_mod_showcase.py <mod目录或zip>

# ② 先看配对结果（不写文件）：选了哪个动画、查出哪些幽灵符号
"<dst-app路径>" script --bypass --file .work/batch_dryrun.lua

# ③ 正式导出到本目录，文件名 = 物品预制体 id
"<dst-app路径>" script --bypass --file .work/batch_export.lua
```

导出参数：`max_dimension = 512`（最长边不超过 512 像素，保持透明背景）。

> ⚠️ **跑完记得检查残留进程。** `dst-app script` 打完一行 JSON 后**不会自己退出**，
> 它的常驻主实例还会继续活着（并会重建 `.work/` 里的输出文件）。收尾用：
>
> ```powershell
> Get-Process dst-app -ErrorAction SilentlyContinue | Stop-Process -Force
> ```

## 幽灵符号（导出踩过的坑）

dst-app 找符号是**跨 build 按名字解析**的：某个动画里引用了自己 build 里并不存在的符号时，
只要同一次导入的其它 build 里有同名符号，就会被画上去。两个实例：

- `lj_cuiju_box` 的 `closed` 帧里有一个遗留的 `swap_object` 元件 → 批量导入时从灵韵（弓）的
  build 解析出来，匣子图上**多画了一把弓**
- `lj_wudao_chair` 的 `idle` 帧同理 → 石台上**浮着一个蓝瓶子**（别处的 `swap_object`）

脚本因此会在导出前逐个检查帧内元件：**元素符号不在该条目自己的 build 里**时，把它所在的
Layer 加进 `hide_layers` 一起导出（丹药那种刻意用 `override_symbols` 替换的会被排除）。
dry-run 报告里的 `hide=` 一列就是被隐藏的 Layer，`build 未找到，跳过幽灵检查` 表示那条
无法判断（此时不会乱隐藏）。

还有一条更隐蔽的坑：**导入过的资源会留在 dst-app 的文档里，跨多次调用都不清空**。
所以做「只导某一个包」的隔离导出时，一定要先清空，否则上一个包还赖在文档里，
符号会被它抢走。清空用的 Lua：

```lua
tool:reset_workspace()   -- 命令会排队，脚本提交后执行
```

实例：境界徽章 `realm_value_ui` 与灵力徽章 `spirit_value_ui` 的符号名完全一样
（`bg`、`frame_circle`、`brain`…），不清空就连着导两次，两张图会渲染成**一模一样**
（详见 `../anim/README.md`）。

## 已知特例

| 物品 | 情况 |
| --- | --- |
| 17 种丹药 | 共用 `lj_pill` 的 `idle` 动画，靠 **符号覆盖** 区分：导出时带 `override_symbols = { swap_food = "<丹药 id>" }`，对应代码 `lj_pill.lua:142` 的 `OverrideSymbol("swap_food", "lj_pill", name)` |
| `lj_crystalcrown` | 动画名是 `anim`，不是 `idle` |
| `lj_chiyan_scorpion_dragon` | 该 bank **没有 `idle`**，只有 `idle_loop_side/upside/downside`；兜底会选到 `downside`（俯视角度，**头部被身体挡住看不见**），必须指定 `idle_loop_side` |
| `lj_cuiju_box` / `lj_huangjie_box` | 没有 `idle`，取 `closed`（关闭状态） |
| `lj_blood_bat` / `lj_demon_bat` | 飞行生物，没有 `idle`，取 `fly_loop_side` |
| 5 本线索日志 | 借用 `lj_log` 的 bank（同一个模型） |
| `lj_soul_devouring_snake` | 借用 `lj_three_headed_snake` 的 bank（模型名不同） |
| 蝴蝶岛 / 融灵草根 / 彼岸花根 | 没有动画，卡片沿用图标 |
| 炼丹炉 / 灵虚光盏 / 残骸祭坛 / 月狮 / 毒蝎幼虫 / 噬魂蛇 | 都没有精确的 `idle`，脚本兜底取该 bank 里第一个 `idle*`（dry-run 报告会标 `(fallback)`） |

目前共 78 张（61 个独立动画的物品 + 17 种丹药的符号覆盖图，**17 张丹药图内容各不相同**）。

## 与 `icons/` 的区别

| 目录 | 内容 | 用途 |
| --- | --- | --- |
| `../icons/` | 64×64 的物品图标（从图集切出） | **配方**里的材料图标 |
| 本目录 | 物品的 idle 第一帧（尺寸按原图） | **卡片预览图** |

卡片图优先用展示图，没有展示图的物品自动回退到图标。

素材版权归 mod 原作者，请勿用于其他用途。
