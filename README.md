# 🐑 AI 羊毛雷达

自动追踪全网 Claude / ChatGPT / Gemini 等 AI 订阅的优惠信息、区域套利、拼车合租、学生折扣、薅羊毛技巧等。

## ✨ 功能

- **6 大数据源**：Reddit、V2EX、HackerNews、什么值得买、Chiphell、Telegram 公开频道
- **智能评分**：关键词匹配 + 模式识别 + 热度加权，自动过滤噪音
- **可选 LLM 二次筛选**：配置 DeepSeek / OpenAI API Key 后，用 LLM 进一步剔除无关帖子
- **9 种优惠分类**：区域套利 / 拼车合租 / 优惠码 / 学生教育 / 礼品卡 / 免费试用 / 降价折扣 / 薅羊毛技巧 / API 优惠
- **6 款产品追踪**：ChatGPT、Claude、Gemini、Copilot、Midjourney、Cursor
- **前端体验**：深色模式、实时搜索（`/` 快捷键）、多维筛选、多种排序、卡片流
- **自动更新**：GitHub Actions 每 4 小时抓取并自动部署
- **零成本**：GitHub Pages 静态托管，无需服务器

## 🚀 快速开始

### 1. Fork 本仓库

### 2. 启用 GitHub Pages
Settings → Pages → Source: **GitHub Actions**

### 3. (可选) 启用 LLM 筛选
Settings → Secrets and variables → Actions → New repository secret:
- `LLM_API_KEY` — DeepSeek / OpenAI 兼容的 API Key
- `LLM_BASE_URL` — 可选，默认 `https://api.deepseek.com/v1`
- `LLM_MODEL` — 可选，默认 `deepseek-chat`

### 4. 首次手动抓取
Actions → "Scrape AI Deals" → Run workflow

### 5. 访问站点
`https://<你的用户名>.github.io/ai-price-tracker/`

## 📁 项目结构

```
├── index.html                   # 前端（Tailwind + Vanilla JS，零构建）
├── data/deals.json              # 抓取结果，GitHub Actions 自动更新
├── scraper/
│   ├── main.py                  # 主入口
│   ├── reddit.py                # Reddit（6 个 subreddit）
│   ├── v2ex.py                  # V2EX（节点 API + SOV2EX 搜索）
│   ├── hackernews.py            # HackerNews（Algolia API）
│   ├── smzdm.py                 # 什么值得买（搜索 + RSS）
│   ├── chiphell.py              # Chiphell 论坛
│   ├── telegram.py              # Telegram 公开频道（t.me/s/）
│   ├── scorer.py                # 评分 & 分类引擎
│   └── llm_filter.py            # LLM 二次筛选（可选）
├── .github/workflows/scrape.yml # 每 4 小时自动抓取 + 部署
├── requirements.txt
└── README.md
```

## 🧠 评分规则

| 信号 | 加分 |
|------|------|
| 标题包含产品名 | +6 |
| 正文包含产品名 | +3 |
| 匹配优惠类型关键词（标题） | +10 |
| 匹配优惠类型关键词（正文） | +5 |
| 包含价格信息（$xx / ¥xx / xx元） | +3 |
| 高互动（50+ upvotes） | +5 |
| 发布于 24 小时内 | +5 |
| 负面关键词（招聘 / 纯评测 等） | -3 |

最终分数 ≥ 8 且匹配至少一种优惠类型 → 展示在页面上。

启用 LLM 后，还会调用 DeepSeek/OpenAI 对候选帖子做二次判断，剔除纯资讯/评测/技术讨论。

## 🖥️ 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行爬虫
python -m scraper.main

# (可选) 启用 LLM 筛选
export LLM_API_KEY=sk-xxx
python -m scraper.main

# 查看结果 - 直接用浏览器打开 index.html
python -m http.server 8000
# 访问 http://localhost:8000
```

## ⌨️ 快捷键

- `/` — 聚焦搜索框
- `Esc` — 取消搜索聚焦

## ⚠️ 免责声明

- 本项目仅聚合公开信息，不提供代充、账号交易等服务
- 部分优惠方式（如区域套利、拼车合租）可能违反服务条款，请自行评估风险
- 信息仅供参考，时效性与准确性无法保证

## 📄 License

MIT
