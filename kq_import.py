#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kq_import.py — 考勤月度导入（《微波载荷定标室.xlsx》→ Sheet「考勤记录」）

用途（对应 C 文档 §六A「考勤记录子表」）：
  发起人每月从考勤系统导出《微波载荷定标室.xlsx》后，本机运行本脚本：
    - 解析 xlsx 上下班打卡明细
    - 按固化口径计算每人每月一行（9 列：月份/姓名/应出勤天数/应出勤时长(h)/
      实际出勤天数/合计时长(h)/漏卡次数/异常摘要/备注）
    - 整批一次 set_range_value 写入 Sheet「考勤记录」（全量登记，含非花名册人员）
    - 读回逐格比对自检

口径（与 2026-08 实测数据一致，改动需同步 C 文档 §六A）：
  应出勤天数 = 当月总日数 − xlsx 标记「休息」日数；应出勤时长 = 应出勤天数 × 9h
  单日：双卡 = 下班 − 上班；漏下班卡（只有上午卡）= 上班卡 ~ 12:00 → 「漏下午」；
       漏上班卡（只有下午卡）= 12:00 ~ 下班卡 → 「漏上午」；双漏（无卡）= 0 → 「无卡」
  实际出勤 = 正常 1 天 / 单漏 0.5 天 / 无卡 0；漏卡次数 = 缺卡张数（单漏 1 / 双漏 2）
  合计时长 = Σ 单日时长（h，1 位小数）；异常摘要 = 区间压缩（如 8/4漏上午;8/19-21无卡）
  漏卡只计数不判因；备注列留空（本人自填），本脚本不写备注。

用法：
  python kq_import.py                     # --check：只计算并与 Sheet 现值比对，不写库
  python kq_import.py --write             # 计算并写入（同月已存在 → 覆盖该月块）
  python kq_import.py --xlsx <路径> --month 2026-08 --write
  python kq_import.py --show              # 只打印计算结果（不比对 Sheet）

依赖：WorkBuddy 本机运行（腾讯文档连接器已连）；python 需 openpyxl：
  pip install openpyxl   （本仓库脚本由 WorkBuddy 会话执行，自动使用隔离环境）
