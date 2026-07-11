import os
import json
import urllib.request

# 1. 初始化环境变量
token = os.environ.get("GITHUB_TOKEN")
repo = os.environ.get("GITHUB_REPOSITORY")
username = repo.split("/")[0]

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
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode("utf-8"))
    weeks = res_data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
except Exception:
    exit(1)

# 3. 动态绘制真实 matrix.svg
svg_header = """<svg width="715" height="95" viewBox="0 0 715 95" xmlns="http://www.w3.org/2000/svg">
  <style>
    .lvl-0 { fill: #161b22; rx: 2px; }
    .lvl-1 { fill: #0e4429; rx: 2px; animation: scanLevel1 4s infinite ease-in-out; }
    .lvl-2 { fill: #006d32; rx: 2px; animation: scanLevel2 4s infinite ease-in-out; }
    .lvl-3 { fill: #26a641; rx: 2px; animation: scanLevel1 4s infinite ease-in-out; }
    .lvl-4 { fill: #39d353; rx: 2px; animation: scanLevel2 4s infinite ease-in-out; }
    @keyframes scanLevel1 { 0%, 100% { opacity: 1; } 20% { opacity: 0.1; } 40% { opacity: 1; } }
    @keyframes scanLevel2 { 0%, 100% { opacity: 1; } 50% { opacity: 0.1; } 100% { opacity: 1; } }
  </style>
  <g>
"""

rects = []
level_map = {
    "NONE": "lvl-0",
    "FIRST_QUARTILE": "lvl-1",
    "SECOND_QUARTILE": "lvl-2",
    "THIRD_QUARTILE": "lvl-3",
    "FOURTH_QUARTILE": "lvl-4"
}

for week_idx, week in enumerate(weeks):
    for day in week["contributionDays"]:
        day_idx = day["weekday"]
        level = day["contributionLevel"]
        cls = level_map.get(level, "lvl-0")
        x = week_idx * 13
        y = day_idx * 13
        rects.append(f'    <rect x="{x}" y="{y}" width="11" height="11" class="{cls}" />')

svg_content = svg_header + "\n".join(rects) + "\n  </g>\n</svg>"

with open("matrix.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

# 4. 实时联网抓取一言语录
selected_quote = "生活原本沉闷，但跑起来就会有风。"
try:
    quote_req = urllib.request.Request(
        "https://v1.hitokoto.cn/", 
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(quote_req, timeout=5) as response:
        quote_data = json.loads(response.read().decode("utf-8"))
        selected_quote = f"{quote_data.get('hitokoto')}  —— 《{quote_data.get('from')} \u300b"
except Exception:
    pass

# 5. 精准写回 README.md（改用 100% 肉眼可见标签）
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_text = f.read()
    
    start_tag = "[QUOTE_START]"
    end_tag = "[QUOTE_END]"
    
    if start_tag in readme_text and end_tag in readme_text:
        before = readme_text.split(start_tag)[0]
        after = readme_text.split(end_tag)[1]
        new_readme = f"{before}{start_tag}\n\n> 💡 {selected_quote}\n\n{end_tag}{after}"
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_readme)
