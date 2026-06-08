"""
AI 热点 → 飞书群（卡片消息） + 飞书表格（静默写入）
"""
import requests
import json
from datetime import datetime, timedelta

# ========== 配置 ==========
FEISHU_APP_ID = "cli_aaacd4738fb85be8"
FEISHU_APP_SECRET = "PL9yfbQKWsWt0MiFvXKZXdDYYYut58MA"
BITABLE_APP_TOKEN = "Fg1CboZxRalLcCsPV7ecQIg3nXd"
BITABLE_TABLE_ID = "tblo7KCENL9raw8m"
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/179c1e6a-1942-4b19-9a3e-e6a7b4f6cc87"
AI_TOPICS = ["ai", "llm", "machine-learning", "deep-learning", "artificial-intelligence"]


def get_feishu_token():
    return requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
    ).json()["tenant_access_token"]


def get_ai_repos():
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    all_repos = {}
    for topic in AI_TOPICS:
        url = f"https://api.github.com/search/repositories?q=created:>{week_ago}+topic:{topic}&sort=stars&order=desc&per_page=15"
        try:
            resp = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"}, timeout=15)
            for r in resp.json().get("items", []):
                all_repos[r["full_name"]] = r
        except:
            continue
    return sorted(all_repos.values(), key=lambda x: x["stargazers_count"], reverse=True)[:15]


def write_to_feishu(token, repos):
    """静默写入飞书表格"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records/batch_create"
    today = datetime.now().strftime("%Y-%m-%d")
    records = [{"fields": {
        "仓库名": r["full_name"],
        "描述": (r.get("description") or "")[:200],
        "星数": r["stargazers_count"],
        "今日星数": 0,
        "语言": r.get("language") or "",
        "链接": {"text": "GitHub", "link": r["html_url"]},
        "日期": today,
    }} for r in repos]
    requests.post(url, headers=headers, json={"records": records})
    print(f"✅ 表格写入 {len(records)} 条")


def send_card_to_feishu(repos):
    """发送卡片消息到飞书群"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 构建卡片内容
    elements = []
    
    # 标题
    elements.append({
        "tag": "markdown",
        "content": f"**📊 AI 热点日报** | {today}"
    })
    elements.append({"tag": "hr"})
    
    # 每个仓库
    for i, r in enumerate(repos[:10], 1):
        desc = (r.get("description") or "")[:80]
        lang = r.get("language") or "N/A"
        stars = r["stargazers_count"]
        url = r["html_url"]
        
        md = f"**{i}. [{r['full_name']}]({url})**\n⭐ {stars:,} | {lang}"
        if desc:
            md += f"\n{desc}"
        
        elements.append({"tag": "markdown", "content": md})
    
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": f"数据来源：GitHub Trending | 共 {len(repos)} 个项目"}]
    })
    
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🤖 AI 热点日报"},
                "template": "blue"
            },
            "elements": elements
        }
    }
    
    resp = requests.post(FEISHU_WEBHOOK, json=card)
    if resp.json().get("code") == 0:
        print(f"✅ 飞书群发送成功")
    else:
        print(f"❌ 群发送失败: {resp.json()}")


def main():
    print(f"📊 AI 热点 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    repos = get_ai_repos()
    print(f"   抓到 {len(repos)} 个 AI 仓库")
    
    token = get_feishu_token()
    write_to_feishu(token, repos)
    send_card_to_feishu(repos)


if __name__ == "__main__":
    main()
