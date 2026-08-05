# -*- coding: utf-8 -*-
"""
AStockEveryDay 数据生成规范模板（agent 生成预测 JSON 时照抄此模式）。

★ 唯一允许的写法：先在 Python 里构造 dict，再用 json.dump 序列化。
  —— 绝不手写 JSON 文本、绝不字符串拼接。json.dump 会自动转义引号/换行/控制字符。

用法：填好下面的 D 字典，直接 python gen_template.py 即可生成 data/YYYYMMDD.json。
校验：生成后跑 `python validate_data.py data/YYYYMMDD.json` 确认无硬伤（或依赖 pre-commit 钩子）。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATE_ID = "20260807"  # ← 改成预测日期 YYYYMMDD

# 全部用中文引号『』「」或转义，绝不在字符串里裸写 ASCII 双引号 "
# 例如写 "MLCC是电子工业的“大米”" 会破坏 JSON；应写成 "MLCC是电子工业的「大米」" 或转义为 \"
D = {
    "id": DATE_ID,
    "date": "2026-08-07",
    "weekday": "周五",
    "generated": "08-06 19:55",
    "title": "🔥 涨停预测 · 示例五虎",
    "subtitle": "示例副标题",
    "macroAlert": "🚨 <b>示例宏观警报</b>",
    "themeOverview": "<b>「示例」</b>——市场概况描述。",
    "marketSnapshot": {
        "indices": [
            {"name": "上证指数", "code": "sh000001", "value": "3900.00", "change": "+0.50%", "trend": "up"},
        ],
        "note": "市场画像描述",
    },
    "hotConcepts": [{"name": "示例概念", "change": "+3.00%"}],
    "fiveDayConcepts": [{"name": "示例5日", "change": "+5.00%"}],
    "stocks": [
        {
            "rank": 1,
            "name": "示例股",
            "code": "sz000001",
            "score": 99,
            "tags": [{"label": "涨停", "type": "board"}],
            "price": 10.00,
            "change": "+10.00%",
            "limitStatus": "涨停封板",
            "metrics": [{"label": "市值", "value": "100亿"}],
            "coreLogic": "<b>核心逻辑描述（用中文引号「」避免 ASCII 双引号）</b>",
            "auctionExpect": "<b class='hl'>竞价预期描述</b>",
            "entryCondition": "<b class='hl'>上车条件描述</b>",
        },
        # ... 共 5 只，rank 1-5
    ],
    "summaryTable": [{"label": "市场背景", "value": "示例"}],
    "auctionTimeline": [{"time": "9:15-9:20", "event": "示例"}],
    "riskItems": [{"level": "critical", "text": "🚨 <b>示例风险</b>"}],
    "footer": "⚠️ 以上内容由 AI 基于公开市场信息自动生成，仅供参考，不构成任何投资建议。",
}

# 校验：非法结构会在 dumps 阶段抛错
json.dumps(D, ensure_ascii=False)
out = os.path.join(HERE, "data", f"{DATE_ID}.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(D, f, ensure_ascii=False, indent=2, separators=(",", ": "))
print("GENERATED", out, "stocks:", len(D["stocks"]))
