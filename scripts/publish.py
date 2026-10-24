"""发布 dist 下的资产：GitHub Release（主）+ ModelScope（可选镜像）。

用法：

    python scripts/publish.py --version 1.6.3                # 只发 GitHub
    python scripts/publish.py --version 1.6.3 --mirror       # 同时传 ModelScope

依赖：gh（已登录）、ms（已登录，仅 --mirror 需要）。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ASSETS = ("*.zip", "*.sha256", "manifest.json", "README.md", "LICENSE-INDEX.txt")


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """执行命令并回显。"""
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=check, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="发布索引资产")
    parser.add_argument("--version", required=True)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--repo", default="lingyun14beta/astrbot-endfield-kb-index")
    parser.add_argument("--dataset", default="lingyun14/astrbot-endfield-kb-index")
    parser.add_argument("--notes", default="")
    parser.add_argument("--mirror", action="store_true", help="同时上传 ModelScope")
    args = parser.parse_args()

    if not shutil.which("gh"):
        print("找不到 gh，请先安装 GitHub CLI 并 gh auth login", file=sys.stderr)
        return 2

    tag = f"data-v{args.version}"
    notes = args.notes or f"索引 {args.version}"

    assets: list[str] = []
    for pattern in ASSETS:
        assets.extend(str(p) for p in sorted(args.dist.glob(pattern)))

    run(
        [
            "gh",
            "release",
            "create",
            tag,
            *assets,
            "--repo",
            args.repo,
            "--title",
            f"Endfield KB {args.version}",
            "--notes",
            notes,
        ]
    )

    if args.mirror:
        if not shutil.which("ms"):
            print("找不到 ms，跳过 ModelScope 镜像", file=sys.stderr)
            return 0
        run(["ms", "upload", args.dataset, str(args.dist), "--repo-type", "dataset"])

    print(f"完成：{tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
