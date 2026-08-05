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
        # index.html 使用 i.label / i.isUp(布尔)
        "indices": [
            {"label": "上证指数", "code": "sh000001", "value": "3900.00", "change": "+0.50%", "isUp": True},
        ],
        "note": "市场画像描述",
    },
    # index.html 使用 c.rank / c.name / c.change
    "hotConcepts": [
        {"rank": 1, "name": "示例概念", "change": "+3.00%"},
        {"rank": 2, "name": "示例概念2", "change": "+2.00%"},
    ],
    # index.html 使用 c.rank / c.medal / c.name / c.change（前三自动给 medal）
    "fiveDayConcepts": [
        {"rank": 1, "name": "示例5日", "change": "+5.00%", "medal": "🥇"},
        {"rank": 2, "name": "示例5日2", "change": "+4.00%", "medal": "🥈"},
    ],
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
    # index.html 使用 d.summaryTable.headers / .rows
    "summaryTable": {
        "headers": ["维度", "解读"],
        "rows": [
            ["市场背景", "描述"],
            ["核心逻辑", "描述"],
            ["风险因素", "描述"],
            ["仓位建议", "描述"],
        ],
    },
    # index.html 使用 t.time / t.desc
    "auctionTimeline": [
        {"time": "9:15-9:20", "desc": "观察竞价量"},
        {"time": "9:20-9:25", "desc": "确认竞价方向"},
        {"time": "9:25", "desc": "竞价结束决定是否参与"},
        {"time": "9:30-10:00", "desc": "开盘观察"},
    ],
    # index.html 直接渲染字符串数组，每项必须是 str
    "riskItems": [
        "🚨 <b>高风险提示 1</b>",
        "⚠️ <b>中风险提示 1</b>",
    ],
    # index.html 使用 d.sectorFocus.{verdict,logic,bias,defense,offense,avoid}
    # 基于今日市场情绪特征，推断明日应侧重的方向。纯情绪周期推断，非确定性建议。
    # 规范：defense 固定 2 个；defense/offense 每个板块下 stocks 必须恰好 2 只个股（含 name+code）；
    #       bias 必须存在且为 {defense:N, offense:M} 百分比（防御/进攻倾向，二者合计约 100）
    "sectorFocus": {
        "verdict": "明日分化在即——防守优先、进攻精选",
        "logic": "（说明推断逻辑：如连续百股涨停→次日分化概率高→资金高低切→防御方向优先）",
        "bias": {"defense": 60, "offense": 40},
        "defense": [
            {"name": "医药(创新药/中药)", "reason": "防御属性，退潮期相对抗跌", "stocks": [{"name": "恒瑞医药", "code": "sh600276"}, {"name": "药明康德", "code": "sh603259"}]},
            {"name": "银行/高股息红利", "reason": "低估值+稳定分红，避险首选", "stocks": [{"name": "工商银行", "code": "sh601398"}, {"name": "长江电力", "code": "sh600900"}]},
        ],
        "offense": [
            {"name": "PCB/算力(机构真金白银品种)", "reason": "仅限机构重仓，回避纯题材", "stocks": [{"name": "东山精密", "code": "sz002384"}, {"name": "工业富联", "code": "sh601138"}]},
            {"name": "半导体材料(靶材/大硅片)", "reason": "首板起爆，需看封单确认", "stocks": [{"name": "有研新材", "code": "sh600206"}, {"name": "风华高科", "code": "sz000636"}]},
        ],
        "avoid": [
            "纯题材高位连板(换手>30%分歧巨大)",
            "无机构背书的纯情绪票",
        ],
    },
    # index.html 使用 d.footer.source / d.footer.time
    "footer": {
        "source": "腾讯自选股 · 龙虎榜 · 通达信",
        "time": "2026-08-06 19:55",
    },
}

# 校验：非法结构会在 dumps 阶段抛错
json.dumps(D, ensure_ascii=False)
out = os.path.join(HERE, "data", f"{DATE_ID}.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(D, f, ensure_ascii=False, indent=2, separators=(",", ": "))
print("GENERATED", out, "stocks:", len(D["stocks"]))
