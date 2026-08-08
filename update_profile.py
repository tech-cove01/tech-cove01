import os
import json
import urllib.request
import time

# 1. 初始化环境变量
token = os.environ.get("GITHUB_TOKEN")
repo = os.environ.get("GITHUB_REPOSITORY", "")
username = repo.split("/")[0] if "/" in repo else repo
current_time = int(time.time())

if not token or not username:
    print("❌ 错误：未读取到 GITHUB_TOKEN 或 GITHUB_REPOSITORY 环境变量！")
    exit(1)

# 2. GraphQL 查询真实数据
query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            contributionLevel
            weekday
          }
        }
      }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": {"login": username}}).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (GitHub-Matrix-Generator)"
    }
)

try:
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        
    if "errors" in res_data:
        print("❌ GitHub GraphQL 返回错误:", json.dumps(res_data["errors"], indent=2))
        exit(1)
        
    weeks = res_data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    print(f"✅ 成功抓取到 {len(weeks)} 周的数据！")
except Exception as e:
    print(f"❌ 请求 GitHub GraphQL 失败: {e}")
    exit(1)

# 3. 动态绘制 matrix.svg（动态计算精准宽度 + 100% 自适应，彻底解决裁切问题）
total_weeks = len(weeks)
svg_width = total_weeks * 13  # 每周占 13px (11px 方块 + 2px 间距)
svg_height = 95

# ⚠️ 将 width 设置为 100%，由 viewBox 掌控比例，完美适配任何屏幕与 GitHub 容器
svg_header = f'<svg width="100%" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg">\n  <g>\n'

color_map = {
    "NONE": "#161b22",
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353"
}

rects = []
for week_idx, week in enumerate(weeks):
    for day in week["contributionDays"]:
        day_idx = day["weekday"]
        level = day["contributionLevel"]
        fill_color = color_map.get(level, "#161b22")
        x = week_idx * 13
        y = day_idx * 13
        rects.append(f'    <rect x="{x}" y="{y}" width="11" height="11" fill="{fill_color}" rx="2" />')

svg_content = svg_header + "\n".join(rects) + "\n  </g>\n</svg>"

with open("matrix.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print(f"✅ matrix.svg 渲染成功！动态宽度: {svg_width}px")

# 4. 实时联网抓取一言语录
selected_quote = "生活原本沉闷，但跑起来就会有风。"
try:
    quote_req = urllib.request.Request(
        "https://v1.hitokoto.cn/", 
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(quote_req, timeout=5) as response:
        quote_data = json.loads(response.read().decode("utf-8"))
        selected_quote = f"{quote_data.get('hitokoto')}  —— 《{quote_data.get('from')}》"
except Exception as e:
    print(f"⚠️ 一言抓取失败，使用默认语录: {e}")

# 5. 精准写回 README.md 
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_text = f.read()
    
    start_tag = "<!-- QUOTE_START -->"
    end_tag = "<!-- QUOTE_END -->"
    if start_tag in readme_text and end_tag in readme_text:
        before = readme_text.split(start_tag)[0]
        after = readme_text.split(end_tag)[1]
        readme_text = f"{before}{start_tag}\n\n> 💡 {selected_quote}\n\n{end_tag}{after}"
    
    stats_start = "<!-- STATS_START -->"
    stats_end = "<!-- STATS_END -->"
    if stats_start in readme_text and stats_end in readme_text:
        before_stats = readme_text.split(stats_start)[0]
        after_stats = readme_text.split(stats_end)[1]
        
        dynamic_stats_block = f"""{stats_start}
### 📈 我的赛博活跃心电图
![](https://github-readme-activity-graph.vercel.app/graph?username={username}&theme=react-dark&bg_color=0d1117&hide_border=true)

### 📊 我的 GitHub 战力看板
![](https://github-readme-stats.vercel.app/api?username={username}&show_icons=true&theme=ocean_dark&cache_seconds=1800)
![](https://github-readme-stats.vercel.app/api/top-langs/?username={username}&layout=compact&theme=ocean_dark&hide=html,css&cache_seconds=1800)
![](https://streak-stats.demolab.com/?user={username}&theme=ocean_dark)
{stats_end}"""
        
        readme_text = f"{before_stats}{dynamic_stats_block}{after_stats}"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_text)
    print("✅ README.md 更新完毕！")
