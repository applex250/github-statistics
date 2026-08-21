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

def ghost_paths(icons: list) -> str:
    """图标 markup:先输出品红故障重影层(偏移+降透明),再输出继承青色的主层。"""
    out = ""
    for p in icons:
        out += (
            f'            <path fill-rule="evenodd" d="{p}" fill="{CP["magenta"]}" '
            f'opacity="0.55" transform="translate(0.7,-0.5)" />\n'
        )
    for p in icons:
        out += f'            <path fill-rule="evenodd" d="{p}">\n            </path>\n'
    return out

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

# ---------------------------------------------------------------- 图标 path(CP2077 手绘几何风)
# Issues:切角警示三角 + 感叹号 + 边框故障缺口
ICON_ISSUES = (
    "M11.0,3.9 L13.0,3.9 L21.26,19.6 L20.6,21 L3.4,21 L2.74,19.6 Z "
    "M11.37,7.4 L12.63,7.4 L18.42,18.0 L18.0,18.7 L6.0,18.7 L5.58,18.0 Z "
    "M11.15,9.2 L12.85,9.2 L12.85,14.6 L11.15,14.6 Z "
    "M12,15.95 L12.74,16.26 L13.05,17 L12.74,17.74 L12,18.05 L11.26,17.74 L10.95,17 L11.26,16.26 Z "
    "M5.5,13.5 L9.5,11.5 L9.5,12.6 L5.5,14.6 Z "
    "M16.5,17.3 L20.0,15.7 L20.0,16.7 L16.5,18.3 Z"
)
# Pull Requests:双向切角数据交换箭头 + 电路焊盘
ICON_PULLREQS = (
    "M3,6.4 L13.5,6.4 L13.5,4.4 L18.9,7.49 L18.9,8.51 L13.5,11.6 L13.5,9.6 L3,9.6 Z "
    "M21,14.4 L10.5,14.4 L10.5,12.4 L5.1,15.49 L5.1,16.51 L10.5,19.6 L10.5,17.6 L21,17.6 Z "
    "M3,6.5 L4.06,7.06 L4.5,8 L4.06,8.94 L3,9.5 L1.94,8.94 L1.5,8 L1.94,7.06 Z "
    "M21,14.5 L22.06,15.06 L22.5,16 L22.06,16.94 L21,17.5 L19.94,16.94 L19.5,16 L19.94,15.06 Z"
)
# Contributions:义体芯片(切角方框 + 引脚 + 脉冲折线)
ICON_CONTRIB = (
    "M8.6,7 L15.4,7 L17,8.6 L17,15.4 L15.4,17 L8.6,17 L7,15.4 L7,8.6 Z "
    "M10.2,9.2 L13.8,9.2 L14.8,10.2 L14.8,13.8 L13.8,14.8 L10.2,14.8 L9.2,13.8 L9.2,10.2 Z "
    "M9.4,4.2 L10.8,4.2 L10.8,7 L9.4,7 Z M13.2,4.2 L14.6,4.2 L14.6,7 L13.2,7 Z "
    "M9.4,17 L10.8,17 L10.8,19.8 L9.4,19.8 Z M13.2,17 L14.6,17 L14.6,19.8 L13.2,19.8 Z "
    "M4.2,9.4 L7,9.4 L7,10.8 L4.2,10.8 Z M4.2,13.2 L7,13.2 L7,14.6 L4.2,14.6 Z "
    "M17,9.4 L19.8,9.4 L19.8,10.8 L17,10.8 Z M17,13.2 L19.8,13.2 L19.8,14.6 L17,14.6 Z "
    "M9.7,11.7 L11.1,11.7 L11.9,10.0 L13.0,13.4 L13.7,11.7 L14.3,11.7 "
    "L14.3,12.8 L13.7,12.8 L13.0,14.5 L11.9,11.1 L11.1,12.8 L9.7,12.8 Z"
)
# Repositories:三层切角存储盘片 + LED 指示孔
ICON_REPOS = (
    "M4.9,3.5 L20.5,3.5 L20.5,5.7 L19.1,7.1 L3.5,7.1 L3.5,4.9 Z "
    "M17.2,4.65 L18.6,4.65 L18.6,5.95 L17.2,5.95 Z "
    "M4.9,10.2 L20.5,10.2 L20.5,12.4 L19.1,13.8 L3.5,13.8 L3.5,11.6 Z "
    "M17.2,11.35 L18.6,11.35 L18.6,12.65 L17.2,12.65 Z "
    "M4.9,16.9 L20.5,16.9 L20.5,19.1 L19.1,20.5 L3.5,20.5 L3.5,18.3 Z "
    "M17.2,18.05 L18.6,18.05 L18.6,19.35 L17.2,19.35 Z"
)
# Stars:四芒星火花 + 双伴星
ICON_STAR = (
    "M12,2.5 L14.26,9.74 L21.5,12 L14.26,14.26 L12,21.5 L9.74,14.26 L2.5,12 L9.74,9.74 Z "
    "M19.5,2.8 L20.07,4.43 L21.7,5.0 L20.07,5.57 L19.5,7.2 L18.93,5.57 L17.3,5.0 L18.93,4.43 Z "
    "M5,17.4 L5.42,18.58 L6.6,19 L5.42,19.42 L5,20.6 L4.58,19.42 L3.4,19 L4.58,18.58 Z"
)
# Fork:直角电路分支 + 焊盘
ICON_FORK = (
    "M11.3,4.5 L12.7,4.5 L12.7,10 L11.3,10 Z "
    "M5.5,10 L18.5,10 L18.5,11.4 L5.5,11.4 Z "
    "M5.5,11.4 L6.9,11.4 L6.9,16.5 L5.5,16.5 Z "
    "M17.1,11.4 L18.5,11.4 L18.5,16.5 L17.1,16.5 Z "
    "M12,2.9 L13.13,3.37 L13.6,4.5 L13.13,5.63 L12,6.1 L10.87,5.63 L10.4,4.5 L10.87,3.37 Z "
    "M6.2,16.5 L7.33,16.97 L7.8,18.1 L7.33,19.23 L6.2,19.7 L5.07,19.23 L4.6,18.1 L5.07,16.97 Z "
    "M17.8,16.5 L18.93,16.97 L19.4,18.1 L18.93,19.23 L17.8,19.7 L16.67,19.23 L16.2,18.1 L16.67,16.97 Z"
)
# Repo:切角六边形 + 终端提示符
ICON_REPO = (
    "M21.5,12 L16.75,20.23 L7.25,20.23 L2.5,12 L7.25,3.77 L16.75,3.77 Z "
    "M9,8 L14.6,12 L9,16 L9,13.7 L11.4,12 L9,10.3 Z "
    "M15.2,14 L17.6,14 L17.6,15.8 L15.2,15.8 Z"
)

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
    "&amp;family=Rajdhani:wght@400;500;600&amp;display=swap');"
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
    ("issues", "Issues", [ICON_ISSUES], "2.5%", "1.5s"),
    ("pullRequests", "Pull Requests", [ICON_PULLREQS], "21.5%", "1.0s"),
    ("totalContributions", "Contributions", [ICON_CONTRIB], "40.5%", "0.5s"),
    ("repositories", "Repositories", [ICON_REPOS], "59.5%", "1.0s"),
    ("stars", "Stars", [ICON_STAR], "78.5%", "1.5s"),
]

