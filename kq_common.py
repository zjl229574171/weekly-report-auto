#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kq_common.py — 考勤导入/渲染共享库（kq_import.py / kq_render.py 依赖）

职责：
  1. 定位并加载腾讯文档插件 tencentdocs.py（宿主 WorkBuddy 网关直调，token 由宿主注入）
  2. manifest.json 读取（Sheet《微波周报数据》file_id）
  3. Sheet 子表按名现查 sheet_id（不缓存，遵守 C 文档纪律）
  4. get_cell_data CSV 读取 / set_range_value 整批写入的健壮封装（兼容多种返回形态）

依赖：WorkBuddy 本机运行（CODEBUDDY_MCP_CONFIG 注入）；纯标准库 + 腾讯文档插件。
"""

import os
import sys
import json
import glob
import csv
import io
import urllib.request

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(REPO_DIR, "manifest.json")

# 子表名 → 用途（sheet_id 一律现查，不写死）
SHEET_ATTEND = "考勤记录"
SHEET_ROSTER = "花名册"
SHEET_MONTH_TMPL = "本月模板"


class KqError(Exception):
    pass


# ── 插件定位 / 加载 ──────────────────────────────────────────────
def find_tencentdocs_py():
    """定位 tencentdocs.py（WorkBuddy 插件缓存目录；多版本时取最高）。"""
    home = os.path.expanduser("~")
    patterns = [
        os.path.join(home, ".workbuddy", "plugins", "cache", "workbuddy-builtin",
                     "tencent-docs-plugin", "*", "skills", "tencent-docs", "tencentdocs.py"),
    ]
    hits = []
    for pat in patterns:
        hits.extend(glob.glob(pat))
    if not hits:
        return None
    return max(hits)  # 版本目录 1.0.x 字符串序 = 版本序（同前缀下取最新）


def load_td():
    """返回 tencentdocs 模块；失败抛 KqError。"""
    td_py = find_tencentdocs_py()
    if not td_py:
        raise KqError("未找到 tencentdocs.py：请确认本机已安装 WorkBuddy 腾讯文档插件且已连接")
    sys.path.insert(0, os.path.dirname(td_py))
    import tencentdocs  # noqa
    return tencentdocs


# ── 票据引导：gateway token provider 需带全 headers（含 X-WorkBuddy-MCP-Context） ──
_TOKEN_DONE = False


def bootstrap_token():
    """从宿主 V2 MCP Gateway 拉取腾讯文档 personal token 注入环境变量。

    插件 tencentdocs._load_tokens 自带的 provider 只带 Authorization，实测宿主
    gateway 会拒绝（缺 X-WorkBuddy-MCP-Context）→ no_token。这里把 connector-proxy
    的完整 headers 带上重试，成功后 TDOC_OAUTH_ACCESS_TOKEN 生效（env 优先）。
    """
    global _TOKEN_DONE
    if _TOKEN_DONE:
        return
    _TOKEN_DONE = True
    if os.environ.get("TDOC_OAUTH_ACCESS_TOKEN") or os.environ.get("TDOC_ONEID_ACCESS_TOKEN"):
        return
    cfg_raw = os.environ.get("CODEBUDDY_MCP_CONFIG")
    if not cfg_raw:
        return
    try:
        cfg = json.loads(cfg_raw)
    except ValueError:
        return
    srv = (cfg.get("mcpServers") or {}).get("connector-proxy") or {}
    url = srv.get("url") or ""
    hdrs = srv.get("headers") or {}
    if not (url.endswith("/mcp") and hdrs):
        return
    try:
        req = urllib.request.Request(url + "/internal/tencent-docs/tokens",
                                     headers=hdrs, method="GET")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        personal = data.get("personal") or {}
        if personal.get("available") and personal.get("token"):
            os.environ["TDOC_OAUTH_ACCESS_TOKEN"] = str(personal["token"])
    except Exception:
        pass


def load_manifest():
    if not os.path.exists(MANIFEST):
        raise KqError("未找到 manifest.json：请先按「初始化文档」完成初始化")
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def sheet_file_id():
    """《微波周报数据》file_id：manifest.source.Sheet URL 提取（C 文档权威 = WcPXBJrdsaWL）。"""
    m = load_manifest()
    url = (m.get("source") or {}).get("Sheet") or ""
    return extract_file_id(url)


def extract_file_id(url):
    if not url:
        return None
    return url.rstrip("/").split("/")[-1]


# ── 响应解析（兼容 content[].text 与扁平字段两种形态） ─────────────
def _deep_get(obj, key):
    """递归找第一个 key 对应的值。"""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = _deep_get(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _deep_get(v, key)
            if r is not None:
                return r
    return None


def _unwrap(res):
    """jsonrpc tools/call 响应 → 业务 payload。"""
    if not isinstance(res, dict):
        return res
    if "result" in res:
        res = res["result"]
    content = res.get("content")
    if isinstance(content, list) and content:
        texts = []
        for c in content:
            t = c.get("text") if isinstance(c, dict) else str(c)
            if isinstance(t, str):
                texts.append(t)
        if texts:
            joined = "".join(texts).strip()
            try:
                return json.loads(joined)
            except (ValueError, TypeError):
                return joined
    return res


def call(td, service, tool, args):
    """调用 MCP 工具；返回业务 payload。err 非空抛 KqError。"""
    bootstrap_token()
    # 宿主 MCP 层的工具名带业务前缀（sheet.get_cell_data）；直连腾讯 endpoint 无前缀
    if service.endswith("-mcp") and "." in tool:
        tool = tool.split(".")[-1]
    res, err = td.call_tool(service, tool, args)
    if err:
        raise KqError(f"{tool} 调用失败: {err}")
    payload = _unwrap(res)
    is_err = _deep_get(payload, "isError")
    if is_err:
        raise KqError(f"{tool} 返回错误: {json.dumps(payload, ensure_ascii=False)[:300]}")
    return payload


# ── Sheet 读 / 写 ───────────────────────────────────────────────
def sheet_meta(td, file_id):
    """返回 {子表名: sheet_id}。"""
    payload = call(td, "sheet-mcp", "sheet.get_sheet_info", {"file_id": file_id})
    sheets = payload.get("sheets") or payload.get("data", {}).get("sheets") or []
    if not sheets:
        # 兜底：尝试 result.sheets 之类
        sheets = _deep_get(payload, "sheets") or []
    return {s.get("sheet_name"): s.get("sheet_id") for s in sheets if s.get("sheet_id")}


def sheet_id_by_name(td, file_id, name):
    meta = sheet_meta(td, file_id)
    sid = meta.get(name)
    if not sid:
        raise KqError(f"子表「{name}」不存在（现有: {sorted(meta.keys())}）")
    return sid


def get_csv_rows(td, file_id, sheet_id, r0, c0, r1, c1):
    """读取区域为二维数组（过滤空行尾随占位）。r/c 均 0-based。"""
    payload = call(td, "sheet-mcp", "sheet.get_cell_data", {
        "file_id": file_id, "sheet_id": sheet_id,
        "start_row": r0, "start_col": c0, "end_row": r1, "end_col": c1,
        "return_csv": True,
    })
    csv_data = _deep_get(payload, "csv_data")
    if csv_data is None:
        raise KqError("get_cell_data 未返回 csv_data: " + json.dumps(payload, ensure_ascii=False)[:200])
    if isinstance(csv_data, list):
        return csv_data
    return list(csv.reader(io.StringIO(csv_data)))


def write_values(td, file_id, sheet_id, values):
    """values: [{row,col,value_type,string_value|number_value}]（0-based）。整批一次提交。"""
    call(td, "sheet-mcp", "sheet.set_range_value",
         {"file_id": file_id, "sheet_id": sheet_id, "values": values})


def str_val(v):
    if v is None:
        return ""
    return str(v).strip()


def is_blank_row(row):
    """过滤纯逗号尾随占位行。"""
    return all(str_val(x) == "" for x in row)
