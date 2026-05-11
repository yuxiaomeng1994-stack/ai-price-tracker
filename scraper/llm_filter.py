"""
可选的 LLM 二次筛选模块。
使用 DeepSeek / OpenAI 兼容 API 判断候选条目是否真的是 AI 订阅优惠。

启用方式：设置环境变量 LLM_API_KEY 和可选的 LLM_BASE_URL、LLM_MODEL。
如果未设置，此模块直接返回输入列表（跳过 LLM 筛选）。

推荐用 DeepSeek:
  LLM_API_KEY=sk-xxx
  LLM_BASE_URL=https://api.deepseek.com/v1
  LLM_MODEL=deepseek-chat
"""

import os
import json
import time
import requests


def is_llm_enabled() -> bool:
    return bool(os.environ.get("LLM_API_KEY"))


def get_config():
    return {
        "api_key": os.environ.get("LLM_API_KEY", ""),
        "base_url": os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        "model": os.environ.get("LLM_MODEL", "deepseek-chat"),
    }


SYSTEM_PROMPT = """你是一个 AI 订阅优惠信息筛选助手。用户会给你一些从论坛/社区抓取的帖子，你需要判断每个帖子是否真的包含 Claude/ChatGPT/Gemini/Copilot/Midjourney/Cursor 等 AI 产品的订阅优惠信息。

判断标准：
- ✅ 保留：包含具体的优惠方式（区域套利、拼车、优惠码、学生折扣、降价、礼品卡、免费额度、薅羊毛技巧）
- ❌ 剔除：纯粹的模型评测、使用教程、技术讨论、新闻资讯、招聘、求助问答

返回 JSON 格式：{"keep": [true/false, ...]}，顺序与输入一致。只返回 JSON，不要任何其他文字。"""


def batch_filter(items: list[dict], batch_size: int = 10) -> list[dict]:
    """
    对候选条目做 LLM 二次筛选。
    如果 LLM 未配置，直接返回输入。
    """
    if not is_llm_enabled():
        print("[LLM] 未配置 API Key，跳过 LLM 筛选")
        return items

    config = get_config()
    kept_items = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        # Build user message
        user_content = "请判断以下帖子是否包含真实的 AI 订阅优惠信息：\n\n"
        for idx, item in enumerate(batch):
            title = item.get("title", "")[:100]
            body = item.get("body", "")[:200]
            tags = ", ".join(item.get("tags", []))
            user_content += f"[{idx + 1}] 标题: {title}\n   标签: {tags}\n   摘要: {body}\n\n"

        try:
            resp = requests.post(
                f"{config['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config["model"],
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                },
                timeout=60,
            )

            if resp.status_code != 200:
                print(f"[LLM] API 返回 {resp.status_code}，跳过当前批次")
                kept_items.extend(batch)  # Fallback: keep all
                continue

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            decision = json.loads(content)
            keep_flags = decision.get("keep", [True] * len(batch))

            for idx, item in enumerate(batch):
                if idx < len(keep_flags) and keep_flags[idx]:
                    kept_items.append(item)

            time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"[LLM] 错误: {e}，保留当前批次全部条目")
            kept_items.extend(batch)

    print(f"[LLM] 筛选前: {len(items)}, 筛选后: {len(kept_items)}")
    return kept_items
