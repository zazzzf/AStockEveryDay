# -*- coding: utf-8 -*-
"""
AStockEveryDay 数据完整性校验器（pre-commit 钩子 / CI 用）

设计原则：钩子的核心使命是拦截"坏数据"（推到 GitHub 后前端打不开 / 显示乱码），
而不是惩罚历史文件的格式差异。因此检查分两级：

  【硬伤 HARD】→ 直接导致详情页打不开或展示错乱，必须拦截（退出码 1）
    1. 非合法 UTF-8
    2. 含 U+FFFD 替换字符（编码乱码，源中文变成 �）
    3. 含非法控制字符（0x00-0x1f 裸字节，字符串内混入换行/制表符）
    4. json.loads 解析失败（未转义引号 / 结构断裂 —— 8/6 与 7/10 的真实 bug）
    5. 日期文件 id != 文件名；date 非 YYYY-MM-DD
    6. stocks 非列表或数量 != 5
    7. 个股缺失关键字段(rank/name/code/score/tags/price/change/limitStatus/
       metrics/coreLogic/auctionExpect/entryCondition)
    8. predictions 条目 id 非 YYYYMMDD；topStocks/topCodes 长度 != 5
    9. 渲染器 schema 错配导致页面显示 undefined / [object Object]：
       - marketSnapshot.indices[] 缺 label 或 isUp
       - hotConcepts[] / fiveDayConcepts[] 缺 rank
       - summaryTable 不是 {headers, rows} 对象
       - auctionTimeline[] 缺 desc
       - riskItems[] 包含非字符串对象

  【软项 SOFT】→ 历史格式差异或完整性提示，只警告不拦截（退出码仍 0）
    - 缺失可选顶层字段(fiveDayConcepts/auctionTimeline/themeOverview 等)
    - footer 仍是字符串（页脚来源/时间会为空，但不会阻断页面）
    - predictions 排序非最新在前

用法：
  python validate_data.py            # 钩子模式：仅校验 git 暂存区 data/ 下改动文件
  python validate_data.py --all      # 审计模式：扫描整个 data 目录并分级报告
退出码：0=无硬伤(可提交)，1=存在硬伤(应阻止提交)
"""
import json
import os
import re
import sys
import glob
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")

REQUIRED_TOP = [
    "id", "date", "weekday", "generated", "title", "subtitle",
    "marketSnapshot", "hotConcepts", "fiveDayConcepts", "stocks",
    "summaryTable", "auctionTimeline", "riskItems", "footer",
]
REQUIRED_STOCK = [
    "rank", "name", "code", "score", "tags", "price", "change",
    "limitStatus", "metrics", "coreLogic", "auctionExpect", "entryCondition",
]
REQUIRED_INDEX = [
    "id", "date", "weekday", "generated", "title",
    "summary", "topStocks", "topCodes",
]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^\d{8}$")
ILLEGAL_CTRL = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]")


class Report:
    def __init__(self):
        self.hard = 0
        self.soft = 0

    def hard_err(self, path, msg):
        self.hard += 1
        print(f"  ✗ [硬伤] {path}: {msg}")

    def soft_warn(self, path, msg):
        self.soft += 1
        print(f"  ⚠ [提示] {path}: {msg}")


def check_text(raw, path, rep):
    """解析文本。返回对象或 None。硬伤直接记入 rep。"""
    if b"\xef\xbf\xbd" in raw:
        rep.hard_err(path, "含 U+FFFD 替换字符（编码乱码，源中文变成 �）")
    if ILLEGAL_CTRL.search(raw):
        rep.hard_err(path, "含非法控制字符（0x00-0x1f 裸字节）")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        rep.hard_err(path, f"非法 UTF-8: {e}")
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        rep.hard_err(path, f"JSON 解析失败: {e}")
        return None


