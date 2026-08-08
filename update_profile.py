import os
import json
import urllib.request
import time

# 1. 读取环境变量
token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")
repo = os.environ.get("GITHUB_REPOSITORY", "")
username = repo.split("/")[0] if "/" in repo else repo
current_time = int(time.time())

if not token or not username:
    print("❌ 错误：未读取到 Token 或 GITHUB_REPOSITORY 环境变量！")
    exit(1)

# 2. GraphQL 查询 GitHub 官方贡献墙数据
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
        print("❌ GraphQL 查询失败:", json.dumps(res_data["errors"], indent=2))
        exit(1)
        
    weeks = res_data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    print(f"✅ 成功读取 GitHub 官方数据，共 {len(weeks)} 周！")
except Exception as e:
    print(f"❌ 请求失败: {e}")
    exit(1)

# 3. 绘制 1:1 还原官方绿墙的 matrix.svg
padding = 6       # 外边距，防止贴边
box_size = 11     # 方块大小
step = 13         # 方块 11px + 间距 2px

total_weeks = len(weeks)
svg_width = padding * 2 + total_weeks * step - 2
svg_height = padding * 2 + 7 * step - 2

svg_header = f'<svg width="100%" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg">\n  <g>\n'

# GitHub 官方绿墙 5 档颜色
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
        
        x = padding + week_idx * step
        y = padding + day_idx * step
        rects.append(f'    <rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" fill="{fill_color}" rx="2" />')

svg_content = svg_header + "\n".join(rects) + "\n  </g>\n</svg>"

with open("matrix.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("✅ matrix.svg 已成功生成并写入！")

# 4. 抓取一言语录并更新 README.md
selected_quote = "生活原本沉闷，但跑起来就会有风。"
try:
    quote_req = urllib.request.Request(
        "https://v1.hitokoto.cn/", 
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(quote_req, timeout=5) as response:
        quote_data = json.loads(response.read().decode("utf-8"))
        selected_quote = f"{quote_data.get('hitokoto')}  —— 《{quote_data.get('from')}》"
except Exception:
    pass

if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_text = f.read()
    
    start_tag = "<!-- QUOTE_START -->"
    end_tag = "<!-- QUOTE_END -->"
    if start_tag in readme_text and end_tag in readme_text:
        before = readme_text.split(start_tag)[0]
        after = readme_text.split(end_tag)[1]
        readme_text = f"{before}{start_tag}\n\n> 💡 {selected_quote}\n\n{end_tag}{after}"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_text)
    print("✅ README.md 同步更新成功！")
