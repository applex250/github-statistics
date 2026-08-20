#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Profile README — 内联样式版（GitHub 会过滤 <style>，必须全写 inline）
完全复用网站 Harness 极简黑白写法，但全部用 inline style + table 布局
"""
import json, html, pathlib

OWNER="applex250"
def esc(s): return html.escape(s or "", quote=True)
def fmt(n): n=int(n or 0); return f"{n/1000:.1f}K" if n>=1000 else str(n)
def load(p):
    try: return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    except: return {}

stats=load("output/stats.json")
repos=[]
for line in pathlib.Path("repositories.txt").read_text(encoding="utf-8").splitlines():
    line=line.strip()
    if not line or "/" not in line: continue
    o,n=line.split("/",1)
    j=load(f"output/repositories/{o}/{n}.json")
    if j: repos.append(j)

# 统计顺序：Contributions / Repos / Stars / PRs
stats_items=[("totalContributions","Contributions"),("repositories","Repos"),("stars","Stars"),("pullRequests","PRs")]

lines=[]
lines.append('<div align="left">')
# 头部
lines.append('<p style="margin:18px 0 0;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#636c76">Profile · Harness Minimal</p>')
lines.append('<p style="margin:6px 0 0;font-size:22px;font-weight:600;letter-spacing:-.02em;line-height:1.2">applex250</p>')
lines.append('<p style="margin:6px 0 0;font-size:13px;color:#636c76;line-height:1.6">少即是多 · 毛玻璃 · 留白</p>')

# stats 用 table 一行
lines.append('<table style="width:100%;border-collapse:separate;border-spacing:10px 0;margin-top:16px"><tr>')
for key,label in stats_items:
    v=fmt(stats.get(key,0))
    lines.append(f'<td align="center" style="background:rgba(0,0,0,0.04);border:1px solid rgba(0,0,0,0.08);border-radius:16px;padding:14px 10px;width:25%"><span style="font-size:18px;font-weight:600">{v}</span><br/><span style="font-size:11px;color:#636c76">{label}</span></td>')
lines.append('</tr></table>')

# repos 2列 grid 用 table
lines.append('<table style="width:100%;border-collapse:separate;border-spacing:12px;margin-top:14px">')
for i in range(0,len(repos),2):
    lines.append('<tr>')
    for j in range(2):
        if i+j < len(repos):
            r=repos[i+j]
            name=esc(r.get("name","")); owner=esc(r.get("owner",OWNER)); desc=esc((r.get("description") or "")[:72])
            langs=r.get("languages") or []; lang_txt=" · ".join(esc(l.get("name","")) for l in langs[:2])
            stars=fmt(r.get("stars",0))
            meta=" · ".join(x for x in [lang_txt, f"★ {stars}"] if x)
            cell=f'<td width="50%" style="vertical-align:top"><a href="https://github.com/{owner}/{name}" style="text-decoration:none;color:inherit"><table style="width:100%;background:rgba(0,0,0,0.04);border:1px solid rgba(0,0,0,0.08);border-radius:18px"><tr><td style="padding:16px">'
            cell+=f'<div style="font-size:14px;font-weight:600">{name}</div>'
            cell+=f'<div style="font-size:11px;color:#636c76">{owner}</div>'
            if desc: cell+=f'<div style="margin-top:8px;font-size:12px;color:#24292f;line-height:1.5">{desc}</div>'
            if meta: cell+=f'<div style="margin-top:10px;font-size:11px;color:#636c76">{meta}</div>'
            cell+='</td></tr></table></a></td>'
            lines.append(cell)
        else:
            lines.append('<td width="50%"></td>')
    lines.append('</tr>')
lines.append('</table>')
lines.append('</div>')

out="\n".join(lines)+"\n"
pathlib.Path("generated_readme.md").write_text(out, encoding="utf-8")
print(out[:1200])
print(f"[ok] inline HTML {len(repos)} repos")
