#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kq_render.py — 月报考勤页渲染（Sheet「考勤记录」→ 当月月报模板考勤页表格）

用途（对应 E 文档 §三A「考勤汇总页」）：
  发起人本地运行，把当月考勤计数填入月报模板的考勤页表格：
    - 取数：Sheet「考勤记录」过滤「月份 = 目标月」的行
    - 人员口径：与「花名册」求交集、按花名册顺序排列 —— 非花名册人员（如领导/非在册）
      不渲染；Sheet 仍全量登记，此处只过滤展示层
    - PPT 只放计数：姓名 | 应出勤 | 实际出勤 | 合计时长 | 漏卡次数 | 备注
      （异常摘要不进 PPT，明细留 Sheet，页脚注已指引）
    - 表格为「母版已画好、只改内容」模式：占位表第 1 行（row0）= 表头，
      数据从 row1 起；人数 ≤ 空行上限 → 填前 N 行并清空剩余行（不删行）；
      人数超上限 → 报错提示人工补行（slide_insert_table_rows，本脚本不插行）

为什么是脚本而不是 AI 会话逐格写：
  平台对 slide 表格只有单格 slide_set_cell_text，无批量改格接口——60 格=60 次
  API 往返是版式下限；脚本直连网关串行执行可去掉 AI 逐格编排开销。

用法：
  python kq_render.py --month 2026-08                     # --check：打印将渲染内容，不写
  python kq_render.py --month 2026-08 --write             # 写入当月月报模板考勤页
  python kq_render.py --month 2026-08 --file-id WSUIFXTCMxag --write
      # 指定目标文件（默认从 Sheet「本月模板」按月份现查）
  python kq_render.py --month 2026-08 --write --dry-cell-count  # 仅打印将写格数（调试用）