def keyframes(i: int, tr: str, delay: str) -> str:
    # 每张总览子卡独立 keyframes:前缀唯一 + 互异入场动效
    # 0:glitch 故障闪烁  1:右滑入  2:弹跳上抛  3:左滑入  4:顶部坠落
    if i == 0:
        return (
            f'        @keyframes anim-card{i} {{\n'
            f'            0% {{ opacity: 0%; }}\n'
            f'            18% {{ opacity: 100%; transform: translate({tr},0); }}\n'
            f'            30% {{ opacity: 25%; transform: translate({tr},0) translateX(-6px); }}\n'
            f'            42% {{ opacity: 100%; transform: translate({tr},0) translateX(6px); }}\n'
            f'            54% {{ opacity: 30%; transform: translate({tr},0) translateX(-3px); }}\n'
            f'            70% {{ opacity: 100%; transform: translate({tr},0); }}\n'
            f'            100% {{ opacity: 100%; transform: translate({tr},0); }}\n'
            f'        }}\n'
            f'        .card{i} {{\n            opacity: 0%;\n            animation: anim-card{i} 1.8s forwards steps(1,end);\n        }}\n'
        )
    if i == 1:
        return (
            f'        @keyframes anim-card{i} {{\n'
            f'            0% {{ opacity: 0%; transform: translate({tr},0) translateX(60px); }}\n'
            f'            100% {{ opacity: 100%; transform: translate({tr},0) translateX(0); }}\n'
            f'        }}\n'
            f'        .card{i} {{\n            opacity: 0%;\n            animation: anim-card{i} 1.375s forwards ease-out;\n        }}\n'
        )
    if i == 2:
        return (
            f'        @keyframes anim-card{i} {{\n'
            f'            0% {{ opacity: 0%; transform: translate({tr},0) translateY(40px); }}\n'
            f'            60% {{ opacity: 100%; transform: translate({tr},0) translateY(-10px); }}\n'
            f'            80% {{ transform: translate({tr},0) translateY(4px); }}\n'
            f'            100% {{ opacity: 100%; transform: translate({tr},0) translateY(0); }}\n'
            f'        }}\n'
            f'        .card{i} {{\n            opacity: 0%;\n            animation: anim-card{i} 1.5s forwards cubic-bezier(.28,.84,.42,1);\n        }}\n'
        )
    if i == 3:
        return (
            f'        @keyframes anim-card{i} {{\n'
            f'            0% {{ opacity: 0%; transform: translate({tr},0) translateX(-60px); }}\n'
            f'            100% {{ opacity: 100%; transform: translate({tr},0) translateX(0); }}\n'
            f'        }}\n'
            f'        .card{i} {{\n            opacity: 0%;\n            animation: anim-card{i} 1.375s forwards ease-out;\n        }}\n'
        )
    # i == 4 顶部坠落
    return (
        f'        @keyframes anim-card{i} {{\n'
        f'            0% {{ opacity: 0%; transform: translate({tr},0) translateY(-50px); }}\n'
        f'            100% {{ opacity: 100%; transform: translate({tr},0) translateY(0); }}\n'
        f'        }}\n'
        f'        .card{i} {{\n            opacity: 0%;\n            animation: anim-card{i} 1.375s forwards ease-in;\n        }}\n'
    )