def check_date_file(d, path, stem, rep):
    if not isinstance(d, dict):
        rep.hard_err(path, "顶层必须是对象"); return
    if d.get("id") != stem:
        rep.hard_err(path, f"id='{d.get('id')}' 不等于文件名 '{stem}'")
    if not DATE_RE.match(str(d.get("date", ""))):
        rep.hard_err(path, f"date 格式非法: '{d.get('date')}' (应为 YYYY-MM-DD)")
    for k in ("fiveDayConcepts", "auctionTimeline", "themeOverview", "macroAlert"):
        if k not in d:
            rep.soft_warn(path, f"缺少可选字段 '{k}'（历史格式）")
    stocks = d.get("stocks")
    if not isinstance(stocks, list):
        rep.hard_err(path, "stocks 必须是数组"); return
    if len(stocks) != 5:
        rep.hard_err(path, f"stocks 数量应为 5，实际 {len(stocks)}")
    for i, s in enumerate(stocks):
        if not isinstance(s, dict):
            rep.hard_err(path, f"stocks[{i}] 不是对象"); continue
        nm = s.get("name", "?")
        for k in REQUIRED_STOCK:
            if k not in s:
                rep.hard_err(path, f"stocks[{i}]({nm}) 缺失字段 '{k}'")
        if s.get("tags") is not None and not isinstance(s["tags"], list):
            rep.hard_err(path, f"stocks[{i}]({nm}) tags 必须是数组")
        if s.get("metrics") is not None and not isinstance(s["metrics"], list):
            rep.hard_err(path, f"stocks[{i}]({nm}) metrics 必须是数组")

    # ===== 与 index.html 渲染器对齐的 schema 硬检查 =====
    ms = d.get("marketSnapshot")
    if isinstance(ms, dict):
        for j, it in enumerate(ms.get("indices", [])):
            if "label" not in it:
                rep.hard_err(path, f"marketSnapshot.indices[{j}] 缺 'label'（会导致 undefined）")
            if "isUp" not in it:
                rep.hard_err(path, f"marketSnapshot.indices[{j}] 缺 'isUp' 布尔值")
            if "value" not in it or it.get("value") is None:
                rep.hard_err(path, f"marketSnapshot.indices[{j}]({it.get('label','?')}) 缺 'value'（页面显示 undefined，旧 schema 用 price 需迁移）")
            if it.get("change") is not None and not isinstance(it.get("change"), str):
                rep.soft_warn(path, f"marketSnapshot.indices[{j}]({it.get('label','?')}) change 建议为字符串（当前 {type(it.get('change')).__name__}，如 {it.get('change')!r}→应为 '+1.15%'）")
    for j, c in enumerate(d.get("hotConcepts", [])):
        if "rank" not in c:
            rep.hard_err(path, f"hotConcepts[{j}]({c.get('name','?')}) 缺 'rank'（会显示 #undefined）")
        # 渲染器执行 c.change.startsWith('+')：非字符串会 TypeError，整页打不开（20260728 真实事故）
        if c.get("change") is not None and not isinstance(c.get("change"), str):
            rep.hard_err(path, f"hotConcepts[{j}]({c.get('name','?')}) change 必须是字符串（当前 {type(c.get('change')).__name__}，如 {c.get('change')!r}→应为 '+9.65%'）")
    for j, c in enumerate(d.get("fiveDayConcepts", [])):
        if "rank" not in c:
            rep.hard_err(path, f"fiveDayConcepts[{j}]({c.get('name','?')}) 缺 'rank'")
        if c.get("change") is not None and not isinstance(c.get("change"), str):
            rep.soft_warn(path, f"fiveDayConcepts[{j}]({c.get('name','?')}) change 建议为字符串（当前 {type(c.get('change')).__name__}，页面涨幅为空）")
    st = d.get("summaryTable")
    if isinstance(st, list):
        rep.hard_err(path, "summaryTable 为数组；渲染器需要 {headers, rows} 对象")
    elif isinstance(st, dict):
        if "headers" not in st or "rows" not in st:
            rep.hard_err(path, "summaryTable 对象必须含 'headers' 和 'rows'")
    for j, t in enumerate(d.get("auctionTimeline", [])):
        if "desc" not in t:
            rep.hard_err(path, f"auctionTimeline[{j}] 缺 'desc'（会显示 undefined）")
    ri = d.get("riskItems")
    if isinstance(ri, list):
        for j, r in enumerate(ri):
            if not isinstance(r, str):
                rep.hard_err(path, f"riskItems[{j}] 必须是字符串（当前 {type(r).__name__}，会显示 [object Object]）")
    # footer 软检查：字符串仍能过，但提示应改为对象
    if isinstance(d.get("footer"), str):
        rep.soft_warn(path, "footer 建议改为对象 {source, time}（当前字符串导致页脚来源为空）")
    # sectorFocus（可选功能）硬检查：若提供则结构必须正确，否则页面渲染异常
    sf = d.get("sectorFocus")
    if sf is not None:
        if not isinstance(sf, dict):
            rep.hard_err(path, "sectorFocus 必须是对象")
        else:
            if not sf.get("verdict"):
                rep.hard_err(path, "sectorFocus.verdict 缺失（页面标题为空）")
            b = sf.get("bias")
            if not isinstance(b, dict) or not isinstance(b.get("defense"), (int, float)) or not isinstance(b.get("offense"), (int, float)):
                rep.hard_err(path, "sectorFocus.bias 必须是含 defense/offense 数值的对象（防御/进攻倾向百分比）")
            for grp in ("defense", "offense"):
                items = sf.get(grp)
                if items is not None:
                    if not isinstance(items, list):
                        rep.hard_err(path, f"sectorFocus.{grp} 必须是数组")
                    else:
                        for j, it in enumerate(items):
                            if not isinstance(it, dict) or "name" not in it or "reason" not in it:
                                rep.hard_err(path, f"sectorFocus.{grp}[{j}] 必须是含 name/reason 的对象")
            av = sf.get("avoid")
            if av is not None and not isinstance(av, list):
                rep.hard_err(path, "sectorFocus.avoid 必须是数组")
    # 兜底：旧版数组字段类型
    for arr in ("hotConcepts", "fiveDayConcepts", "summaryTable",
                "auctionTimeline", "riskItems", "marketSnapshot"):
        v = d.get(arr)
        if v is not None and not isinstance(v, (list, dict)):
            rep.soft_warn(path, f"'{arr}' 类型非预期(历史格式)")