依赖：WorkBuddy 本机运行（腾讯文档连接器已连）。纯标准库。
"""

import os
import sys
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kq_common as kc  # noqa

# 考勤页表格结构常量（母版考勤占位页：6 列空计数表，row0=表头，数据行 1..9）
TABLE_ROWS_CAP = 9        # 占位表数据行上限
TABLE_COLS = ["姓名", "应出勤", "实际出勤", "合计时长", "漏卡次数", "备注"]  # col0..5
DEFAULT_SHAPE_ID = "84ahw3"
PAGE_SEARCH_TEXT = "考勤汇总"

# 数字归一显示
def num_str(v):
    f = float(v)
    return str(int(f)) if f == int(f) else str(round(f, 1))


def month_key(m):
    """'2026-08' → '2026年08月'（本月模板表月份列格式）。"""
    y, mo = m.split("-")
    return f"{y}年{mo}月"


def gather(td, file_id, month):
    """读考勤记录当月行 ∩ 花名册（按花名册顺序）→ 渲染行数据 list。"""
    att_id = kc.sheet_id_by_name(td, file_id, kc.SHEET_ATTEND)
    ros_id = kc.sheet_id_by_name(td, file_id, kc.SHEET_ROSTER)

    # 花名册（顺序权威；row0=表头）
    roster_rows = kc.get_csv_rows(td, file_id, ros_id, 0, 0, 199, 0)
    roster = [kc.str_val(r[0]) for r in roster_rows[1:] if r and kc.str_val(r[0])]
    if not roster:
        raise kc.KqError("花名册为空")

    # 考勤记录：读全表 200 行 × 9 列
    att_rows = kc.get_csv_rows(td, file_id, att_id, 0, 0, 199, 8)
    by_name = {}
    for row in att_rows[1:]:
        if row and kc.str_val(row[0]) == month and kc.str_val(row[1]):
            by_name[row[1]] = row

    # 交集 + 花名册顺序
    out = []
    for name in roster:
        row = by_name.get(name)
        if not row:
            continue
        out.append({
            "姓名": name,
            "应出勤": num_str(row[2]),
            "实际出勤": num_str(row[4]),
            "合计时长": num_str(row[5]),
            "漏卡次数": num_str(row[6]),
            "备注": kc.str_val(row[8]),
        })
    return roster, out


def plan_cells(people):
    """people → [(row, col, text)]；数据行 1..N，剩余行清空。"""
    cells = []
    for i, p in enumerate(people):
        row = i + 1
        for c, key in enumerate(["姓名", "应出勤", "实际出勤", "合计时长", "漏卡次数", "备注"]):
            cells.append((row, c, p[key]))
    for row in range(len(people) + 1, TABLE_ROWS_CAP + 1):
        for c in range(0, 6):
            cells.append((row, c, ""))
    return cells


def main():
    ap = argparse.ArgumentParser(description="月报考勤页渲染（Sheet → 模板表格）")
    ap.add_argument("--month", required=True, help="目标月份 YYYY-MM（考勤记录表月份列格式）")
    ap.add_argument("--file-id", default="", help="目标月报模板 file_id（默认从 Sheet「本月模板」现查）")
    ap.add_argument("--shape-id", default=DEFAULT_SHAPE_ID, help=f"考勤页表格 shape id（默认 {DEFAULT_SHAPE_ID}）")
    ap.add_argument("--page-index", type=int, default=None, help="考勤页 index（默认 slide_find_text 现查）")
    ap.add_argument("--write", action="store_true", help="写 PPT（默认只 check 预览，不写）")
    args = ap.parse_args()

    td = kc.load_td()
    file_id = kc.sheet_file_id()
    if not file_id:
        print("[FAIL] manifest.source.Sheet 为空")
        return 1

    roster, people = gather(td, file_id, args.month)
    if not people:
        print(f"[FAIL] Sheet「考勤记录」无 {args.month} 数据（发起人需先跑 kq_import.py 导入）")
        return 1
    miss = [n for n in roster if n not in {p["姓名"] for p in people}]
    print(f"== 渲染取数：{args.month} 花名册 ∩ 考勤记录 = {len(people)} 人 ==")
    for p in people:
        print(f"  {p['姓名']:<6} 应出勤{p['应出勤']} 实际{p['实际出勤']} 合计{p['合计时长']}h 漏卡{p['漏卡次数']} 备注[{p['备注'] or '-'}]")
    if miss:
        print(f"  [注] 花名册中当月无考勤记录：{miss}（将不出现在考勤页）")
    if len(people) > TABLE_ROWS_CAP:
        print(f"[FAIL] 人数 {len(people)} 超过占位表数据行上限 {TABLE_ROWS_CAP}，"
              "需先在母版/模板人工 slide_insert_table_rows 补行（本脚本不插行）")
        return 1

    # 目标文件
    tgt = args.file_id
    if not tgt:
        mt_id = kc.sheet_id_by_name(td, file_id, kc.SHEET_MONTH_TMPL)
        rows = kc.get_csv_rows(td, file_id, mt_id, 0, 0, 199, 3)
        key = month_key(args.month)
        for row in rows:
            if kc.str_val(row[0]) == key and kc.str_val(row[2]):
                tgt = kc.str_val(row[2])
                break
        if not tgt:
            print(f"[FAIL] Sheet「本月模板」未找到 {key} 的登记行，请 --file-id 显式指定")
            return 1
    print(f"== 目标：file_id={tgt} ==")

    # 考勤页定位
    page_index = args.page_index
    if page_index is None:
        payload = kc.call(td, "slide-mcp", "slide_find_text",
                          {"file_id": tgt, "search": PAGE_SEARCH_TEXT})
        matches = kc._deep_get(payload, "matches") or []
        if not matches:
            print(f"[FAIL] 目标文件内未找到「{PAGE_SEARCH_TEXT}」文本，请检查是否已插入考勤页")
            return 1
        # 取标题型匹配（文本上下文最短、含"考勤汇总"字样优先），多页时取第一个
        page_index = int(matches[0].get("page_index", 0))
    print(f"== 考勤页 index={page_index}，表格 shape={args.shape_id} ==")

    cells = plan_cells(people)
    write_n = sum(1 for (_, _, t) in cells if t != "")
    print(f"== 将写入 {write_n} 格内容 + 清空 {len(cells) - write_n} 格（共 {len(cells)} 次单元格写） ==")

    if not args.write:
        print("[CHECK] 预览如上；确认无误后加 --write 执行。")
        return 0

    # ── 逐格写（串行直连网关） ──
    t0 = time.time()
    fails = []
    ok = 0
    for row, col, text in cells:
        try:
            kc.call(td, "slide-mcp", "slide_set_cell_text", {
                "file_id": tgt, "page_index": page_index,
                "shape_id": args.shape_id, "row": row, "col": col, "text": text,
            })
            ok += 1
        except kc.KqError as e:
            fails.append((row, col, str(e)))
    dt = time.time() - t0
    if fails:
        print(f"[FAIL] {len(fails)}/{len(cells)} 格失败（用时 {dt:.0f}s）：")
        for row, col, e in fails[:30]:
            print(f"  row{row} col{col}: {e}")
        return 1
    print(f"[OK] 考勤页填充完成：{ok} 格全部成功（用时 {dt:.0f}s）")
    print("    提示：slide 表格文本无读回通道，请打开模板目检一次（标题=YYYY年MM月考勤汇总）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
