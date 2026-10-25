"""把 dist/ 里的索引资产上传到 ModelScope 数据集。

只传对外分发的文件：zip、sha256、manifest.json、README.md、LICENSE-INDEX.txt。
构建用的原始 sqlite（30 MB+）不会上传。

用法：

    set MODELSCOPE_API_TOKEN=xxxx        # Windows
    export MODELSCOPE_API_TOKEN=xxxx     # Linux / macOS
    python scripts/upload_modelscope.py

也可以显式传 --token。
"""

from __future__ import annotations

import argparse
import fnmatch
import os
from pathlib import Path

REPO = "lingyun14/astrbot-endfield-kb-index"
PATTERNS = ["*.zip", "*.sha256", "manifest.json", "README.md", "LICENSE-INDEX.txt"]
DIST = Path(__file__).resolve().parent.parent / "dist"


def collect(dist: Path) -> list[Path]:
    """按白名单挑出要上传的文件，跳过原始 sqlite。"""
    if not dist.is_dir():
        raise FileNotFoundError(f"找不到 {dist}，先跑 scripts/package.py 生成资产")
    files = [p for p in dist.iterdir() if p.is_file()]
    picked = [
        p
        for p in sorted(files)
        if any(fnmatch.fnmatch(p.name, pattern) for pattern in PATTERNS)
    ]
    if not picked:
        raise FileNotFoundError(f"{dist} 里没有可上传的文件，先跑 scripts/package.py")
    return picked


def main() -> int:
    parser = argparse.ArgumentParser(description="上传索引资产到 ModelScope 数据集")
    parser.add_argument("--dist", type=Path, default=DIST, help="dist 目录")
    parser.add_argument("--repo", default=REPO, help="数据集 id")
    parser.add_argument(
        "--token",
        default=os.environ.get("MODELSCOPE_API_TOKEN", ""),
        help="访问令牌；留空则用本机已保存的登录信息",
    )
    parser.add_argument("--message", default="", help="提交说明")
    args = parser.parse_args()

    picked = collect(args.dist)
    total = sum(p.stat().st_size for p in picked) / 1e6
    print(f"目标数据集：{args.repo}")
    print(f"待上传 {len(picked)} 个文件，共 {total:.1f} MB")
    for p in picked:
        print(f"  {p.name}  {p.stat().st_size} bytes")

    try:
        from modelscope.hub.api import HubApi
    except ImportError:
        print("缺少 modelscope，先执行：pip install -U modelscope")
        return 2

    api = HubApi()
    if args.token:
        api.login(args.token)

    try:
        api.upload_folder(
            repo_id=args.repo,
            repo_type="dataset",
            folder_path=str(args.dist),
            allow_patterns=PATTERNS,
            commit_message=args.message or "update index assets",
        )
    except Exception as exc:  # noqa: BLE001 - 统一提示，避免刷屏堆栈
        print(f"上传失败：{exc}")
        print("检查：令牌是否有效、数据集是否存在、账号是否有写权限")
        return 1

    base = f"https://www.modelscope.cn/api/v1/datasets/{args.repo}/repo"
    print("\n完成。用这几条地址自查：")
    for name in ("manifest.json", "endfield_kb-latest.sqlite3.zip"):
        print(f"  {base}?Revision=master&FilePath={name}")
    print("\nsha256 应与 dist/*.sha256 一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