def check_predictions(d, path, rep):
    if not isinstance(d, list):
        rep.hard_err(path, "predictions.json 顶层必须是数组"); return
    prev = None
    for i, e in enumerate(d):
        if not isinstance(e, dict):
            rep.hard_err(path, f"第 {i} 条不是对象"); continue
        for k in REQUIRED_INDEX:
            if k not in e:
                rep.hard_err(path, f"第 {i} 条缺失字段 '{k}'")
        if not ID_RE.match(str(e.get("id", ""))):
            rep.hard_err(path, f"第 {i} 条 id='{e.get('id')}' 非 YYYYMMDD")
        for fld in ("topStocks", "topCodes"):
            v = e.get(fld)
            if isinstance(v, list) and len(v) != 5:
                rep.hard_err(path, f"第 {i} 条 {fld} 长度应为 5，实际 {len(v)}")
        cur = str(e.get("id", ""))
        if prev is not None and cur > prev:
            rep.soft_warn(path, f"排序: 第 {i} 条 {cur} 晚于上一条 {prev}（应最新在前）")
        prev = cur


def get_staged():
    """兜底：从 git 暂存区获取 data/ 下改动文件（钩子通常直接传参，此路径仅作后备）。"""
    try:
        staged = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=HERE, stderr=subprocess.DEVNULL).decode("utf-8").split()
    except Exception:
        staged = []
    return [os.path.join(HERE, r) for r in staged
            if "/data/" in r and r.endswith(".json") and os.path.exists(os.path.join(HERE, r))]


def all_files():
    files = [os.path.join(DATA_DIR, "predictions.json"),
             os.path.join(DATA_DIR, "backtest_results.json")]
    files += sorted(glob.glob(os.path.join(DATA_DIR, "20*.json")))
    return [f for f in files if os.path.exists(f)]


def resolve_targets():
    args = [a for a in sys.argv[1:] if a != "--all"]
    if args:
        targets = []
        for a in args:
            p = a if os.path.isabs(a) else os.path.join(HERE, a)
            if os.path.exists(p):
                targets.append(p)
        return targets, "（钩子指定文件）"
    if "--all" in sys.argv:
        return all_files(), "（全量审计）"
    staged = get_staged()
    return staged, "（仅暂存改动）"


def run(targets):
    rep = Report()
    for f in targets:
        base = os.path.basename(f)
        print(f"[{base}]")
        d = check_text(open(f, "rb").read(), base, rep)
        if d is None:
            continue
        if base == "predictions.json":
            check_predictions(d, base, rep)
        elif base == "backtest_results.json":
            pass
        else:
            check_date_file(d, base, base[:-5], rep)
    return rep


def main():
    targets, mode = resolve_targets()
    if not targets:
        print("（本次无数据文件改动，跳过校验）")
        return 0
    print("=== AStockEveryDay 数据校验" + mode + " ===")
    rep = run(targets)
    print("=" * 30)
    print(f"硬伤: {rep.hard}  |  提示: {rep.soft}")
    if rep.hard:
        print("✗ 存在硬伤，应阻止提交")
        return 1
    print("✓ 无硬伤，可提交" + ("（含 %d 项历史格式提示）" % rep.soft if rep.soft else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
