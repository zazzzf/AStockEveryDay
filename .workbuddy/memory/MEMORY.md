# AStockEveryDay 项目备忘录

## 回测数据更新规则

每次新交易日结束后更新 backtest_results.json：

1. **更新现有 is_recent 条目**：将所有 `is_recent: true` 的条目 `exit_date` 更新为最新交易日，`exit_close` 更新为最新交易日收盘价，重新计算 `return_pct` 和 `days_held`
2. **新增当日预测条目**：如果当日有新的预测数据文件（如 20260701.json），新增回测条目：`entry_date` = 当日日期，`entry_open` = 当日开盘价，`exit_close` = 当日收盘价，`is_recent: true`
3. **重新计算统计**：更新 `total_predictions`、`win_count`、`win_rate`、`avg_return`
4. **同步副本**：确保 root 级别和 data/ 目录下的 backtest_results.json 保持一致

数据来源：通过 `westockdata` skill 的 kline 命令批量查询所有需要的股票 K 线数据。

## 文件结构
- `backtest_results.json`（root 级别）：主回测数据文件
- `data/backtest_results.json`：同步副本
- `data/YYYYMMDD.json`：每日预测数据文件
- `data/predictions.json`：预测索引
- `index.html`：SPA 主应用

## 项目技术栈
- 纯静态 SPA，无构建步骤
- Tailwind CSS CDN
- 中国股市配色：红涨绿跌
