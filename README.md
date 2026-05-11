# 🐑 AI 羊毛雷达

自动追踪全网 Claude / ChatGPT / Gemini 等 AI 订阅的优惠信息、区域套利、拼车合租、学生折扣等羊毛情报。

## 功能

- **4 大数据源**：Reddit、V2EX、HackerNews、什么值得买
- **智能评分**：关键词匹配 + 模式识别 + 热度加权，自动过滤噪音
- **9 种优惠分类**：区域套利 / 拼车合租 / 优惠码 / 学生教育 / 礼品卡 / 免费试用 / 降价折扣 / 薅羊毛技巧 / API优惠
- **6 款产品追踪**：ChatGPT / Claude / Gemini / Copilot / Midjourney / Cursor
- **自动更新**：GitHub Actions 每 4 小时抓取一次
- **零成本部署**：GitHub Pages 静态托管，无需服务器

## 快速开始

### 1. Fork 本仓库

### 2. 启用 GitHub Pages
- Settings → Pages → Source: GitHub Actions

### 3. 手动触发首次抓取
- Actions → "Scrape AI Deals" → Run workflow

### 4. 访问你的站点
- `https://<你的用户名>.github.io/ai-price-tracker/`

## 项目结构

```
├── index.html              # 前端页面（纯静态，Tailwind CSS）
├── data/
│   └── deals.json          # 抓取的优惠数据（自动更新）
├── scraper/
│   ├── __init__.py
│   ├── main.py             # 主运行入口
│   ├── reddit.py           # Reddit 爬虫
│   ├── v2ex.py             # V2EX 爬虫
│   ├── hackernews.py       # HackerNews 爬虫（Algolia API）
│   ├── smzdm.py            # 什么值得买爬虫
│   └── scorer.py           # 评分 & 分类引擎
├── .github/
│   └── workflows/
│       └── scrape.yml      # 定时抓取 + 自动部署
├── requirements.txt
└── README.md
```

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行爬虫
python -m scraper.main

# 查看结果
# 用浏览器打开 index.html 即可
```

## 评分规则

| 信号 | 加分 |
|------|------|
| 标题包含产品名 | +6 |
| 正文包含产品名 | +3 |
| 匹配优惠类型关键词（标题） | +10 |
| 匹配优惠类型关键词（正文） | +5 |
| 包含价格信息（$xx / ¥xx） | +3 |
| 高互动（50+ upvotes） | +5 |
| 发布于 24 小时内 | +5 |
| 负面关键词（招聘/论文等） | -3 |

最终分数 ≥ 8 且匹配至少一种优惠类型 → 展示在页面上。

## ⚠️ 免责声明

- 本项目仅聚合公开信息，不提供代充、账号交易等服务
- 部分优惠方式（如区域套利、拼车合租）可能违反服务条款，请自行评估风险
- 信息仅供参考，时效性和准确性无法保证

## License

MIT