# ---------------------------------------------------------------- 常态持续(idle)动效
# 每张卡入场动画一次后,idle 层持续循环;两类互不抢同一个 animation 属性(挂不同元素)
OVERVIEW_IDLE = {0: "vbeam", 1: "breathe", 2: "flick", 3: "float", 4: "pulse"}
REPO_IDLE = {0: "hbeam", 1: "gflick", 2: "breathe", 3: "float", 4: "bflash", 5: "hbeamy"}
# 总览 5 子卡横向 band 左边界(宽 170)
OV_BAND = [22, 193, 363, 534, 704]

def overview_idle_css() -> str:
    s = ""
    # 0 竖向扫描光束
    s += ('            @keyframes idle-vbeam { 0%{transform:translateY(-256px)} 100%{transform:translateY(256px)} }\n'
          '            .idle-vbeam { animation: idle-vbeam 2.4s linear infinite; }\n')
    # 1 边框呼吸
    s += ('            @keyframes idle-breathe { 0%,100%{opacity:0.12} 50%{opacity:0.85} }\n'
          '            .idle-breathe { animation: idle-breathe 2.2s ease-in-out infinite; }\n')
    # 2 图标故障闪
    s += ('            @keyframes idle-flick { 0%{opacity:1} 7%{opacity:0.25} 9%{opacity:1} 38%{opacity:0.5} 41%{opacity:1} 70%{opacity:0.3} 73%{opacity:1} 100%{opacity:1} }\n'
          '            .idle-flick { animation: idle-flick 3.2s steps(1,end) infinite; }\n')
    # 3 图标浮动
    s += ('            @keyframes idle-float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-7px)} }\n'
          '            .idle-float { animation: idle-float 2.6s ease-in-out infinite; }\n')
    # 4 顶部辉光脉冲
    s += ('            @keyframes idle-pulse { 0%,100%{opacity:0.2} 50%{opacity:0.95} }\n'
          '            .idle-pulse { animation: idle-pulse 1.8s ease-in-out infinite; }\n')
    return s

