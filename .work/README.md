# dsh-persona-preset —— 把旧目录式 persona 迁移成 0.2.x 的 preset bundle

**目的**：让 `persona` 重新出现在 DSH 0.2.0 桌面版的 agent preset 名册里，
从而把被锁死在 `persona` 上的老会话 `session-c83b180c-ea8d-49e9-bb24-4f0da3f614e8` 恢复起来。

> 这个目录是**排查与迁移的产物**，不是 DSH 本体的一部分。
> 它放在 `lingjie` 仓库工作区的 `.work/` 下（沙箱只允许写工作区），
> `.work/` 目前未提交、也不在 `.gitignore` 里 —— 别 `git add .`。

---

## 1. 结论（为什么会 resume failed）

| 事实 | 证据 |
|---|---|
| 报错来自桌面应用内置引擎，不是 D 盘那份 CLI | `Unknown agent preset: ${wanted}` 只出现在 `DeepSeek Harness\resources\app.asar`（版本 **0.2.0-rc.2**，宿主协议 v4） |
| 老会话被锁在 `persona` | 会话日志第 4 条事件 `{"type":"agent-preset/selected","seq":3,"data":{"agentPreset":"persona"}}`；投影缓存 `session_projcache\...\session-c83b180c….json` 里 `agentPreset.val="persona"` |
| 0.2.0 不再扫 preset 目录 | 应用内 `dsh-agent-preset` 包文档原文：*"Before declaration rows, a user preset was a directory `$DSH_HOME/.agent-presets/<id>/` … **Nothing reads that directory any more.**"* |
| 0.2.0 的 preset 是「插件行声明」 | `@deepseek-ai/dsh-agent-preset-registry`：定义由插件行注册，`definitions` 是内存 Map，**既不扫目录也不接受 preset 路径** |
| 0.1.5 的 `persona` 目录本身没坏 | `D:\Users\huan\Documents\GitHub\deepseek\verify-preset.mjs` 实测：5 个 preset 全部被发现、0 broken、persona 文本 20 项断言全过 |

**一句话**：`persona` 是 0.1.x 的目录式 preset；桌面版升到 0.2.0-rc.2 后名册里只有内置的
`standard / ptc / minimal / cordis`，于是任何"我想用 persona"的请求（包括恢复一条锁定在
persona 的会话）都被宿主以 `agent-preset/not-found` 拒绝，网关再把它包成
`RemoteError: gateway/internal` 显示给陛下。

### 结果（2026-09-30 0:18，已复核）

| 验证点 | 结果 |
|---|---|
| 预设卡片 | 「加载失败」红框消失，只剩「自定义 / persona」 |
| 会话迁移 | `session-c83b180c…` 目录新增 `session.v4.jsonl.zstd`（9815024 字节，0:18:24），由 17.9 MB 的 v3 日志迁移而来 |
| 内容完整 | 迁移后 21381 条事件，末两条为 `turn/end`（第 264 轮 completed）与 `session/end-seed` |
| 身份保留 | header `agentPreset:"standard"` 之后，`agent-preset/selected` = **`persona`**（seq 3）—— 原样保留 |
| v3 原件 | 未改动，仍在同目录，可作备份 |

> 迁移出的 `.v4` 日志与 v3 并存是 0.2.0 的正常行为（读取优先走 v4）。

---

## 2. 安装（二选一）

### A. 图形界面（推荐，最省事）

侧边栏 **插件 / Plugins** 页面 → 安装本地 bundle → 目标目录填：

```
D:\Users\huan\Documents\GitHub\lingjie\.work\dsh-persona-preset
```

（绝对路径；页面会自己跑依赖安装并勾选该 bundle。）

### B. Creator 模式（创造模式）

新建一个**创造模式**会话，让那边的 agent 调用：

```
plugin_manager  action: install_bundle
                target: D:\Users\huan\Documents\GitHub\lingjie\.work\dsh-persona-preset
```

`install_bundle` 会自己完成依赖安装与 bundle 选择，**不要**用 shell 手动改 profile 的
`package.json` / `cordis.patch.yml`、也不要手动跑 pnpm。

> **改完 bundle 必须重启宿主。** 桌面 profile 的 `cordis.yml` 没有开 HMR
> （只有随附的 `web` 模板是 live reload），profile 层的改动在进程重启后才重新组合；
> 而且 `link:` 的 bundle 内容变化不触发清单事件。重启后本 bundle 会加载最新内容。

> `plugin_manager` 只有创造模式才有，且每次调用都需要**完全权限或一次审批**。

---

## 3. 验证

1. `plugin_manager` **list_plugins** → 应出现 `preset-persona` 行；再看激活状态：
   - 正常：已挂载（无 failed 诊断）
   - 若 `failed`：诊断文本会点名是哪一行插件装不上（见下面第 6 节）
