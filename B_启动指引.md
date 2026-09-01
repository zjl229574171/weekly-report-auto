# 周报流程 · AI启动指引（总入口）
文档性质：本文档是周报流程 AI 侧的唯一总入口，存放于 Git 仓库（目录名 weekly-report-auto/，即本仓库工作副本）。AI 读本仓库内的本文档，按启动协议与初始化协议执行，再按索引跳转深文档执行业务流程。
版本：以 git tag 为准（当前 v5.10）；历史见 git log。腾讯文档备份版 B：https://docs.qq.com/doc/DV2pvR2xDV3pqUUNP（仅备份/参考，权威以本仓库为准）
维护者：流程发起人（改本文档 = 改仓库文件 → git commit / push；组员只读）
适用平台：WorkBuddy（需已连接「腾讯文档」与「微云」两个连接器，均为使用者本人账号授权）
## 〇、给 AI 的第一条指令（必读）
如果你（AI）正在读本文档，说明本 Git 仓库已就绪。请严格按以下顺序执行，不要跳步：
判定场景（首次初始化 / 版本检查）→ 见「一、启动协议」
需要初始化时 → 见「二、初始化协议」
初始化完成或无需更新后 → 读本地《C_周报总流程.md》→ 按用户请求执行业务流程
本文档只在启动时读；日常业务流程以本地《C_周报总流程.md》为准
触发词：用户说「记录工作 / 写周报 / 周报 / 月报 / 生成PPT」等时，同样按启动协议执行（工作区根目录 CODEBUDDY.md 会自动引导）；记录一律写入腾讯文档 Sheet《微波周报数据》「周报记录」，禁止创建本地 md 代替。
## 〇A、工具调用路径（新会话必读）
流程中的 slide_*/sheet_*/doc.*/manage.*/get_content/weiyun.* 都不在对话工具列表里，按下面路径调用（**仅数据层与 PPT 产物层需要**；流程文档读取走 git，不依赖本脚本）：
腾讯文档系列（PPT/表格/文档/文件）→ 走脚本：
python3 tencentdocs.py tdoc_call <service> <tool> '<json>'
service：slide-mcp(PPT) / sheet-mcp(表格) / doc-mcp(Word) / tencent-docs(文件管理)
★ 需要什么功能自己找：tdoc_list <service> 列全部工具、tdoc_schema <service> <tool> 查参数，先用后调
大参数：import tencentdocs as td; td.call_tool()
微云（weiyun.*）→ MCP 工具，真实名 mcp__tencent-weiyun__weiyun.*，先 ToolSearch 加载再调
项目自动化（automation_*）→ mcp__wb-issues__automation_*（ToolSearch 加载，组员一般不碰）
约束：参数按 tdoc_schema 传；URL 用 API 返回的 url 字段；大参数走 td.call_tool()。
云端自动化走 tdocs-app 连接器直接调同一批工具（AI 不执行，仅了解）。
## 一、启动协议（每次会话开始时执行）
### 1.1 场景判定
| 情况 | 判定 | 动作 |
|---|---|---|
| 本地无 weekly-report-auto/ 目录（首次） | 未初始化 | → 走「二、初始化协议」（git clone 仓库） |
| 本地有 weekly-report-auto/ 目录 | 已初始化 | → 读 README.md 了解目录 → 走 1.2 版本检查 |
| 无仓库地址且本地无目录 | 降级 | 提示用户：请提供 Git 仓库地址；若无远程仓库，可降级用腾讯文档备份（周报流程/ 目录）初始化，标注"只读备份模式" |
### 1.2 版本检查（已初始化时）
配置了远程仓库（git remote）→ 执行 git fetch，对比本地 HEAD 与 origin/HEAD（或 tag）：
| 比对结果 | 动作 |
|---|---|
| 本地 HEAD == 远程 HEAD | 静默通过，直接读本地《C_周报总流程.md》开工 |
| 本地落后远程 | 单轮询问：向用户一句话说明"检测到新版本（本地 <commit> → 远程 <commit>）。是否更新？"用户答复更新 → git pull → 一句话告知完成；不更新 → 继续用本地版本。只问这一轮 |
| 未配置远程仓库 | 以本地 git log 为准继续业务，结束时提醒用户"仓库未配置远程，无法自动更新" |
| git 命令失败/网络异常 | 降级运行：用本地仓库版本继续业务，结束时提醒"本次未能核对仓库更新" |
### 1.3 纪律
版本检查每次会话只做一次，不要在会话中途反复 git fetch
更新 = git pull，只动 weekly-report-auto/ 目录内文件；绝不动 Sheet 任何数据、绝不清理工作区其他内容
仓库纪律：weekly-report-auto/ 内只放流程文档与脚本（版本化内容）；Sheet 数据、PPT 产物、AI 运行时临时文件一律不写入仓库，临时文件放工作区仓库外
## 二、初始化协议（首次 / 重装时执行）
### 2.1 目标
git clone 流程仓库到工作区，得到全部流程文档与脚本（即权威即工作副本，目录名固定 weekly-report-auto/）：
weekly-report-auto/
├─ B_启动指引.md             ← 本文档
├─ C_周报总流程.md           ← 组员日常必读流程规范
├─ D_模板构建手册.md         ← 模板构建手册副本（权威在腾讯文档，自动化读；本副本仅本地参考）
├─ E_月报生成手册.md         ← 月报生成手册副本（权威在腾讯文档，自动化读；本副本仅本地参考）
├─ README.md                ← 目录说明
├─ CODEBUDDY.md             ← 工作区入口（clone 后置于工作区根目录，AI 自动加载）
├─ _weiyun_params.py        ← 微云上传 SHA1 参数计算脚本（已通过测试向量校验）
└─ manifest.json            ← 腾讯文档源链接记录（参考用，版本以 git 为准）
### 2.2 执行步骤
前置确认：确认用户已连接「腾讯文档」「微云」两个连接器；未连接则引导用户在 WorkBuddy 中连接（各自用自己的账号授权），连好后再继续
git clone <仓库地址> 到工作区 → 得到 weekly-report-auto/ 目录（若已存在则 git pull 更新）
自检（必须执行）：
- 文件齐全：B_启动指引.md / C_周报总流程.md / D_模板构建手册.md / E_月报生成手册.md / README.md / CODEBUDDY.md / _weiyun_params.py 均存在
- _weiyun_params.py 测试向量校验：创建测试文件（内容 abc、无换行），运行 python _weiyun_params.py <测试文件>，输出必须精确等于：
```
file_sha = a9993e364706816aba3e25717850c26c9cd0d89d
file_md5 = 900150983cd24fb0d6963f7d28e17f72
block_sha_list = ["a9993e364706816aba3e25717850c26c9cd0d89d"]
check_sha = 0123456789abcdeffedcba9876543210f0e1d2c3
check_data = YWJj
```
（任一字段不符 = 脚本被损坏，向用户报告，初始化中止）
- 校验通过后删除测试文件
CODEBUDDY.md 归位：确认工作区根目录有 CODEBUDDY.md（内容=仓库内 CODEBUDDY.md）
降级模式：无 git 环境或仓库不可达 → 从腾讯文档备份（周报流程/ 目录）镜像，标注"只读备份模式"，并提醒用户配置 Git 仓库地址
收尾报告：向用户汇报——已 clone/更新哪些文件、当前 git 版本、自校验结果；然后读本地《C_周报总流程.md》，等待或直接执行用户请求的业务
### 2.3 边界（静态本地化，动态永远读云端）
| 内容 | 处理 |
|---|---|
| B/C 流程文档、README、CODEBUDDY、_weiyun_params.py | Git 仓库（本协议） |
| D/E 手册 | 仓库存副本（本地参考）；**权威在腾讯文档**（云端自动化读腾讯文档） |
| Sheet《微波周报数据》所有子表（周报记录/项目词表/本周模板/花名册/流程版本） | 永不本地化，每次实时读云端 |
| 每周 PPT 模板、母版 | 永不本地化，从「本周模板」子表取动态 file_id 直连 |
### 2.4 幂等性
git clone / git pull 天然幂等，可安全重复执行（换电脑、本地丢失、重装时重跑即可）。更新一律用 git pull，禁止手动逐段编辑仓库文件（会破坏与远程的一致性）。
## 二A、版本修改流程（发起人 / 维护者用）
流程文档分两类，按对应流程修改，一处不落：
- **B/C/README/CODEBUDDY/_weiyun_params.py（Git 权威）**：改仓库文件 → git add → git commit → git tag（升版本，如 v5.11）→ git push（若有远程）。版本号 = git tag；不再依赖 Sheet「流程版本」（如需保留更新说明，可选登记）。
- **D/E（腾讯文档权威，云端自动化读取）**：改腾讯文档（D：DV1p0Z0xIVERSU095；E：DV0pxbkxBaU94V0tz）→ 同步更新仓库内 D/E 副本 → git commit 记录一致。**D/E 的任何改动必须同步腾讯文档，否则自动化执行的是旧规则。**
CODEBUDDY.md 位于仓库内（clone 后置于工作区根）：直接改仓库文件 → commit；禁止手工改工作区副本（会被 git pull 覆盖）。
## 三、深文档索引
| 代号 | 文档 | 权威载体 | 读者 | 何时读 |
|---|---|---|---|---|
| C | 《周报总流程》 | Git 仓库 | 组员日常必读 | 每次写周报前（读仓库内副本） |
| D | 《模板构建手册》 | 腾讯文档（自动化读） | 发起人 / 云端自动化 | 建周模板时（仓库副本仅参考） |
| E | 《月报生成手册》 | 腾讯文档（自动化读） | 发起人 / 受指派者 | 生成月报时（仓库副本仅参考） |
在线链接（发起人维护用）：
C 周报总流程：https://docs.qq.com/doc/DV0V5a1RMb3Fmcm1K
D 模板构建手册：https://docs.qq.com/doc/DV1p0Z0xIVERSU095
E 月报生成手册：https://docs.qq.com/doc/DV0pxbkxBaU94V0tz
Sheet《微波周报数据》：https://docs.qq.com/sheet/DV2NQWEJKcmRzYVdM
## 四、附录：微云上传参数脚本（测试向量）
脚本 _weiyun_params.py 以仓库文件为准（纯 Python 标准库）。测试向量（内容为 abc、无换行的 3 字节文件）供 2.2 自检：
| 字段 | 期望值 |
|---|---|
| file_sha | a9993e364706816aba3e25717850c26c9cd0d89d |
| file_md5 | 900150983cd24fb0d6963f7d28e17f72 |
| file_size | 3 |
| block_sha_list | ["a9993e364706816aba3e25717850c26c9cd0d89d"]（单块 = file_sha） |
| check_sha | 0123456789abcdeffedcba9876543210f0e1d2c3 |
| check_data | YWJj（abc 的 base64） |
## 四A、附录：CODEBUDDY.md 模板
CODEBUDDY.md 位于仓库根（clone 后置于工作区根目录，AI 每次会话自动加载）。模板即仓库内 CODEBUDDY.md 文件内容，维护方式见「二A」。
## 附：维护者备忘（发起人专用，组员忽略）
改 Git 权威文档（B/C/README/CODEBUDDY/脚本）→ git add/commit/tag/push；改 D/E → 腾讯文档优先 + 仓库副本同步 commit。
腾讯文档备份（周报流程/ 目录）只作存档，不参与权威版本；以 Git 仓库为唯一权威。
