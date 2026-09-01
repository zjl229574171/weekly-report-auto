# 周报流程 · AI启动指引（总入口）
文档性质：本文档是周报流程 AI 侧的唯一总入口。组员把本文档链接发给 AI 后，AI 按本文档执行启动协议与初始化协议，再按索引跳转深文档执行业务流程。
版本：5.10（版本历史与权威版本见 Sheet《微波周报数据》「流程版本」子表）
维护者：流程发起人（本文档 policy=2 只读，任何人不在此文档内直接编辑；要改流程请发起人在腾讯文档修改后同步版本号）
适用平台：WorkBuddy（需已连接「腾讯文档」与「微云」两个连接器，均为使用者本人账号授权）
## 〇、给 AI 的第一条指令（必读）
如果你（AI）正在读本文档，说明有人把本文档链接发给了你。请严格按以下顺序执行，不要跳步：
判定场景（首次初始化 / 版本检查）→ 见「一、启动协议」
需要初始化时 → 见「二、初始化协议」
初始化完成或无需更新后 → 读本地《C_周报总流程.md》→ 按用户请求执行业务流程
本文档只在启动时读；日常业务流程以本地《C_周报总流程.md》为准
触发词：用户未发本文档链接但说「记录工作 / 写周报 / 周报 / 月报 / 生成PPT」等时，同样按启动协议执行（工作区根目录 CODEBUDDY.md 会自动引导）；记录一律写入腾讯文档 Sheet《微波周报数据》「周报记录」，禁止创建本地 md 代替。
## 〇A、工具调用路径（新会话必读）
流程中的 slide_*/sheet_*/doc.*/manage.*/get_content/weiyun.* 都不在对话工具列表里，按下面路径调用：
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
| 用户发来本文档链接 + “初始化周报环境”（或类似表述） | 首次初始化 | → 走「二、初始化协议」全流程 |
| 工作区存在 周报流程/manifest.json（用户未贴本文档链接） | 已初始化 | → 读 周报流程/README.md 了解目录 → 走 1.2 版本检查 |
| 工作区不存在 周报流程/ 目录，但用户说”写周报” | 未初始化 | 提示用户：请把《周报流程·AI启动指引》链接发给我，说”初始化周报环境”（一次性操作，约 2 分钟） |
### 1.2 版本检查（已初始化时）
读 Sheet《微波周报数据》「流程版本」子表（见 3.2 资源清单），取当前权威版本号（一行数据，格式如 5.2，及”是否强制”标记）
读本地 周报流程/manifest.json 的 version 字段
按下表决策：
| 比对结果 | 动作 |
|---|---|
| 一致 | 静默通过，直接读本地《C_周报总流程.md》开工 |
| 版本不同（大小版本均适用） | 单轮询问：向用户一句话说明”检测到新版本（本地 x.x → 云端 y.y，更新说明：…）。是否更新？更新将清理 周报流程/ 目录下全部内容并重建。”用户答复更新 → 删除 周报流程/ 整目录 → 按初始化协议全量重建 → 一句话告知完成；用户答复不更新 → 继续用本地版本跑业务。只问这一轮，不再反复确认 |
| Sheet 读不到/网络失败 | 降级运行：以本地 manifest 版本继续业务，结束时提醒用户”本次未能联网核对流程版本” |
### 1.3 纪律
版本检查每次会话只做一次，不要在会话中途反复查询
更新时只动 周报流程/ 目录，绝不动 Sheet 任何数据，绝不清理工作区其他内容
产物归位：周报流程产生的所有本地文件（镜像、脚本、临时文件）一律放 周报流程/ 目录内，目录外零残留——保证清理 = 删除整个目录，无漏网之鱼
## 二、初始化协议（首次 / 强制更新时执行）
### 2.1 目标
在用户当前 WorkBuddy 工作区生成以下本地镜像（目录名固定 周报流程/）：
周报流程/
├─ README.md                 ← 本目录文件说明（不含流程内容与链接）
├─ manifest.json            ← 版本与来源记录
├─ B_启动指引.md             ← 本文档的语义逐字副本
├─ C_周报总流程.md           ← 深文档 C 的语义逐字副本
├─ D_模板构建手册.md         ← 深文档 D 的语义逐字副本（组员一般不用，但必须落盘）
├─ E_月报生成手册.md         ← 深文档 E 的语义逐字副本
└─ _weiyun_params.py        ← 从本文档附录提取的脚本
 
