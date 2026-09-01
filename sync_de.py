#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_de.py — D/E 手册同步脚本（Git 仓库权威 → 腾讯文档自动化权威）

用途：D/E 的权威在 Git 仓库（本目录）。云端自动化（6553649 读 D、6750800 读 E）
在云端运行、无 git，只能读腾讯文档。改完仓库内 D_模板构建手册.md / E_月报生成手册.md 后，
运行本脚本把内容推送到腾讯文档对应 file_id（file_id 从本地 manifest.json 读取，
manifest.json 由「初始化文档」生成、.gitignore 排除，不进仓库）。

用法：
    python3 sync_de.py          # 同步 D 和 E
    python3 sync_de.py D        # 只同步 D
    python3 sync_de.py E        # 只同步 E
    python3 sync_de.py --check  # 只读检查（列出 manifest 里 D/E 的 file_id，不推送）

依赖：本机 WorkBuddy 内置 Python 3.13 + tencentdocs.py（标准库，自动定位）；腾讯文档连接器已连接。
"""

import sys
import os
import json
import re
import glob
import base64

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(REPO_DIR, "manifest.json")

DOCS = {
    "D": {
        "md": "D_模板构建手册.md",
        "manifest_key": "D",
        "title": "模板构建手册",
    },
    "E": {
        "md": "E_月报生成手册.md",
        "manifest_key": "E",
        "title": "月报生成手册",
    },
}


def find_tencentdocs_py():
    """定位 tencentdocs.py（WorkBuddy 插件缓存目录，跨机器通用）。"""
    home = os.path.expanduser("~")
    patterns = [
        os.path.join(home, ".workbuddy", "plugins", "cache", "workbuddy-builtin",
                     "tencent-docs-plugin", "*", "skills", "tencent-docs", "tencentdocs.py"),
    ]
    for pat in patterns:
        hits = glob.glob(pat)
        if hits:
            return hits[0]
    return None


def load_manifest():
    if not os.path.exists(MANIFEST):
        print("[FAIL] 未找到 manifest.json。请先按「初始化文档」完成初始化（git clone + 配置 manifest.json）。")
        sys.exit(1)
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def extract_file_id(url):
    """从腾讯文档 URL 提取 file_id（doc URL 末尾段即 file_id）。"""
    if not url:
        return None
    return url.rstrip("/").split("/")[-1]


def md_to_html(md_text):
    """把镜像 md 转成腾讯文档 overwrite_doc_with_html 接受的 HTML（基础转换）。"""
    lines = md_text.split("\n")
    html = []
    i = 0
    in_table = False
    table_rows = []
    in_code = False
    code_lines = []

    def flush_table():
        nonlocal table_rows, in_table
        if not table_rows:
            return
        # table_rows[0] = 表头, table_rows[1] = 分隔行, 之后为数据
        header = table_rows[0]
        body = table_rows[2:]
        cells = lambda row: [c.strip() for c in row.strip().strip("|").split("|")]
        out = ["<table>", "<tr>"]
        for c in cells(header):
            out.append("<td><b>{}</b></td>".format(_esc(c)))
        out.append("</tr>")
        for row in body:
            out.append("<tr>")
            for c in cells(row):
                out.append("<td>{}</td>".format(_esc(c)))
            out.append("</tr>")
        out.append("</table>")
        html.append("".join(out))
        table_rows = []
        in_table = False

    def flush_code():
        nonlocal code_lines, in_code
        if code_lines:
            html.append("<pre>{}</pre>".format(_esc("\n".join(code_lines))))
            code_lines = []
            in_code = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 代码块
        if stripped.startswith("```"):
            if in_code:
                flush_code()
            else:
                in_table and flush_table()
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue

        # 表格行
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_rows.append(line)
            i += 1
            continue
        if in_table:
            flush_table()
            # 不 i+=1，让当前行继续按普通逻辑处理

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            html.append("<h{0}>{1}</h{0}>".format(level, _inline(m.group(2))))
            i += 1
            continue

        # 引用
        if stripped.startswith(">"):
            html.append("<blockquote>{}</blockquote>".format(_inline(stripped.lstrip(">").strip())))
            i += 1
            continue

        # 无序列表
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(_inline(re.sub(r"^[-*]\s+", "", lines[i].strip())))
                i += 1
            html.append("<ul>" + "".join("<li>{}</li>".format(x) for x in items) + "</ul>")
            continue

        # 有序列表
        if re.match(r"^\d+[.、]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+[.、]\s+", lines[i].strip()):
                items.append(_inline(re.sub(r"^\d+[.、]\s+", "", lines[i].strip())))
                i += 1
            html.append("<ol>" + "".join("<li>{}</li>".format(x) for x in items) + "</ol>")
            continue

        # 空行
        if not stripped:
            i += 1
            continue

        # 普通段落
        html.append("<p>{}</p>".format(_inline(stripped)))
        i += 1

    flush_table()
    flush_code()
    return "".join(html)


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(s):
    """行内粗体/行内代码转 HTML。"""
    s = _esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def sync_one(key, manifest, td):
    doc = DOCS[key]
    url = manifest.get("source", {}).get(doc["manifest_key"])
    file_id = extract_file_id(url)
    md_path = os.path.join(REPO_DIR, doc["md"])
    if not file_id:
        print(f"[FAIL] {key}：manifest.json source.{doc['manifest_key']} 为空，无法定位腾讯文档。")
        return False
    if not os.path.exists(md_path):
        print(f"[FAIL] {key}：仓库文件 {doc['md']} 不存在。")
        return False

    md_text = open(md_path, encoding="utf-8").read()
    html = md_to_html(md_text)
    b64 = base64.b64encode(html.encode("utf-8")).decode()

    res, err = td.call_tool("doc-mcp", "overwrite_doc_with_html",
                            {"file_id": file_id, "base64_html_text": b64})
    if err:
        print(f"[FAIL] {key}（{file_id}）：{err}")
        return False
    print(f"[OK] {key}（{file_id}）已同步 {len(md_text)} 字符 → 腾讯文档（{doc['title']}）")
    return True


def main():
    args = sys.argv[1:]
    if "--check" in args:
        manifest = load_manifest()
        for key in DOCS:
            url = manifest.get("source", {}).get(DOCS[key]["manifest_key"])
            print(f"  {key}: file_id={extract_file_id(url)}  url={url}")
        return 0

    td_py = find_tencentdocs_py()
    if not td_py:
        print("[FAIL] 未找到 tencentdocs.py。请确认本机已安装 WorkBuddy 腾讯文档插件。")
        return 1
    sys.path.insert(0, os.path.dirname(td_py))
    import tencentdocs as td  # noqa

    manifest = load_manifest()
    targets = [a.upper() for a in args if a.upper() in DOCS] or list(DOCS.keys())
    ok = True
    for key in targets:
        ok = sync_one(key, manifest, td) and ok
    print("完成。" if ok else "存在失败项，请检查。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
