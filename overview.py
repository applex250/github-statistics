#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Statistics —— SVG 卡片 + 主页 README 生成器
(替代 tanjeffreyz 私有仓库 github-overview 的 main.py,输出格式 1:1 复刻)

输入:
  output/stats.json                          用户总览统计(Java 程序生成)
  output/repositories/{owner}/{repo}.json    各仓库信息(Java 程序生成)
  repositories.txt                           要生成卡片/展示的仓库清单(每行 owner/repo)
输出:
  output/overview.svg                        总览渐变卡片(Issues/PRs/Contributions/Repos/Stars)
  output/repositories/{owner}/{repo}.svg     每个清单内仓库的渐变卡片
  output/spacer.svg                          间隔条(静态,已存在则保留)
  output/footer.svg                          底部波浪装饰(静态,已存在则保留)
  generated_readme.md                        主页 README(HTML,推送到 profile 仓库)
"""
import json
import os
import sys
import html

OWNER = "applex250"          # GitHub 用户名
REPO = "github-statistics"   # 本生成器所在仓库名
OUTPUT_DIR = "output"
# 图片走 jsdelivr CDN(国内可达),并带 commit SHA 以绕过 CDN 缓存滞后
CDN_SHA = os.environ.get("SHA", "main")
RAW_BASE = f"https://cdn.jsdelivr.net/gh/{OWNER}/{REPO}@{CDN_SHA}/output"

# ---------------------------------------------------------------- 通用工具
def fmt_num(n: int) -> str:
    n = int(n)
    if n >= 1000:
        return f"{n / 1000:.1f}K"  # 9719 -> 9.7K
    return str(n)

def esc(s: str) -> str:
    return html.escape(s or "", quote=True)

def wrap_desc(text: str, max_chars: int = 69) -> list:
    """按单词边界把描述截成最多 2 行,每行不超过 max_chars 字符(与原版 main.py 一致:69 字符 ≈ 396px)。"""
    if not text:
        return []
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            if len(lines) == 2:
                break
            cur = w
            # 单词本身超长则硬截断
            while len(cur) > max_chars:
                lines.append(cur[: max_chars])
                cur = cur[max_chars:]
    if cur and len(lines) < 2:
        lines.append(cur)
    if len(lines) == 2 and len(lines[1]) > max_chars:
        lines[1] = lines[1][: max_chars - 3].rstrip() + "..."
    return lines

# ---------------------------------------------------------------- 图标 path
ICON_REPO_1 = "M3 2.75A2.75 2.75 0 015.75 0h14.5a.75.75 0 01.75.75v20.5a.75.75 0 01-.75.75h-6a.75.75 0 010-1.5h5.25v-4H6A1.5 1.5 0 004.5 18v.75c0 .716.43 1.334 1.05 1.605a.75.75 0 01-.6 1.374A3.25 3.25 0 013 18.75v-16zM19.5 1.5V15H6c-.546 0-1.059.146-1.5.401V2.75c0-.69.56-1.25 1.25-1.25H19.5z"
ICON_REPO_2 = "M7 18.25a.25.25 0 01.25-.25h5a.25.25 0 01.25.25v5.01a.25.25 0 01-.397.201l-2.206-1.604a.25.25 0 00-.294 0L7.397 23.46a.25.25 0 01-.397-.2v-5.01z"
ICON_ISSUES_1 = "M17.28 9.28a.75.75 0 00-1.06-1.06l-5.97 5.97-2.47-2.47a.75.75 0 00-1.06 1.06l3 3a.75.75 0 001.06 0l6.5-6.5z"
ICON_ISSUES_2 = "M12 1C5.925 1 1 5.925 1 12s4.925 11 11 11 11-4.925 11-11S18.075 1 12 1zM2.5 12a9.5 9.5 0 1119 0 9.5 9.5 0 01-19 0z"
ICON_PR_1 = "M4.75 3a1.75 1.75 0 100 3.5 1.75 1.75 0 000-3.5zM1.5 4.75a3.25 3.25 0 116.5 0 3.25 3.25 0 01-6.5 0zM4.75 17.5a1.75 1.75 0 100 3.5 1.75 1.75 0 000-3.5zM1.5 19.25a3.25 3.25 0 116.5 0 3.25 3.25 0 01-6.5 0zm17.75-1.75a1.75 1.75 0 100 3.5 1.75 1.75 0 000-3.5zM16 19.25a3.25 3.25 0 116.5 0 3.25 3.25 0 01-6.5 0z"
ICON_PR_2 = "M4.75 7.25A.75.75 0 015.5 8v8A.75.75 0 014 16V8a.75.75 0 01.75-.75zm8.655-5.53a.75.75 0 010 1.06L12.185 4h4.065A3.75 3.75 0 0120 7.75v8.75a.75.75 0 01-1.5 0V7.75a2.25 2.25 0 00-2.25-2.25h-4.064l1.22 1.22a.75.75 0 01-1.061 1.06l-2.5-2.5a.75.75 0 010-1.06l2.5-2.5a.75.75 0 011.06 0z"
ICON_CONTRIB = "M12 2.5c-3.81 0-6.5 2.743-6.5 6.119 0 1.536.632 2.572 1.425 3.56.172.215.347.422.527.635l.096.112c.21.25.427.508.63.774.404.531.783 1.128.995 1.834a.75.75 0 01-1.436.432c-.138-.46-.397-.89-.753-1.357a18.354 18.354 0 00-.582-.714l-.092-.11c-.18-.212-.37-.436-.555-.667C4.87 12.016 4 10.651 4 8.618 4 4.363 7.415 1 12 1s8 3.362 8 7.619c0 2.032-.87 3.397-1.755 4.5-.185.23-.375.454-.555.667l-.092.109c-.21.248-.405.481-.582.714-.356.467-.615.898-.753 1.357a.75.75 0 01-1.437-.432c.213-.706.592-1.303.997-1.834.202-.266.419-.524.63-.774l.095-.112c.18-.213.355-.42.527-.634.793-.99 1.425-2.025 1.425-3.561C18.5 5.243 15.81 2.5 12 2.5zM9.5 21.75a.75.75 0 01.75-.75h3.5a.75.75 0 010 1.5h-3.5a.75.75 0 01-.75-.75zM8.75 18a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5z"
ICON_STAR = "M12 .25a.75.75 0 01.673.418l3.058 6.197 6.839.994a.75.75 0 01.415 1.279l-4.948 4.823 1.168 6.811a.75.75 0 01-1.088.791L12 18.347l-6.117 3.216a.75.75 0 01-1.088-.79l1.168-6.812-4.948-4.823a.75.75 0 01.416-1.28l6.838-.993L11.328.668A.75.75 0 0112 .25zm0 2.445L9.44 7.882a.75.75 0 01-.565.41l-5.725.832 4.143 4.038a.75.75 0 01.215.664l-.978 5.702 5.121-2.692a.75.75 0 01.698 0l5.12 2.692-.977-5.702a.75.75 0 01.215-.664l4.143-4.038-5.725-.831a.75.75 0 01-.565-.41L12 2.694z"
# fork 图标(三个 path,与样例一致)
ICON_FORK_1 = "M12 21a1.75 1.75 0 110-3.5 1.75 1.75 0 010 3.5zm-3.25-1.75a3.25 3.25 0 106.5 0 3.25 3.25 0 00-6.5 0zm-3-12.75a1.75 1.75 0 110-3.5 1.75 1.75 0 010 3.5zM2.5 4.75a3.25 3.25 0 106.5 0 3.25 3.25 0 00-6.5 0zM18.25 6.5a1.75 1.75 0 110-3.5 1.75 1.75 0 010 3.5zM15 4.75a3.25 3.25 0 106.5 0 3.25 3.25 0 00-6.5 0z"
ICON_FORK_2 = "M6.5 7.75v1A2.25 2.25 0 008.75 11h6.5a2.25 2.25 0 002.25-2.25v-1H19v1a3.75 3.75 0 01-3.75 3.75h-6.5A3.75 3.75 0 015 8.75v-1h1.5z"
ICON_FORK_3 = "M11.25 16.25v-5h1.5v5h-1.5z"

# ---------------------------------------------------------------- CP2077 palette
CP = {
    "bg":        "#0D0D12",
    "grad_top":  "#111219",
    "grad_mid":  "#16181F",
    "grad_bot":  "#0D0D12",
    "yellow":    "#FCEE0A",
    "cyan":      "#00F0FF",
    "magenta":   "#FF003C",
    "text_dim":  "#B8BCC4",
    "border":    "#FCEE0A",
}

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900"
    "&family=Rajdhani:wght@400;500;600&display=swap');"
)
FONT_NUM  = "'Orbitron','Trebuchet MS',sans-serif"
FONT_BODY = "'Rajdhani','Trebuchet MS',sans-serif"

# 切角多边形：总览卡 896x256（左上22 + 右下22）
PATH_BIG = "M22,0 H896 V234 L874,256 H0 V22 Z"
PATH_BIG_INNER = "M25,3 H893 V231 L871,253 H3 V25 Z"
# 仓库卡 421x140
PATH_SMALL = "M22,0 H421 V118 L399,140 H0 V22 Z"
PATH_SMALL_INNER = "M25,3 H418 V115 L396,137 H3 V25 Z"
# 卡角夹折线
CORNER_TL = "M0,34 L0,22 L12,10"
CORNER_BR = "M896,222 L896,234 L884,246"
CORNER_BR_S = "M421,106 L421,118 L409,130"

# ---------------------------------------------------------------- overview.svg
OVERVIEW_CARDS = [
    # (key, label, [icon_paths], anim_translate, anim_delay)
    ("issues", "Issues", [ICON_ISSUES_1, ICON_ISSUES_2], "2.5%", "1.5s"),
    ("pullRequests", "Pull Requests", [ICON_PR_1, ICON_PR_2], "21.5%", "1.0s"),
    ("totalContributions", "Contributions", [ICON_CONTRIB], "40.5%", "0.5s"),
    ("repositories", "Repositories", [ICON_REPO_1, ICON_REPO_2], "59.5%", "1.0s"),
    ("stars", "Stars", [ICON_STAR], "78.5%", "1.5s"),
]

def keyframes(i: int, tr: str, delay: str) -> str:
    return (
        f'        @keyframes fade-in-slide-up-card{i} {{\n'
        f'            0% {{\n                transform: translate({tr}, 29.5%);\n                opacity: 0%;\n            }}\n'
        f'            67% {{\n                transform: translate({tr}, 24.5%);\n            }}\n'
        f'            100% {{\n                transform: translate({tr}, 24.5%);\n                opacity: 100%;\n            }}\n'
        f'        }}\n'
        f'        .card{i} {{\n            opacity: 0%;\n            animation: fade-in-slide-up-card{i} 1.375s forwards ease-out;\n        }}\n'
    )

def gen_overview(stats: dict) -> str:
    css = (
        '            ' + FONT_IMPORT + '\n'
        '            * {\n                font-family: "Rajdhani", "Trebuchet MS", sans-serif;\n            }\n'
        '            .overview-background {\n                opacity: 0%;\n'
        '                animation: fade-in-overview-background 0.75s forwards ease-in-out;\n'
        '                animation-delay: 0s;            }\n'
        '            @keyframes fade-in-overview-background {\n'
        '                0% {\n                    opacity: 0%;\n                }\n'
        '                100% {\n                    opacity: 100%;\n                }\n            }\n'
    )
    for i, (_, _, _, tr, _) in enumerate(OVERVIEW_CARDS):
        css += "\n" + keyframes(i, tr, "")
    cards = []
    for i, (key, label, icons, _, delay) in enumerate(OVERVIEW_CARDS):
        num = fmt_num(stats.get(key, 0))
        icon_paths = "".join(
            f'            <path fill-rule="evenodd" d="{p}">\n            </path>\n' for p in icons
        )
        cards.append(
            f'        <g class="card{i}" width="170.23999999999998px" height="256px" style="animation-delay: {delay}">\n'
            f'        <svg viewBox="0 0 24 24" width="76.8px" height="76.8px" x="46.71999999999999px" fill="{CP["cyan"]}">\n'
            f'{icon_paths}        </svg>\n'
            f'        <text y="107.52px" x="85.11999999999999px" font-size="30.72px" text-anchor="middle" fill="{CP["yellow"]}" font-family="{FONT_NUM}" font-weight="700" letter-spacing="1px" filter="url(#neonGlowY)">\n            {esc(num)}\n        </text>\n'
            f'        <text y="130.56px" x="85.11999999999999px" font-size="15.36px" text-anchor="middle" fill="{CP["cyan"]}" font-family="{FONT_BODY}" font-weight="500" letter-spacing="2px">\n            {esc(label)}\n        </text>\n'
            f'    </g>\n'
        )
    return (
        "<?xml version='1.0' encoding='utf-8'?>\n"
        '<svg xmlns="http://www.w3.org/2000/svg" width="896.0px" height="256px" viewBox="0 0 896.0 256">\n'
        "        <style>\n" + css + "        </style>\n"
        '        <svg width="896.0px" height="256px">\n'
        '            <defs>\n'
        '                <linearGradient id="overviewGradient" gradientTransform="rotate(90)">\n'
        f'                    <stop offset="0%" stop-color="{CP["grad_top"]}" stop-opacity="0.92" />\n'
        f'                    <stop offset="52%" stop-color="{CP["grad_mid"]}" stop-opacity="0.88" />\n'
        f'                    <stop offset="100%" stop-color="{CP["grad_bot"]}" stop-opacity="0.94" />\n'
        '                </linearGradient>\n'
        '                <filter id="neonGlowY" x="-20%" y="-20%" width="140%" height="140%">\n'
        f'                    <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="{CP["yellow"]}" flood-opacity="0.45" />\n'
        '                </filter>\n'
        '                <filter id="neonGlowC" x="-20%" y="-20%" width="140%" height="140%">\n'
        f'                    <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="{CP["cyan"]}" flood-opacity="0.35" />\n'
        '                </filter>\n'
        '                <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">\n'
        '                    <rect width="4" height="1" fill="#ffffff" opacity="0.04" />\n'
        '                </pattern>\n'
        f'                <clipPath id="clipBig"><path d="{PATH_BIG}" /></clipPath>\n'
        "            </defs>\n"
        f'            <path class="overview-background" d="{PATH_BIG}" fill="url(\'#overviewGradient\')" stroke="rgba(252,238,10,0.8)" stroke-width="1.5" clip-path="url(#clipBig)" mask="url(\'#overviewContents\')" />\n'
        f'            <path d="{PATH_BIG_INNER}" fill="none" stroke="{CP["cyan"]}" stroke-width="0.75" opacity="0.6" />\n'
        f'            <path d="{PATH_BIG}" fill="url(\'#scanlines\')" clip-path="url(#clipBig)" mask="url(\'#overviewContents\')" style="pointer-events:none" />\n'
        f'            <line x1="22" y1="0" x2="874" y2="0" stroke="{CP["yellow"]}" stroke-width="2" opacity="0.5" />\n'
        f'            <path d="{CORNER_TL}" fill="none" stroke="{CP["yellow"]}" stroke-width="3" />\n'
        f'            <path d="{CORNER_BR}" fill="none" stroke="{CP["yellow"]}" stroke-width="3" />\n'
        '            <mask id="overviewContents">\n'
        f'                <path d="{PATH_BIG}" fill="white" />\n'
        + "".join(cards)
        + "        </mask>\n        </svg>\n</svg>\n"
    )

# ---------------------------------------------------------------- repo 卡片
def gen_repo_card(repo: dict, index: int = 0) -> str:
    # 入场错峰:delay 随卡片在 repositories.txt 的序号递增(0.25s × (index+1)),内容组依次 +0.5s
    bg = 0.25 * (index + 1)
    g1 = bg + 0.5   # 图标/名称
    g2 = bg + 1.0   # 描述
    g3 = bg + 1.5   # 底部统计 + 语言色点
    f = lambda v: f"{v:g}s"
    grad_n = index // 2  # 渐变 translate 偏移按行递增(每行两张同值)
    name = repo.get("name", "")
    owner = repo.get("owner", "")
    desc_lines = wrap_desc(repo.get("description"))
    languages = repo.get("languages") or []
    stars = repo.get("stars", 0)
    forks = repo.get("forks", 0)

    fade_blocks = []
    # 图标 + 名称 + owner
    fade_blocks.append(
        f'        <g class="repo-info-fade" style="animation-delay: {f(g1)}">\n'
        f'        <svg fill="white" viewBox="0 0 24 24" width="36.48666666666667px" height="36.48666666666667px" x="8.0px" y="12.411666666666667px">\n'
        f'            <path fill-rule="evenodd" d="{ICON_REPO_1}">\n            </path>\n'
        f'            <path d="{ICON_REPO_2}">\n            </path>\n'
        f'        </svg>\n'
        f'            <text fill="white" x="52.90666666666667px" y="28.55px" width="396.0" height="21.05px" font-size="21.05px">\n                {esc(name)}\n            </text>\n'
        f'            <text fill="white" x="52.90666666666667px" y="43.98666666666667px" width="396.0" height="12.63px" font-size="12.63px">\n                {esc(owner)}\n            </text>\n'
        f'        </g>\n'
    )
    # 描述
    desc_block = f'    <g class="repo-info-fade" style="animation-delay: {f(g2)}">\n'
    y0 = 67.84333333333333
    for i, line in enumerate(desc_lines):
        y = y0 + 15.436666666666667 * i
        desc_block += (
            f'            <text fill="white" x="12.5px" y="{y}px" width="396.0" height="12.63px" font-size="12.63px">\n'
            f'                {esc(line)}\n            </text>\n'
        )
    desc_block += "        </g>"
    if desc_lines:
        fade_blocks.append(desc_block)
    # 底部统计(mask 内 g:语言名 + fork/star 数与图标)
    lang_names = ""
    for idx, lang in enumerate(languages[:2]):
        lx = 28.638333333333335 + idx * 129.68166666666666
        lang_names += (
            f'<text fill="white" x="{lx}px" y="123.51833333333335px" width="{max(6.5, len(lang.get("name",""))*6.50445):.4f}px" height="12.63px" font-size="12.63px" dominant-baseline="middle">\n                {esc(lang.get("name",""))}\n            </text>\n'
        )
    star_x = 335.01939999999996
    fork_x = 386.2972
    star_icon_x = 316.07439999999997
    fork_icon_x = 367.3522
    footer = (
        f'        <text fill="white" x="{fork_x}px" y="123.51833333333335px" width="{max(6.5, len(str(forks))*6.5676):.4f}px" height="15.436666666666667px" font-size="12.63px" dominant-baseline="middle">\n                    {esc(str(forks))}\n                </text>\n'
        f'        <svg fill="white" viewBox="0 0 24 24" width="15.436666666666667px" height="15.436666666666667px" x="{fork_icon_x}px" y="114.80000000000001px">\n'
        f'            <path fill-rule="evenodd" d="{ICON_FORK_1}" /><path fill-rule="evenodd" d="{ICON_FORK_2}"></path><path fill-rule="evenodd" d="{ICON_FORK_3}">\n            </path>\n'
        f'        </svg>\n'
        f'                <text fill="white" x="{star_x}px" y="123.51833333333335px" width="{max(6.5, len(str(stars))*6.5676):.4f}px" height="15.436666666666667px" font-size="12.63px" dominant-baseline="middle">\n                    {esc(str(stars))}\n                </text>\n'
        f'        <svg fill="white" viewBox="0 0 24 24" width="15.436666666666667px" height="15.436666666666667px" x="{star_icon_x}px" y="114.80000000000001px">\n'
        f'            <path fill-rule="evenodd" d="{ICON_STAR}">\n            </path>\n'
        f'        </svg>\n'
    )
    if languages:
        fade_blocks.append(
            f'    <g class="repo-info-fade" style="animation-delay: {f(g3)}">\n{lang_names}{footer}    </g>'
        )
    else:
        fade_blocks.append(f'    <g class="repo-info-fade" style="animation-delay: {f(g3)}">\n{footer}    </g>')

    # 语言色点:必须在 mask 外(与原版一致),否则作为遮罩不会显示彩色
    lang_circles = ""
    for idx, lang in enumerate(languages[:2]):
        cx = 18.815 + idx * 129.68166666666666
        color = lang.get("color", "#cccccc")
        lang_circles += f'<circle cx="{cx}px" cy="122.51833333333335px" r="6.315px" fill="{color}" opacity="65%" />'

    body = "".join(fade_blocks)
    return (
        "<?xml version='1.0' encoding='utf-8'?>\n"
        '<svg xmlns="http://www.w3.org/2000/svg" width="421px" height="140.33333333333334px" viewBox="0 0 421 140.33333333333334">\n'
        "        <style>\n"
        '            * {\n                font-family: "Trebuchet MS", sans-serif;\n            }\n'
        "            @keyframes repo-info-fade-in {\n                0% {\n                    opacity: 0%;\n                }\n                100% {\n                    opacity: 100%;\n                }\n            }\n"
        "            .repo-info-fade {\n                opacity: 0%;\n                animation: repo-info-fade-in 1.25s forwards ease-out;\n            }\n"
        "            .repo-info-background-fade {\n                opacity: 0%;\n                animation: repo-info-fade-in 1.25s forwards ease-in-out;\n            }\n"
        "        </style>\n"
        "        <defs>\n"
        f'            <linearGradient id="repoInfoGradient" gradientTransform="rotate(90) translate(-{grad_n},0) scale(4,2)">\n'
        '                <stop offset="0%" stop-color="#0a0a0a" stop-opacity="0.84" />\n'
        '                <stop offset="52%" stop-color="#2a2a2a" stop-opacity="0.54" />\n'
        '                <stop offset="100%" stop-color="#6b7280" stop-opacity="0.34" />\n'
        '            </linearGradient>\n'
        '            <linearGradient id="cardHighlight" gradientTransform="rotate(90)">\n'
        '                <stop offset="0%" stop-color="#ffffff" stop-opacity="0.18" />\n'
        '                <stop offset="20%" stop-color="#ffffff" stop-opacity="0.05" />\n'
        '                <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />\n'
        '            </linearGradient>\n'
        '            <filter id="cardShadow" x="-8%" y="-8%" width="116%" height="116%">\n'
        '                <feDropShadow dx="0" dy="3" stdDeviation="10" flood-color="#0a0a0a" flood-opacity="0.22" />\n'
        '            </filter>\n'
        "        </defs>\n"
        '        <rect width="421px" height="140.33333333333334px" rx="15px" fill="#0d1117" opacity="0.0" />\n'
        '        <rect class="repo-info-background-fade" style="animation-delay: ' + f(bg) + '" width="421px" height="140.33333333333334px" rx="15px" fill="url(\'#repoInfoGradient\')" stroke="rgba(255,255,255,0.13)" stroke-width="1.1" filter="url(#cardShadow)" mask="url(\'#repoContents\')" />\n'
        '        <rect width="421px" height="140.33333333333334px" rx="15px" fill="url(\'#cardHighlight\')" opacity="0.9" mask="url(\'#repoContents\')" style="pointer-events:none" />\n'
        '        <mask id="repoContents">\n'
        '            <rect width="421px" height="140.33333333333334px" rx="15px" fill="white" />\n'
        + body
        + "\n        </mask>"
        + f'<g class="repo-info-fade" style="animation-delay: {f(g3)}">{lang_circles}</g>'
        + "\n</svg>\n"
    )

# ---------------------------------------------------------------- README
def gen_readme(repo_list: list) -> str:
    lines = ['<div align="center">']
    lines.append(
        f'    <a href="https://github.com/{OWNER}/{REPO}"><img src="{RAW_BASE}/overview.svg" width="100.00%" /></a>'
    )
    row = []
    for owner, name in repo_list:
        card = (
            f'<a href="https://github.com/{owner}/{name}">'
            f'<img src="{RAW_BASE}/repositories/{owner}/{name}.svg" width="49.68%" /></a>'
        )
        if len(row) == 1:
            row.append(card)
            lines.append("    " + row[0] + f'<a href="#"><img src="{RAW_BASE}/spacer.svg" width="0.64%" /></a>' + row[1])
            row = []
        else:
            row.append(card)
    if row:  # 奇数个,补 spacer
        lines.append("    " + row[0] + f'<a href="#"><img src="{RAW_BASE}/spacer.svg" width="0.64%" /></a>')
    lines.append(
        f'    <a href="https://github.com/{OWNER}/{REPO}"><img src="{RAW_BASE}/footer.svg" width="100.00%" /></a>'
    )
    lines.append("</div>")
    return "\n".join(lines) + "\n"

# ---------------------------------------------------------------- main
def main():
    with open(os.path.join(OUTPUT_DIR, "stats.json")) as f:
        stats = json.load(f)

    repo_list = []
    with open("repositories.txt") as f:
        for line in f:
            line = line.strip()
            if line and "/" in line:
                repo_list.append(tuple(line.split("/", 1)))

    os.makedirs(os.path.join(OUTPUT_DIR, "repositories"), exist_ok=True)

    with open(os.path.join(OUTPUT_DIR, "overview.svg"), "w") as f:
        f.write(gen_overview(stats).rstrip("\n"))

    for index, (owner, name) in enumerate(repo_list):
        json_path = os.path.join(OUTPUT_DIR, "repositories", owner, name + ".json")
        if not os.path.exists(json_path):
            print(f"[skip] 缺少 {json_path}")
            continue
        with open(json_path) as f:
            repo = json.load(f)
        out_dir = os.path.join(OUTPUT_DIR, "repositories", owner)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, name + ".svg"), "w") as f:
            f.write(gen_repo_card(repo, index).rstrip("\n"))

    with open("generated_readme.md", "w") as f:
        f.write(gen_readme(repo_list))

    print(f"[ok] overview.svg + {len(repo_list)} 张仓库卡片 + generated_readme.md 已生成")


if __name__ == "__main__":
    main()