def overview_idle_deco(i: int) -> str:
    left = OV_BAND[i]
    if OVERVIEW_IDLE[i] == "vbeam":
        return (f'        <g clip-path="url(#clipBig)"><rect class="idle-vbeam" x="{left+82}px" y="0" width="5px" height="256px" fill="{CP["cyan"]}" opacity="0.45" /></g>\n')
    if OVERVIEW_IDLE[i] == "breathe":
        return (f'        <rect class="idle-breathe" x="{left+2}px" y="3px" width="166px" height="250px" fill="none" stroke="{CP["yellow"]}" stroke-width="1.5" />\n')
    if OVERVIEW_IDLE[i] == "pulse":
        return (f'        <line class="idle-pulse" x1="{left+22}px" y1="0" x2="{left+148}px" y2="0" stroke="{CP["yellow"]}" stroke-width="3" />\n')
    # flick / float 作用在图标元素本身(在卡片组内加 class),此处不另加装饰
    return ""

def repo_idle_css() -> str:
    s = ""
    # 横向扫描光束(青)
    s += ('            @keyframes idle-hbeam { 0%{transform:translateX(0)} 100%{transform:translateX(407px)} }\n'
          '            .idle-hbeam { animation: idle-hbeam 2.8s linear infinite; }\n')
    # 横向扫描光束(黄,反向相位)
    s += ('            @keyframes idle-hbeamy { 0%{transform:translateX(407px)} 100%{transform:translateX(0)} }\n'
          '            .idle-hbeamy { animation: idle-hbeamy 3.1s linear infinite; }\n')
    # 故障闪(品红)
    s += ('            @keyframes idle-gflick { 0%{opacity:0.3} 6%{opacity:1} 8%{opacity:0.3} 36%{opacity:1} 39%{opacity:0.25} 66%{opacity:1} 69%{opacity:0.4} 100%{opacity:0.3} }\n'
          '            .idle-gflick { animation: idle-gflick 3.4s steps(1,end) infinite; }\n')
    # 边框呼吸(黄)
    s += ('            @keyframes idle-breathe-r { 0%,100%{opacity:0.12} 50%{opacity:0.8} }\n'
          '            .idle-breathe-r { animation: idle-breathe-r 2.3s ease-in-out infinite; }\n')
    # 边框流光闪
    s += ('            @keyframes idle-bflash { 0%,92%{opacity:0.15} 95%{opacity:0.9} 97%{opacity:0.2} 100%{opacity:0.15} }\n'
          '            .idle-bflash { animation: idle-bflash 2.0s steps(1,end) infinite; }\n')
    return s

def repo_idle_deco(idx: int) -> str:
    kind = REPO_IDLE[idx]
    if kind == "hbeam":
        return f'        <g clip-path="url(#clipSmall)"><rect class="idle-hbeam" x="0" y="0" width="16px" height="140px" fill="{CP["cyan"]}" opacity="0.4" /></g>\n'
    if kind == "hbeamy":
        return f'        <g clip-path="url(#clipSmall)"><rect class="idle-hbeamy" x="0" y="0" width="16px" height="140px" fill="{CP["yellow"]}" opacity="0.4" /></g>\n'
    if kind == "gflick":
        return f'        <rect class="idle-gflick" x="3px" y="3px" width="415px" height="134px" fill="none" stroke="{CP["magenta"]}" stroke-width="1" />\n'
    if kind == "breathe":
        return f'        <rect class="idle-breathe-r" x="3px" y="3px" width="415px" height="134px" fill="none" stroke="{CP["yellow"]}" stroke-width="1.5" />\n'
    if kind == "bflash":
        return f'        <rect class="idle-bflash" x="3px" y="3px" width="415px" height="134px" fill="none" stroke="{CP["cyan"]}" stroke-width="1.5" />\n'
    return ""

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
    css += "\n" + overview_idle_css()
    cards = []
    for i, (key, label, icons, _, delay) in enumerate(OVERVIEW_CARDS):
        num = fmt_num(stats.get(key, 0))
        idle_cls = "idle-flick" if OVERVIEW_IDLE[i] == "flick" else ("idle-float" if OVERVIEW_IDLE[i] == "float" else "")
        icon_paths = ghost_paths(icons)
        cards.append(
            f'        <g class="card{i}" width="170.23999999999998px" height="256px" style="animation-delay: {delay}">\n'
            f'        <svg class="{idle_cls}" viewBox="0 0 24 24" width="76.8px" height="76.8px" x="46.71999999999999px" y="18px" fill="{CP["cyan"]}">\n'
            f'{icon_paths}        </svg>\n'
            f'        <text y="125.52px" x="85.11999999999999px" font-size="30.72px" text-anchor="middle" fill="{CP["yellow"]}" font-family="{FONT_NUM}" font-weight="700" letter-spacing="1px" filter="url(#neonGlowY)">\n            {esc(num)}\n        </text>\n'
            f'        <text y="148.56px" x="85.11999999999999px" font-size="15.36px" text-anchor="middle" fill="{CP["cyan"]}" font-family="{FONT_BODY}" font-weight="500" letter-spacing="2px">\n            {esc(label)}\n        </text>\n'
            f'    </g>\n'
        )
    idle_decos = "".join(overview_idle_deco(i) for i in range(5))
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
        '            </mask>\n'
        + idle_decos
        + "".join(cards)
        + "        </svg>\n</svg>\n"
    )

