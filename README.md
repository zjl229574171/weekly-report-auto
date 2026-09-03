# 周报流程 · Git 仓库说明

本仓库是周报/月报流程文档的权威载体（Git 版），由 `git clone` 获取。数据（Sheet《微波周报数据》）与 PPT 产物（Slides 模板/母版）仍在腾讯文档，不在本仓库。

## 目录内容

| 文件 | 用途 |
|---|---|
| B_启动指引.md | AI 启动指引（启动协议 / 初始化协议 / 深文档索引）——**Git 权威** |
| C_周报总流程.md | 组员日常必读的周报流程规范——**Git 权威** |
| D_模板构建手册.md | 模板构建手册（**Git 权威**；云端自动化读腾讯文档，经 sync_de.py 同步） |
| E_月报生成手册.md | 月报生成手册（**Git 权威**；云端自动化读腾讯文档，经 sync_de.py 同步） |
| CODEBUDDY.md | 工作区入口（clone 后置于工作区根目录，AI 自动加载） |
| _weiyun_params.py | 微云上传 SHA1 参数计算脚本（已通过测试向量校验） |
| sync_de.py | D/E 同步脚本：仓库 md → 腾讯文档（读本地 manifest.json 的 D/E 链接，`python3 sync_de.py`） |
| manifest.json.template | manifest 占位模板（真实 manifest.json 由初始化时用「初始化文档」链接生成，不入仓库） |

## 安全边界

- **本仓库不含任何腾讯文档 URL**（可安全公开）。真实链接在「初始化文档」（机密，腾讯文档）与本地生成的 manifest.json 中。
- file_id / sheet_id 为内部标识符，保留在文档中供 AI 调用工具用。

## 版本与更新

- 版本权威：Sheet《微波周报数据》「流程版本」子表；`git tag` 作记录（当前 v0.6.0）。版本号三段式「发布.大修.小更」，进位规则见 B 文档「二A」
- 更新：AI 启动时读 Sheet「流程版本」↔ 本地 manifest.json version → 不同则 `git pull`（B 文档 1.2）
- 修改：发起人 `git add → git commit → git tag → git push` + 在 Sheet「流程版本」登记
- D/E 改动须同步腾讯文档（自动化执行依据）；详见 B 文档「二A、版本修改流程」

## 边界

- Sheet 数据、PPT 模板/母版永不本地化，实时读腾讯文档
- 仓库内只放流程文档与脚本，不产生运行临时文件