"""

import os
import re
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kq_common as kc  # noqa

COLS = ["月份", "姓名", "应出勤天数", "应出勤时长(h)", "实际出勤天数",
        "合计时长(h)", "漏卡次数", "异常摘要", "备注"]
DEFAULT_XLSX = r"D:/temp/微波载荷定标室.xlsx"

# xlsx 结构常量（实测 2026-08：Sheet0，row5=日期表头 E..AI，row6 起 每人两行 上下班）
DATE_ROW = 5          # 1-based
COL_NAME = 2          # B
COL_FLAG = 4          # D = 上班/下班
COL_DAY0 = 5          # E = 每周期首日
FULL_DAY = 31


def hhmm_to_min(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def num_str(v):
    """数字归一显示：整数不带 .0。"""
    f = float(v)
    return str(int(f)) if f == int(f) else str(round(f, 1))


def parse_xlsx(path):
    """返回 (month, people)。people: [{name, daily:[(up,down,dayno)]}] dayno 1..31。"""
    try:
        import openpyxl
    except ImportError:
        raise kc.KqError("缺少 openpyxl，请先安装：pip install openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]

    def cell(r, c):
        v = ws.cell(row=r, column=c).value
        return "" if v is None else str(v).strip()

    # 月份：row2「考勤周期 : 2026-08-31」
    m = re.search(r"(\d{4})-(\d{2})-\d{2}", cell(2, 1))
    if not m:
        raise kc.KqError(f"xlsx 第2行未找到考勤周期日期（A2={cell(2,1)!r}），结构可能变化")
    month = f"{m.group(1)}-{m.group(2)}"

    # 日期表头 row5 col E..：校验首日为 MM/01
    dates = []
    for c in range(COL_DAY0, COL_DAY0 + FULL_DAY):
        v = cell(DATE_ROW, c)
        if not re.match(r"^\d{2}/\d{2}$", v):
            raise kc.KqError(f"xlsx 日期表头第{DATE_ROW}行第{c}列异常: {v!r}")
        dates.append(v)
    if dates[0][-2:] != "01":
        raise kc.KqError(f"xlsx 日期表头首日应为当月1日，实际 {dates[0]}")

    people = []
    r = DATE_ROW + 1
    while r <= ws.max_row:
        name = cell(r, COL_NAME)
        flag = cell(r, COL_FLAG)
        if name and flag == "上班":
            up = [cell(r, c) for c in range(COL_DAY0, COL_DAY0 + FULL_DAY)]
            down = [cell(r + 1, c) for c in range(COL_DAY0, COL_DAY0 + FULL_DAY)] if r + 1 <= ws.max_row else []
            if len(down) != FULL_DAY:
                raise kc.KqError(f"{name} 的下班行缺失或结构异常（row {r + 1}）")
            daily = [(up[i], down[i], dates[i]) for i in range(FULL_DAY)]
            people.append({"name": name, "daily": daily})
            r += 2
        else:
            r += 1
    if not people:
        raise kc.KqError("xlsx 未解析到任何人员行，结构可能变化")
    return month, people


def calc_one(person):
    """按口径计算单人的 9 列（备注除外）。返回 dict。"""
    name = person["name"]
    days = [d for d in person["daily"]]
    rest_days = [d for d in days if d[0] == "休息" or d[1] == "休息"]

    def dayno_to_md(dayno):
        # dayno 形如 "08/04" → (8,4)
        mo, dd = dayno.split("/")
        return int(mo), int(dd)

    def md_to_label(mo, dd):
        return f"{mo}/{dd}"

    work = [d for d in days if d[0] != "休息" and d[1] != "休息"]
    total_min = 0
    att = 0.0
    miss = 0
    seq = []  # (label, kind)
    for up, down, dayno in work:
        mo, dd = dayno_to_md(dayno)
        label = md_to_label(mo, dd)
        u_off = up in ("", "漏卡")
        d_off = down in ("", "漏卡")
        if up and not u_off and down and not d_off:
            total_min += hhmm_to_min(down) - hhmm_to_min(up)
            att += 1.0
        elif up and not u_off and d_off:      # 只有上午卡 → 缺下午 → 漏下午
            total_min += 12 * 60 - hhmm_to_min(up)
            att += 0.5
            miss += 1
            seq.append((label, "漏下午"))
        elif u_off and down and not d_off:    # 只有下午卡 → 缺上午 → 漏上午
            total_min += hhmm_to_min(down) - 12 * 60
            att += 0.5
            miss += 1
            seq.append((label, "漏上午"))
        else:                                 # 双漏 → 无卡
            miss += 2
            seq.append((label, "无卡"))
    return {
        "应出勤天数": len(days) - len(rest_days),
        "应出勤时长(h)": (len(days) - len(rest_days)) * 9,
        "实际出勤天数": att,
        "合计时长(h)": round(total_min / 60.0, 1),
        "漏卡次数": miss,
        "异常摘要": compress_summary(seq),
    }


def _prev_day(mo, dd):
    import datetime
    d = datetime.date(2000, mo, dd) - datetime.timedelta(days=1)
    return d.month, d.day


def compress_summary(seq):
    """seq: [(label, kind)] → '8/4漏上午;8/19-21无卡'。相邻同日类型合并区间。"""
    if not seq:
        return ""
    parts = []

    def parse(label):
        mo, dd = label.split("/")
        return int(mo), int(dd)

    def fmt(mo, dd):
        return f"{mo}/{dd}"

    cur_kind = None
    seg_start = None
    seg_end = None

    def flush():
        nonlocal parts, cur_kind, seg_start, seg_end
        if seg_start is None:
            return
        s = fmt(*seg_start)
        if seg_end and seg_end != seg_start:
            s = f"{s}-{seg_end[1]}" if seg_start[0] == seg_end[0] else f"{s}-{fmt(*seg_end)}"
        parts.append(f"{s}{cur_kind}")
        seg_start = seg_end = None
        cur_kind = None

    for label, kind in seq:
        mo, dd = parse(label)
        if kind == cur_kind and seg_end and _prev_day(mo, dd) == seg_end:
            seg_end = (mo, dd)
            continue
        flush()
        cur_kind = kind
        seg_start = seg_end = (mo, dd)
    flush()
    return ";".join(parts)


def build_records(month, people):
    """people → 9 列 records（月份/姓名 + calc_one 结果 + 备注''）。"""
    recs = []
    for p in people:
        c = calc_one(p)
        recs.append({
            "月份": month, "姓名": p["name"],
            "应出勤天数": c["应出勤天数"], "应出勤时长(h)": c["应出勤时长(h)"],
            "实际出勤天数": c["实际出勤天数"], "合计时长(h)": c["合计时长(h)"],
            "漏卡次数": c["漏卡次数"], "异常摘要": c["异常摘要"], "备注": "",
        })
    return recs


def rec_to_row(rec):
    return [rec["月份"], rec["姓名"], rec["应出勤天数"], rec["应出勤时长(h)"],
            rec["实际出勤天数"], rec["合计时长(h)"], rec["漏卡次数"],
            rec["异常摘要"], rec["备注"]]


def display(recs):
    lines = []
    for r in recs:
        lines.append(
            f"{r['姓名']:<6} 应出勤{r['应出勤天数']}天/{num_str(r['应出勤时长(h)'])}h  "
            f"实际{num_str(r['实际出勤天数'])}天 合计{num_str(r['合计时长(h)'])}h  "
            f"漏卡{r['漏卡次数']} 摘要[{r['异常摘要'] or '-'}]")
    return "\n".join(lines)


def locate_month_block(td, file_id, sheet_id, month):
    """现读全表（200 行×9 列），返回 (header_row0, 月份行 idx 列表, 首个全空行 idx)。"""
    rows = kc.get_csv_rows(td, file_id, sheet_id, 0, 0, 199, 8)
    month_rows = [i for i, row in enumerate(rows) if i > 0 and kc.str_val(row[0]) == month]
    first_blank = None
    for i in range(1, len(rows)):
        if kc.is_blank_row(rows[i]):
            first_blank = i
            break
    return rows, month_rows, first_blank


def main():
    ap = argparse.ArgumentParser(description="考勤月度导入（xlsx → Sheet 考勤记录）")
    ap.add_argument("--xlsx", default=DEFAULT_XLSX, help=f"考勤 xlsx 路径（默认 {DEFAULT_XLSX}）")
    ap.add_argument("--month", default="", help="目标月份 YYYY-MM（默认从 xlsx 推断）")
    ap.add_argument("--write", action="store_true", help="写库（默认只 check 比对，不写）")
    ap.add_argument("--show", action="store_true", help="只打印计算结果，不比对 Sheet")
    args = ap.parse_args()

    if not os.path.exists(args.xlsx):
        print(f"[FAIL] xlsx 不存在：{args.xlsx}")
        return 1

    month_from_xlsx, people = parse_xlsx(args.xlsx)
    month = args.month or month_from_xlsx
    if month != month_from_xlsx:
        print(f"[WARN] 指定月份 {month} 与 xlsx 周期 {month_from_xlsx} 不一致，按指定月份处理")
    recs = build_records(month, people)
    print(f"== 计算完成：{month} 共 {len(recs)} 人 ==")
    print(display(recs))

    if args.show:
        return 0

    td = kc.load_td()
    file_id = kc.sheet_file_id()
    if not file_id:
        print("[FAIL] manifest.source.Sheet 为空")
        return 1
    sheet_id = kc.sheet_id_by_name(td, file_id, kc.SHEET_ATTEND)
    rows, month_rows, first_blank = locate_month_block(td, file_id, sheet_id, month)

    expected = []
    for i, rec in enumerate(recs):
        expected.append([i + (month_rows[0] if month_rows else first_blank), rec])

    if args.write:
        # ── 写库（整批一次 set_range_value） ──
        if month_rows:
            start = month_rows[0]
            base = len(month_rows)
            n = len(recs)
            if n > base:
                # 新增行检查：块尾到 start+n 之间不得压到别的月份数据
                for i in range(start + base, start + n):
                    if not kc.is_blank_row(rows[i]) and kc.str_val(rows[i][0]) not in ("", month):
                        raise kc.KqError(
                            f"{month} 人数从 {base} 增至 {n}，但 row{i} 之后已有其他月份数据（{rows[i][0]}），"
                            "请人工处理（不建议脚本跨月插行）")
            # 构造 values：目标行集合 = start..start+n-1（覆盖/新写）+ 清空剩余旧行
            target_rows = list(range(start, start + n))
            stale = list(range(start + n, start + base))
        else:
            start = first_blank
            if start is None:
                raise kc.KqError("Sheet「考勤记录」已无空行（200 行满），请人工扩表")
            target_rows = list(range(start, start + len(recs)))
            stale = []

        values = []
        for row_idx, rec in zip(target_rows, recs):
            row_vals = rec_to_row(rec)
            for c, v in enumerate(row_vals):
                if c == 7:  # 异常摘要 STRING
                    values.append({"row": row_idx, "col": c, "value_type": "STRING", "string_value": v})
                elif c == 8:  # 备注不写（本人自填）
                    continue
                elif c in (2, 3, 4, 5, 6):
                    fv = float(v)
                    values.append({"row": row_idx, "col": c, "value_type": "NUMBER",
                                   "number_value": int(fv) if fv == int(fv) else round(fv, 1)})
                else:  # 0 月份 / 1 姓名
                    values.append({"row": row_idx, "col": c, "value_type": "STRING", "string_value": v})
        for row_idx in stale:
            for c in range(0, 9):
                values.append({"row": row_idx, "col": c, "value_type": "STRING", "string_value": ""})
        print(f"[WRITE] 写入 row{target_rows[0]}..row{target_rows[-1]}（{len(target_rows)} 行）"
              f"{'，并清空旧行 ' + str(stale) if stale else ''} …")
        kc.write_values(td, file_id, sheet_id, values)
        # 写后读回自检
        r0 = min(target_rows) if target_rows else start
        r1 = max((target_rows or [start]) + (stale or []))
        back = kc.get_csv_rows(td, file_id, sheet_id, r0, 0, r1, 8)
        diff = []
        for k, (row_idx, rec) in enumerate(zip(target_rows, recs)):
            want = rec_to_row(rec)
            got = back[k] if k < len(back) else []
            for c in range(0, 9):
                wv = num_str(want[c]) if c in (2, 3, 4, 5, 6) else ("" if c == 8 else str(want[c]))
                gv = num_str(got[c]) if c in (2, 3, 4, 5, 6) and got and c < len(got) else \
                    (kc.str_val(got[c]) if got and c < len(got) else "")
                if wv != gv:
                    diff.append(f"  row{row_idx} col{c}（{COLS[c]}）：期望[{wv}] 实际[{gv}]")
        for i in stale:
            got = back[(i - r0)] if 0 <= i - r0 < len(back) else []
            if got and not kc.is_blank_row(got):
                diff.append(f"  row{i} 应为空，实际有内容")
        if diff:
            print("[FAIL] 写后读回不一致：\n" + "\n".join(diff))
            return 1
        print(f"[OK] 写入完成，读回一致（row{r0}..{r1}）")
        return 0

    # ── check 模式：与现值比对 ──
    if not month_rows:
        print("[CHECK] Sheet 尚无该月数据（首个空行 = row%d）。以上为将写入内容。" % first_blank)
        return 0
    start = month_rows[0]
    back = kc.get_csv_rows(td, file_id, sheet_id, start, 0, start + len(month_rows) - 1, 8)
    diffs = []
    for k, (row_idx, rec) in enumerate(zip(month_rows, recs)):
        want = rec_to_row(rec)
        got = back[k] if k < len(back) else []
        for c in range(0, 9):
            if c == 8:
                continue  # 备注不比
            wv = num_str(want[c]) if c in (2, 3, 4, 5, 6) else str(want[c])
            gv = num_str(got[c]) if c in (2, 3, 4, 5, 6) and c < len(got) else \
                (kc.str_val(got[c]) if c < len(got) else "")
            if wv != gv:
                diffs.append(f"  row{row_idx} col{c}（{COLS[c]}）{rec['姓名']}：脚本[{wv}] Sheet[{gv}]")
    if diffs:
        print(f"[CHECK] 发现 {len(diffs)} 处与 Sheet 现值不一致（口径或结构差异）：")
        print("\n".join(diffs[:60]))
        return 1
    print("[CHECK] 与 Sheet 现值完全一致 ✓（同月重跑幂等）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