# ---------------------------------------------------------------- repo 卡片
REPO_ANIMS = [
    # (name, css_keyframes(index_unused, tr_placeholder), animation_class)
    # 6 张仓库卡各一种,均与总览 5 种不重复
    "slide-up",    # 0 上滑入
    "glitch",      # 1 故障闪烁
    "slide-right", # 2 右侧滑入
    "slide-left",  # 3 左侧滑入
    "bounce",      # 4 弹跳回弹
    "drop",        # 5 顶部坠落
]

def repo_keyframes(cls: str, idx: int) -> str:
    """返回单张仓库卡的 @keyframes + class 定义(前缀含 idx 保证唯一)"""
    n = f"repo{idx}"
    if cls == "slide-up":
        return (f'            @keyframes {n} {{ 0%{{opacity:0%;transform:translateY(28px)}} '
                f'100%{{opacity:100%;transform:translateY(0)}} }}\n'
                f'            .{n} {{ opacity:0%; animation:{n} 1.3s forwards ease-out; }}\n')
    if cls == "glitch":
        return (f'            @keyframes {n} {{ 0%{{opacity:0%}} 20%{{opacity:100%}} '
                f'34%{{opacity:20%;transform:translateX(-5px)}} 48%{{opacity:100%;transform:translateX(5px)}} '
                f'62%{{opacity:30%}} 80%{{opacity:100%}} 100%{{opacity:100%}} }}\n'
                f'            .{n} {{ opacity:0%; animation:{n} 1.8s forwards steps(1,end); }}\n')
    if cls == "slide-right":
        return (f'            @keyframes {n} {{ 0%{{opacity:0%;transform:translateX(70px)}} '
                f'100%{{opacity:100%;transform:translateX(0)}} }}\n'
                f'            .{n} {{ opacity:0%; animation:{n} 1.3s forwards ease-out; }}\n')
    if cls == "slide-left":
        return (f'            @keyframes {n} {{ 0%{{opacity:0%;transform:translateX(-70px)}} '
                f'100%{{opacity:100%;transform:translateX(0)}} }}\n'
                f'            .{n} {{ opacity:0%; animation:{n} 1.3s forwards ease-out; }}\n')
    if cls == "bounce":
        return (f'            @keyframes {n} {{ 0%{{opacity:0%;transform:translateY(36px)}} '
                f'55%{{opacity:100%;transform:translateY(-12px)}} 78%{{transform:translateY(5px)}} '
                f'100%{{opacity:100%;transform:translateY(0)}} }}\n'
                f'            .{n} {{ opacity:0%; animation:{n} 1.5s forwards cubic-bezier(.28,.84,.42,1); }}\n')
    # drop
    return (f'            @keyframes {n} {{ 0%{{opacity:0%;transform:translateY(-50px)}} '
            f'100%{{opacity:100%;transform:translateY(0)}} }}\n'
            f'            .{n} {{ opacity:0%; animation:{n} 1.3s forwards ease-in; }}\n')

