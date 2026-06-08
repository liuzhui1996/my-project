"""
GitHub Trending → 飞书多维表格
通过 GitHub API 获取每日热门仓库，写入飞书多维表格
"""
import requests
from datetime import datetime, timedelta

# ========== 配置 ==========
FEISHU_APP_ID = "cli_aaacd4738fb85be8"
FEISHU_APP_SECRET = "PL9yfbQKWsWt0MiFvXKZXdDYYYut58MA"
BITABLE_APP_TOKEN = "Fg1CboZxRalLcCsPV7ecQIg3nXd"
BITABLE_TABLE_ID = "tblo7KCENL9raw8m"
TOP_N = 20


def get_feishu_token():
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
    )
    return resp.json()["tenant_access_token"]


def get_trending_repos():
    """通过 GitHub API 获取最近创建的高星仓库"""
    yesterday = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://api.github.com/search/repositories?q=created:>{yesterday}&sort=stars&order=desc&per_page={TOP_N}"
    
    resp = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"}, timeout=30)
    data = resp.json()
    
    repos = []
    for r in data.get("items", [])[:TOP_N]:
        repos.append({
            "repo_name": r["full_name"],
            "desc": (r.get("description") or "")[:200],
            "stars": r["stargazers_count"],
            "lang": r.get("language") or "",
            "url": r["html_url"],
        })
    return repos


def write_to_feishu(token, repos):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records/batch_create"
    
    today = datetime.now().strftime("%Y-%m-%d")
    records = []
    for r in repos:
        records.append({
            "fields": {
                "仓库名": r["repo_name"],
                "描述": r["desc"],
                "星数": r["stars"],
                "语言": r["lang"],
                "链接": {"text": r["repo_name"], "link": r["url"]},
                "日期": today,
            }
        })
    
    resp = requests.post(url, headers=headers, json={"records": records})
    result = resp.json()
    if result.get("code") == 0:
        print(f"✅ 成功写入 {len(records)} 条数据到飞书")
    else:
        print(f"❌ 写入失败: {result.get('msg', result)}")


def main():
    print(f"📊 开始抓取 GitHub Trending ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    
    repos = get_trending_repos()
    print(f"   抓到 {len(repos)} 个仓库")
    
    for i, r in enumerate(repos[:5], 1):
        print(f"   {i}. {r['repo_name']} ⭐{r['stars']:,}")
    
    token = get_feishu_token()
    write_to_feishu(token, repos)


if __name__ == "__main__":
    main()
