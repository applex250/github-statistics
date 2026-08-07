# GitHub Statistics

自动编译 GitHub 统计并生成 SVG 卡片,展示在 [applex250 的主页 README](https://github.com/applex250)。

- `output/overview.svg` — 用户总览统计(Issues / Pull Requests / Contributions / Repositories / Stars)
- `output/repositories/<owner>/<repo>.svg` — 仓库信息卡片
- `output/footer.svg` / `output/spacer.svg` — 装饰
- `overview.py` — 由 `output/*.json` 生成 SVG 与 `generated_readme.md`(推送至 profile 仓库)

统计数据每 3 小时由 GitHub Actions 自动刷新(需 `ACCESS_TOKEN` secret,带 `repo` 权限)。

展示哪些仓库:编辑 `repositories.txt`(每行 `owner/repo`)。
