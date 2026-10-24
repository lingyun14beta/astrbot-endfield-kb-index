"""从 PRTS 语料构建索引。

逻辑不在这里复制：直接复用插件仓库的 ``endfield_kb.build_index``，
避免构建器和查询端出现两套清洗规则。

用法：

    python tools/build_index.py --out dist/endfield_kb.sqlite3
    python tools/build_index.py --plugin-dir ../astrbot_plugin_endfield_kb \
        --corpus ~/.dsh/prts-corpus/releases/<release> --out dist/endfield_kb.sqlite3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_PLUGIN_DIRS = [
    Path(__file__).resolve().parent.parent / "astrbot_plugin_endfield_kb",
    Path.home() / "astrbot_plugin_endfield_kb",
]


def find_plugin_dir(explicit: Path | None) -> Path:
    """定位插件仓库，供导入 endfield_kb。"""
    candidates = [explicit] if explicit else []
    candidates += DEFAULT_PLUGIN_DIRS
    for candidate in candidates:
        if candidate and (candidate / "endfield_kb.py").is_file():
            return candidate
    raise FileNotFoundError(
        "找不到插件仓库里的 endfield_kb.py，请用 --plugin-dir 指定"
    )


def latest_release(releases_dir: Path) -> Path:
    """读取 current.json 指向的发布目录。"""
    import json

    current = releases_dir / "current.json"
    if current.is_file():
        release_id = json.loads(current.read_text(encoding="utf-8")).get("release_id")
        if release_id and (releases_dir / release_id).is_dir():
            return releases_dir / release_id
    candidates = [
        p for p in releases_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
    ]
    if not candidates:
        raise FileNotFoundError(f"{releases_dir} 下没有发布目录")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def main() -> int:
    parser = argparse.ArgumentParser(description="构建终末地知识库索引")
    parser.add_argument("--plugin-dir", type=Path, help="插件仓库目录")
    parser.add_argument("--corpus", type=Path, help="语料发布目录")
    parser.add_argument("--out", type=Path, required=True, help="输出的 sqlite 路径")
    args = parser.parse_args()

    plugin_dir = find_plugin_dir(args.plugin_dir)
    sys.path.insert(0, str(plugin_dir))
    from endfield_kb import build_index  # noqa: PLC0415

    corpus_root = args.corpus or latest_release(
        Path.home() / ".dsh" / "prts-corpus" / "releases"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    print(f"插件：{plugin_dir}")
    print(f"语料：{corpus_root}")

    stats = build_index(corpus_root, args.out)
    print(
        "完成：{documents} 篇，{characters} 字，{seconds} 秒，{size_mb} MB".format(
            **stats
        )
    )
    print(f"输出：{args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
