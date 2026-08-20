#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Profile README 生成器 — 完全重构版
- 不再生成旧式渐变 SVG 卡片
- 完全复用 https://applex250.github.io/random-web-20260820-fd964c0e/ 的 HTML 写法：
  surface / border / text 变量、Harness 留白、卡片 24px 圆角、Fragment Mono 小标
- GitHub README 仅支持有限 HTML/CSS（不支持 backdrop-filter），用半透明 + 细边模拟毛玻璃
"""
import json, os, html, pathlib

OWNER = "applex250"
REPO  = "github-statistics"
STATS_PATH = "output/stats.json"

CSS = """
<style>
.profile-wrap{max-width:896px;margin:0 auto;font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif;}
.profile-head{padding:22px 4px 8px;text-align:left}
.profile-kpi{font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:10px; letter-spacing:.16em; text-transform:uppercase; color:#636c76}
.profile-title{margin:8px 0 0; font-size:22px; font-weight:600; letter-spacing:-0.02em; line-height:1.2}
.profile-desc{margin:8px 0 0; font-size:13px; color:#636c76; line-height:1.6}
.stats-row{display:flex;gap:12px;flex-wrap:wrap;margin-top:16px}
.stat{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:14px 16px;flex:1 1 120px;min-width:120px}
.stat b{font-size:18px;font-weight:600}
.stat span{font-size:12px;color:#636c76}
.repo-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}
@media(max-width:640px){.repo-grid{grid-template-columns:1fr}}
.card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:18px;padding:18px 16px;min-height:96px}
.card .name{font-size:14px;font-weight:600}
.card .owner{font-size:11px;color:#636c76}
.card .desc{margin-top:8px;font-size:12px;color:#24292f;line-height:1.6;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card .meta{margin-top:12px;font-size:11px;color:#636c76}
</style>
""".strip()

def esc(s): return html.escape(s or "", quote=True)
def fmt(n): n=int(n or 0); return f"{n/1000:.1f}K" if n>=1000 else str(n)

def load_json(p):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    except: return {}

def main():
    stats = load_json(STATS_PATH)
    repos=[]
    for line in pathlib.Path("repositories.txt").read_text(encoding="utf-8").splitlines():
        line=line.strip();
        if not line or "/" not in line: continue
        owner,name=line.split("/",1)
        jpath=f"output/repositories/{owner}/{name}.json"
        j=load_json(jpath)
        if not j: continue
        repos.append(j)

    # 生成 README.html 风格的 HTML（GitHub 支持）
    lines=[]
    lines.append('<div class="profile-wrap">')
    lines.append(CSS)
    lines.append('<div class="profile-head">')
    lines.append('  <div class="profile-kpi">Profile · Harness Minimal</div>')
    lines.append('  <div class="profile-title">applex250</div>')
    lines.append('  <div class="profile-desc">少即是多 · 毛玻璃 · 留白</div>')
    lines.append('</div>')
    # stats
    lines.append('<div class="stats-row">')
    for key,label in [("issues","Issues"),("pullRequests","PRs"),("totalContributions","Contributions"),("repositories","Repos"),("stars","Stars")]:
        lines.append(f'  <div class="stat"><b>{fmt(stats.get(key,0))}</b><br/><span>{label}</span></div>')
    lines.append('</div>')
    # repos
    lines.append('<div class="repo-grid">')
    for r in repos:
        name=esc(r.get("name","")); owner=esc(r.get("owner",OWNER))
        desc=esc(r.get("description","")); langs=r.get("languages") or []
        lang_txt=" · ".join(esc(l.get("name","")) for l in langs[:2])
        stars=fmt(r.get("stars",0)); forks=fmt(r.get("forks",0))
        lines.append(f'  <a href="https://github.com/{owner}/{name}" style="text-decoration:none;color:inherit">')
        lines.append('    <div class="card">')
        lines.append(f'      <div class="name">{name}</div>')
        lines.append(f'      <div class="owner">{owner}</div>')
        if desc: lines.append(f'      <div class="desc">{desc}</div>')
        meta = " · ".join(x for x in [lang_txt, f"★ {stars}", f"⑂ {forks}"] if x)
        if meta: lines.append(f'      <div class="meta">{meta}</div>')
        lines.append('    </div>')
        lines.append('  </a>')
    lines.append('</div>')
    lines.append('</div>')
    out="\n".join(lines)+"\n"
    pathlib.Path("generated_readme.md").write_text(out, encoding="utf-8")
    print(f"[ok] HTML profile {len(repos)} repos")

if __name__=="__main__": main()