### 2.2 执行步骤
前置确认：确认用户已连接「腾讯文档」「微云」两个连接器；未连接则引导用户在 WorkBuddy 中连接（各自用自己的账号授权），连好后再继续
创建目录：在工作区创建 周报流程/（已存在则覆盖其中文件）
镜像四份指引文档（语义逐字）： 
用腾讯文档连接器依次读取本文档（B）及索引中 C、D、E 的全文
硬性要求：语义逐字——标题、条目、数值、代码一字不差，不重写、不总结、不增删任何标题与条目（这些文档是流程规范，一个字的偏差都可能导致执行错误）。排版格式跟随腾讯文档渲染形态即可；但标题层级（#）、表格结构（|）、章节编号、表格单元格内容、代码、链接必须与在线版一致（读取方法见下）读取方法（高保真镜像）：以 get_content 取正文作骨架；用 doc-mcp 的表格结构类工具重建 Markdown 表格（工具名以 tdoc_list doc-mcp 实际为准，常见如 list_tables / get_table_info）、代码块回填原位；标题按在线章节层级补 #（主标题 = #、章节 = ##、小节 = ###）；超链接只保留一次 URL（url 去重为 url）。

自检：在线 get_content 每一行非空文本必须在本地镜像中存在（HYPERLINK 渲染行除外），有缺失则重做

分别保存为 B_启动指引.md、C_周报总流程.md、D_模板构建手册.md、E_月报生成手册.md
自检：保存后核对每份文档的一级/二级标题与在线版一致；不一致则重新读取保存
生成 _weiyun_params.py： 
从本文档「四、附录」代码块中逐字提取代码，保存为 周报流程/_weiyun_params.py
自校验（必须执行）：创建测试文件（内容为 abc 三个字母，无换行），运行 python _weiyun_params.py <测试文件>，输出必须精确等于：
```
file_sha = a9993e364706816aba3e25717850c26c9cd0d89d
file_md5 = 900150983cd24fb0d6963f7d28e17f72
block_sha_list = ["a9993e364706816aba3e25717850c26c9cd0d89d"]
check_sha = 0123456789abcdeffedcba9876543210f0e1d2c3
check_data = YWJj
```
 
 （脚本以单行 JSON 输出，逐字段比对；`block_sha_list` 仅 1 个元素且等于 file_sha，因 3 字节只占 1 块）
任一字段不符 = 代码块在文档中被损坏（常见：缩进丢失）。此时禁止使用该副本，告知用户”文档中附录代码校验失败，请联系流程发起人修复文档”，初始化中止
校验通过后删除测试文件
写 manifest.json：
```
{
  "version": "<从「流程版本」子表读到的权威版本号>",
  "updated_at": "<本次初始化时间 ISO8601>",
  "source": {
    "B": "<本文档链接>",
    "C": "<C 文档链接>",
    "D": "<D 文档链接>",
    "E": "<E 文档链接>",
    "Sheet": "<《微波周报数据》链接>"
  }
}
```
 
生成 工作区根目录 CODEBUDDY.md（AI 会话入口，内容=本文档「四、附录」CODEBUDDY 模板逐字提取）；
生成 周报流程/README.md（目录文件说明，只介绍各文件含义用途，不写流程内容、不放链接——流程看各文档本身，链接看 manifest）：
```
# 周报流程 · 本地目录说明

本目录是周报流程的本地镜像，由 AI 按《AI启动指引》初始化协议生成。

| 文件 | 用途 |
|---|---|
| manifest.json | 版本号、初始化时间、各云端文档链接（版本检查与重建的依据） |
| B_启动指引.md | AI 启动指引副本（启动协议 / 初始化协议 / 深文档索引 / 附录代码） |
| C_周报总流程.md | 组员日常必读的周报流程规范副本（写周报前读它） |
| D_模板构建手册.md | 模板构建手册副本（发起人/自动化专用，组员一般不用） |
| E_月报生成手册.md | 月报生成手册副本（生成月报时读） |
| _weiyun_params.py | 微云上传 SHA1 参数计算脚本（传图时用，已通过测试向量校验） |

版本更新：按 B_启动指引.md 的版本检查流程执行；更新会清理本目录全部内容并重建。
```
 
