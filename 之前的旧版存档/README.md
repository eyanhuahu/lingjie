# 旧版存档

这里是**改用 `data.json` 之前**的旧版内容文件，仅作存档，**网站已不再读取**。

| 文件 | 说明 |
| --- | --- |
| `content.xlsx` | 旧版内容表。当时网站用浏览器端手写的 xlsx 解析器现场解压读取它 |

改成 `data.json` 的原因：

- 二进制文件没法用 `git diff` 看清改了什么
- 每次打开网页都要现场解压 + 解析整个表格，内容多了会拖慢首屏
- 不好从 mod 代码批量生成

想看旧版的原始内容，直接用 Excel / WPS 打开这个 `content.xlsx` 即可。
需要回退到旧方案的话，得同时把 `site/app.js` 与 `site/js/sheetsContent.js` 回退到对应版本
（`site/js/sheetsContent.js` 里保留着 `loadContentWorkbook()`，代码本身还在）。