def gen_repo_card(repo: dict, index: int = 0) -> str:
    # 每张仓库卡:独立入场动效(cls 按 index 取,各不相同),内容组入场做轻微错峰
    cls = REPO_ANIMS[index % len(REPO_ANIMS)]
    anim_cls = f"repo{index}"
    # 入场错峰:delay 随卡片序号递增(0.25s × (index+1)),内容组依次 +0.5s
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

    icon_idle = ' class="idle-float"' if REPO_IDLE[index] == "float" else ""
    fade_blocks = []
    # 图标 + 名称 + owner (全体内容由 return 处的 translate(0,10) 统一下移)
    fade_blocks.append(
        f'        <g class="repo-info-fade" style="animation-delay: {f(g1)}">\n'
        f'        <svg{icon_idle} fill="{CP["cyan"]}" viewBox="0 0 24 24" width="36.48666666666667px" height="36.48666666666667px" x="8.0px" y="12.411666666666667px">\n'
        f'{ghost_paths([ICON_REPO])}        </svg>\n'
        f'            <text fill="{CP["yellow"]}" font-family="{FONT_NUM}" font-weight="500" letter-spacing="0.5px" x="52.90666666666667px" y="28.55px" width="396.0" height="21.05px" font-size="21.05px" filter="url(#neonGlowY)">\n                {esc(name)}\n            </text>\n'
        f'            <text fill="{CP["cyan"]}" font-family="{FONT_BODY}" x="52.90666666666667px" y="43.98666666666667px" width="396.0" height="12.63px" font-size="12.63px">\n                {esc(owner)}\n            </text>\n'
        f'        </g>\n'
    )
    # 描述
    desc_block = f'    <g class="repo-info-fade" style="animation-delay: {f(g2)}">\n'
    y0 = 67.84333333333333
    for i, line in enumerate(desc_lines):
        y = y0 + 15.436666666666667 * i
        desc_block += (
            f'            <text fill="{CP["cyan"]}" font-family="{FONT_BODY}" x="12.5px" y="{y}px" width="396.0" height="12.63px" font-size="12.63px">\n'
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
            f'<text fill="{CP["text_dim"]}" font-family="{FONT_BODY}" x="{lx}px" y="123.51833333333335px" width="{max(6.5, len(lang.get("name",""))*6.50445):.4f}px" height="12.63px" font-size="12.63px" dominant-baseline="middle">\n                {esc(lang.get("name",""))}\n            </text>\n'
        )
    star_x = 335.01939999999996
    fork_x = 386.2972
    star_icon_x = 316.07439999999997
    fork_icon_x = 367.3522
    footer = (
        f'        <text fill="{CP["yellow"]}" font-family="{FONT_NUM}" font-weight="500" x="{fork_x}px" y="123.51833333333335px" width="{max(6.5, len(str(forks))*6.5676):.4f}px" height="15.436666666666667px" font-size="12.63px" dominant-baseline="middle">\n                    {esc(str(forks))}\n                </text>\n'
        f'        <svg fill="{CP["cyan"]}" viewBox="0 0 24 24" width="15.436666666666667px" height="15.436666666666667px" x="{fork_icon_x}px" y="114.80000000000001px">\n'
        f'{ghost_paths([ICON_FORK])}        </svg>\n'
        f'                <text fill="{CP["yellow"]}" font-family="{FONT_NUM}" font-weight="500" x="{star_x}px" y="123.51833333333335px" width="{max(6.5, len(str(stars))*6.5676):.4f}px" height="15.436666666666667px" font-size="12.63px" dominant-baseline="middle">\n                    {esc(str(stars))}\n                </text>\n'
        f'        <svg fill="{CP["cyan"]}" viewBox="0 0 24 24" width="15.436666666666667px" height="15.436666666666667px" x="{star_icon_x}px" y="114.80000000000001px">\n'
        f'{ghost_paths([ICON_STAR])}        </svg>\n'
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
        '            ' + FONT_IMPORT + '\n'
        '            * {\n                font-family: "Rajdhani", "Trebuchet MS", sans-serif;\n            }\n'
        "            @keyframes repo-info-fade-in {\n                0% {\n                    opacity: 0%;\n                }\n                100% {\n                    opacity: 100%;\n                }\n            }\n"
        "            .repo-info-fade {\n                opacity: 0%;\n                animation: repo-info-fade-in 1.25s forwards ease-out;\n            }\n"
        "            .repo-info-background-fade {\n                opacity: 0%;\n                animation: repo-info-fade-in 1.25s forwards ease-in-out;\n            }\n"
        + repo_keyframes(cls, index)
        + repo_idle_css()
        + "        </style>\n"
        "        <defs>\n"
        f'            <linearGradient id="repoInfoGradient" gradientTransform="rotate(90) translate(-{grad_n},0) scale(4,2)">\n'
        f'                <stop offset="0%" stop-color="{CP["grad_top"]}" stop-opacity="0.92" />\n'
        f'                <stop offset="52%" stop-color="{CP["grad_mid"]}" stop-opacity="0.88" />\n'
        f'                <stop offset="100%" stop-color="{CP["grad_bot"]}" stop-opacity="0.94" />\n'
        '            </linearGradient>\n'
        '                <filter id="neonGlowY" x="-20%" y="-20%" width="140%" height="140%">\n'
        f'                    <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="{CP["yellow"]}" flood-opacity="0.45" />\n'
        '                </filter>\n'
        '                <filter id="neonGlowC" x="-20%" y="-20%" width="140%" height="140%">\n'
        f'                    <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="{CP["cyan"]}" flood-opacity="0.35" />\n'
        '                </filter>\n'
        '                <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">\n'
        '                    <rect width="4" height="1" fill="#ffffff" opacity="0.04" />\n'
        '                </pattern>\n'
        f'                <clipPath id="clipSmall"><path d="{PATH_SMALL}" /></clipPath>\n'
        "        </defs>\n"
        f'            <path class="{anim_cls}" style="animation-delay: ' + f(bg) + f'" d="{PATH_SMALL}" fill="url(\'#repoInfoGradient\')" stroke="rgba(252,238,10,0.7)" stroke-width="1.2" clip-path="url(#clipSmall)" mask="url(\'#repoContents\')" />\n'
        f'            <path d="{PATH_SMALL_INNER}" fill="none" stroke="{CP["cyan"]}" stroke-width="0.75" opacity="0.6" />\n'
        f'            <path d="{PATH_SMALL}" fill="url(\'#scanlines\')" clip-path="url(#clipSmall)" mask="url(\'#repoContents\')" style="pointer-events:none" />\n'
        f'            <line x1="22" y1="0" x2="399" y2="0" stroke="{CP["yellow"]}" stroke-width="2" opacity="0.5" />\n'
        f'            <path d="{CORNER_TL}" fill="none" stroke="{CP["yellow"]}" stroke-width="3" />\n'
        f'            <path d="{CORNER_BR_S}" fill="none" stroke="{CP["yellow"]}" stroke-width="3" />\n'
        '            <mask id="repoContents">\n'
        f'                <path d="{PATH_SMALL}" fill="white" />\n'
        '            </mask>\n'
        + repo_idle_deco(index)
        + f'<g transform="translate(0,10)">'
        + body
        + f'<g class="repo-info-fade" style="animation-delay: {f(g3)}">{lang_circles}</g>'
        + '</g>'
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
    with open(os.path.join(OUTPUT_DIR, "stats.json"), encoding="utf-8") as f:
        stats = json.load(f)

    repo_list = []
    with open("repositories.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "/" in line:
                repo_list.append(tuple(line.split("/", 1)))

    os.makedirs(os.path.join(OUTPUT_DIR, "repositories"), exist_ok=True)

    with open(os.path.join(OUTPUT_DIR, "overview.svg"), "w", encoding="utf-8") as f:
        f.write(gen_overview(stats).rstrip("\n"))

    for index, (owner, name) in enumerate(repo_list):
        json_path = os.path.join(OUTPUT_DIR, "repositories", owner, name + ".json")
        if not os.path.exists(json_path):
            print(f"[skip] 缺少 {json_path}")
            continue
        with open(json_path, encoding="utf-8") as f:
            repo = json.load(f)
        out_dir = os.path.join(OUTPUT_DIR, "repositories", owner)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, name + ".svg"), "w", encoding="utf-8") as f:
            f.write(gen_repo_card(repo, index).rstrip("\n"))

    with open("generated_readme.md", "w", encoding="utf-8") as f:
        f.write(gen_readme(repo_list))

    print(f"[ok] overview.svg + {len(repo_list)} 张仓库卡片 + generated_readme.md 已生成")


if __name__ == "__main__":
    main()