收尾报告：向用户汇报——已生成哪些文件、版本号、自校验结果；然后读本地《C_周报总流程.md》，等待或直接执行用户请求的业务
### 2.3 边界（静态本地化，动态永远读云端）
| 内容 | 处理 |
|---|---|
| B/C/D/E 指引文档、_weiyun_params.py、README.md | 本地镜像（本协议） |
| Sheet《微波周报数据》所有子表（周报记录/项目词表/本周模板/花名册/流程版本） | 永不本地化，每次实时读云端 |
| 每周 PPT 模板、母版 | 永不本地化，从「本周模板」子表取动态 file_id 直连 |
### 2.4 幂等性
本协议可安全重复执行（用户换电脑、本地文件丢失、强制更新时重跑即可）。重跑即全量覆盖，无需 diff。
更新/重建执行纪律（禁止对本地镜像逐段 diff 编辑）：凡版本更新或本地镜像重建，一律执行「删除 周报流程/ 目录 → 按初始化协议全量重建」，禁止逐个 Edit 增量修改镜像文件。
原因（AI 必读）：
逐段 diff 每次修改都要「读云端+读本地+Edit」多次往返，token 开销反而高于一次全量重建；
diff 容易漏改某一处，导致本地镜像与云端不一致；而 AI 日常读的是本地镜像，漏改 = 悄悄沿用旧规则，是流程事故的最高风险来源；
全量重建保证镜像与云端绝对一致，且初始化协议自带标题自检兜底。
## 二A、版本修改流程（发起人 / 维护者用）
任何对 A/B/C/D/E 五份文档或附录代码的修改，按以下三步同步，一处不落：
云端登记：Sheet《微波周报数据》「流程版本」子表登记新版本号 + 是否强制 + 更新说明 + 时间。内容修正/增补说明 → 小版本 +0.1（如 5.6 → 5.7），是否强制=否；协议/列结构/不兼容改动 → 大版本 +1，是否强制=是。
云端同步：更新本文档（B）头部版本号，与 Sheet 一致；两处不一致时以 Sheet 为权威。
本地同步：本地镜像在 AI 下次会话启动时经「1.2 版本检查」检测到版本不一致 → 询问后按「二、初始化协议」全量重建（含四份 md 与 manifest.json 的 version 字段）；也可改完后立即让 AI 重建。
本文档头部版本号是唯一展示位，C/D/E 文档不再写版本号，仅指引到本处与 Sheet。
CODEBUDDY.md（工作区根目录）以本文档「四、附录」模板为唯一维护源：要改内容 → 改模板 + 升版本号 → 初始化重建；禁止手动改根目录文件（会被下次初始化覆盖）。
## 三、深文档索引
| 代号 | 文档 | 读者 | 何时读 |
|---|---|---|---|
| C | 《周报总流程》 | 组员日常必读 | 每次写周报前（读本地副本） |
| D | 《模板构建手册》 | 发起人 / 云端自动化专用（组员一般不使用；唯一例外：C 文档 Step④ 的”缺页兜底”已内联说明，组员无需读 D） | 建周模板时 |
| E | 《月报生成手册》 | 发起人 / 受指派者 | 生成月报时 |
在线链接（本地 manifest 为第一来源；此处为发起人维护用的副本）：
C 周报总流程：https://docs.qq.com/doc/DV0V5a1RMb3Fmcm1K
D 模板构建手册：https://docs.qq.com/doc/DV1p0Z0xIVERSU095
E 月报生成手册：https://docs.qq.com/doc/DV0pxbkxBaU94V0tz
Sheet《微波周报数据》：https://docs.qq.com/sheet/DV2NQWEJKcmRzYVdM
## 四、附录：微云上传参数脚本（完整代码 + 测试向量）
用途：微云分片上传所需的 SHA1 参数计算（file_sha / block_sha_list / check_sha / check_data）。纯 Python 标准库，无任何 token 依赖。 维护规则：本代码由发起人在本文档内维护，逐字级别精确。修改任何一行都必须升小版本号并在「流程版本」子表登记。 提取规则（给 AI）：从下方代码块逐字保存为 周报流程/_weiyun_params.py，并按 2.2 第 4 步完成测试向量校验。
```
import hashlib, base64, json, sys

BLOCK = 524288  # 512KB

class StreamSHA1:
    def __init__(self):
        self.h = [0x67452301,0xEFCDAB89,0x98BADCFE,0x10325476,0xC3D2E1F0]
        self.buf = b""
    def _rotl(self, x, n):
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF
    def _process(self, chunk):
        w = [0]*80
        for j in range(16):
            w[j] = int.from_bytes(chunk[j*4:j*4+4], "big")
        for j in range(16, 80):
            w[j] = self._rotl(w[j-3] ^ w[j-8] ^ w[j-14] ^ w[j-16], 1)
        a,b,c,d,e = self.h
        for j in range(80):
            if j < 20:   f = (b & c) | ((~b & 0xFFFFFFFF) & d); k = 0x5A827999
            elif j < 40: f = b ^ c ^ d; k = 0x6ED9EBA1
            elif j < 60: f = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDC
            else:        f = b ^ c ^ d; k = 0xCA62C1D6
            tmp = (self._rotl(a,5) + f + e + k + w[j]) & 0xFFFFFFFF
            e = d; d = c; c = self._rotl(b,30); b = a; a = tmp
        self.h = [(self.h[i] + v) & 0xFFFFFFFF for i, v in enumerate([a,b,c,d,e])]
    def update(self, data):
        self.buf += data
        while len(self.buf) >= 64:
            self._process(self.buf[:64])
            self.buf = self.buf[64:]
    def state_hex(self):
        return b"".join(h.to_bytes(4, "little") for h in self.h).hex()

def main(path):
    with open(path, "rb") as f:
        data = f.read()
    size = len(data)
    # file_sha + md5
    file_sha = hashlib.sha1(data).hexdigest()
    file_md5 = hashlib.md5(data).hexdigest()

    # streaming block_sha_list
    s = StreamSHA1()
    block_sha_list = []
    off = 0
    nblocks = (size + BLOCK - 1) // BLOCK
    for i in range(nblocks):
        chunk = data[off:off+BLOCK]
        is_last = (i == nblocks - 1)
        s.update(chunk)
        if is_last:
            # last block sha = standard file sha
            block_sha_list.append(file_sha)
        else:
            block_sha_list.append(s.state_hex())
        off += BLOCK

    # check_sha / check_data
    lastBlockSize = size % BLOCK
    if lastBlockSize == 0:
        lastBlockSize = BLOCK
    checkBlockSize = lastBlockSize % 128
    if checkBlockSize == 0:
        checkBlockSize = 128
    s2 = StreamSHA1()
    # process all non-last blocks
    off = 0
    for i in range(nblocks - 1):
        s2.update(data[off:off+BLOCK])
        off += BLOCK
    # process first (lastBlockSize - checkBlockSize) bytes of last block
    last = data[off:off+lastBlockSize]
    s2.update(last[:lastBlockSize - checkBlockSize])
    check_sha = s2.state_hex()
    check_data = base64.b64encode(last[lastBlockSize - checkBlockSize:]).decode()

    out = {
        "filename": path.split("/")[-1].split("\\")[-1],
        "file_size": size,
        "file_sha": file_sha,
        "file_md5": file_md5,
        "block_sha_list": block_sha_list,
        "check_sha": check_sha,
        "check_data": check_data,
    }
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main(sys.argv[1])
```
 