2. 打开 **设置 → 通用 → agent preset**：名册里应多出
   「女王大人的小花花（代码大佬模式）」。
3. 重新打开 `session-c83b180c-ea8d-49e9-bb24-4f0da3f614e8`：应当能恢复，且性格是 persona。

**想让它继续当默认**：在同一个设置页把它设为默认，或 `plugin_manager` 的
`settings.update` 写 `agent-preset-registry` 命名空间的 `selectedDefault: persona`。

> 新装的 bundle 可能需要重启宿主才彻底生效（替换已安装包一定需要重启；首次安装常可走 HMR）。

---

## 4. 这个 bundle 是什么

> **2026-09-30 修订（take 2，重要）**：take 1 把旧 `agent.cordis.yml` 的 0.1.5 行逐行搬过来，
> 只补了 0.2.0 新增的两行。结果界面上这张卡片显示 **「加载失败」/ 自定义 / persona** ——
> 说明 bundle 装上了、声明也注册了，但**激活失败**（`diagnostic` 有内容）。
>
> take 2 改为：**插件列表逐行照抄随发行版交付的 0.2.0 `standard` 预设**（它在本部署里已证明
> 能挂载），只把 `persona` 那一行的 `config`（性格正文）替换成旧 preset 的。
> 复核结果：32 个 id 全唯一、`plugin list matches shipped standard row-for-row`、
> persona 正文与 `{{model}}`/`{{cwd}}` 完好、所有引用在宿主清单里可解析。
> take 1 的产物保留为 `cordis.patch.attempt1.yml.bak`，仅供对比，不会被加载。

```
dsh-persona-preset/
├── package.json                      # 声明 dsh.bundle.patch = ./cordis.patch.yml
├── cordis.patch.yml                  # 一条 insert：@deepseek-ai/dsh-agent-preset 声明，id = persona
└── cordis.patch.attempt1.yml.bak     # take 1 的产物（对比用，不加载）
```

声明内容 = 旧 `preset.yml` 的 `name/description/order` + **0.2.0 `standard` 的插件行**，
唯一差异是 `persona` 行的 `config.prefix`（您那份性格正文）；`suffix` 与 standard 相同。

| 与 take 1 的差别 | 原因 |
|---|---|
| 不再使用旧 preset 的 20 行列表 | 那是 0.1.5 时代的组合；其中 realm 的 `isolate` 集合、`workflow-ptc` 的配置等若与 0.2.0 不符，会导致**整份 preset**激活失败（正是卡片上那个「加载失败」） |
| `workflow-ptc` 不再 `disabled`，`tool-ralph` 恢复 `disabled: true`，补齐 `present` 等行 | 完全跟随 standard 的实际形态 |
| 去掉我先前擅自加的 `tool-presentation` / `tool-plugin-manager` 行 | 与 standard 逐行一致；少即是安全 |

---

## 5. 回退

1. 插件页里移除该 bundle，或 `plugin_manager` `remove_bundle`（包名
   `@local/dsh-preset-persona`），然后重启宿主。
2. 旧的目录式 preset **没有被这个迁移动过**，仍在
   `D:\aideepseek\data\.agent-presets\persona\`，可作为原始备份永久保留 —— 它现在不再被读取，
   删不删都不影响运行。

---

## 6. 如果激活失败

`list_plugins` 的 `failed` 诊断会点名具体行。最可能的两种情况：

- **某行包名在 0.2.0 里不存在** → 报告里会给包名；按 `cordis-composition-reference`
  换成新名，或把该行 `disabled: true`，重装同一个 bundle（不要新建重复 bundle）。
- **`agent-preset/locked`**：会话已经跑过第一轮就不能换 preset。恢复老会话不属于这种情况
  （它记录的就是 persona），但**别指望给新会话中途换性格**。

---

## 7. 附带的脚本（可选，不影响安装）

| 脚本 | 作用 |
|---|---|
| `migrate-persona-preset-v2.mjs` | **当前迁移的执行体**：从 app.asar 里取出随发行版交付的 `standard` 预设，换掉 `persona` 行的 config，生成 bundle，并把两边的行签名逐个对比（输出 `row-shape diffs: none`） |
| `check-persona-bundle-v2.mjs` | **当前复核脚本**：按 Loader 的方式解析 patch，断言根是列表、声明 id、行 id 唯一、2 个平台 `!!js` 仍是表达式、插件列表与 standard 逐行一致、所有引用可解析、persona 正文完好 |
| `migrate-persona-preset.mjs` / `check-persona-bundle.mjs` | take 1 的版本，保留作记录（它的断言针对“旧行搬运”方案，现在会 FAIL，属预期） |
| `scan-session-events.mjs` / `read-asar-lines.mjs` | 排查用：解压会话日志按时间筛事件、按行号读 app.asar（UTF-8 安全） |

脚本都只读旧 preset 与 app.asar，只写 `.work/`。