测试向量（内容为 abc、无换行的 3 字节文件）：
| 字段 | 期望值 |
|---|---|
| file_sha | a9993e364706816aba3e25717850c26c9cd0d89d |
| file_md5 | 900150983cd24fb0d6963f7d28e17f72 |
| file_size | 3 |
| block_sha_list | ["a9993e364706816aba3e25717850c26c9cd0d89d"]（单块 = file_sha） |
| check_sha | 0123456789abcdeffedcba9876543210f0e1d2c3 |
| check_data | YWJj（abc 的 base64） |
## 四A、附录：CODEBUDDY.md 模板
工作区根目录 CODEBUDDY.md 的内容模板（初始化协议生成；唯一维护源为本模板，见「二A」）。初始化时逐字提取保存为 工作区根目录/CODEBUDDY.md：
# CODEBUDDY.md — 工作区入口（AI 每次会话自动加载）
本工作区运行《微波周报》流程（周报 + 月报 + PPT 模板）。

## 触发词
用户提到以下意图时，先读流程文档再执行：
- "记录工作 / 写周报 / 周报 / 月报 / 生成PPT"
→ 先读 周报流程/B_启动指引.md 按启动协议执行（目录说明见 周报流程/README.md）

## 铁律
1. 数据一律写入腾讯文档 Sheet《微波周报数据》（「周报记录」子表），禁止用本地 md 文件代替
2. 工具调用路径见 B_启动指引.md「〇A、工具调用路径」节
3. 版本检查按 B_启动指引.md 1.2 执行；本文件由初始化协议生成，勿手动改
更新机制：改内容 → 改本模板 → 升版本号 → 初始化重建（见「二A、版本修改流程」）。
## 附：维护者备忘（发起人专用，组员忽略）
改任何流程文档（A/B/C/D/E）后：必须同步更新 Sheet「流程版本」子表的版本号（小版本 +0.1；不兼容改动升大版本并标记”强制”），并更新本文档头部版本号。两处不一致时以 Sheet 为准。
本文档发布到腾讯文档后：设 policy=2（只读），把 A/B/C/D/E 链接填入第三节索引与本文件头部。
本文档同时是本地镜像的源：本地 B_启动指引.md 与本文档内容应语义逐字一致（标题、条目、数值、代码一字不差；排版格式跟随腾讯文档渲染形态）。
项目资产中的同名 md 副本为快照存档（非权威），定期原名称覆盖即可，头部已注明。