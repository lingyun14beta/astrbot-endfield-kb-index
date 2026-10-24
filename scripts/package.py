"""把构建好的 sqlite 打包成可发布的 zip，并生成 manifest。

产物（--out 目录）：

    endfield_kb-<version>.sqlite3.zip
    endfield_kb-latest.sqlite3.zip
    *.sha256
    manifest.json

zip 使用固定时间戳与固定成员名，同样的 sqlite 会得到同样的 sha256。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import zipfile
from pathlib import Path

MEMBER = "endfield_kb.sqlite3"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def read_meta(db_path: Path) -> dict[str, str]:
    """读取索引 meta 表。"""
    con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    try:
        return dict(con.execute("SELECT k, v FROM meta"))
    finally:
        con.close()


def write_zip(db_path: Path, target: Path) -> str:
    """生成确定性 zip，返回 sha256。"""
    info = zipfile.ZipInfo(MEMBER, date_time=FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    with zipfile.ZipFile(target, "w") as zf:
        zf.writestr(info, db_path.read_bytes(), compresslevel=9)
    return hashlib.sha256(target.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="打包索引并生成 manifest")
    parser.add_argument("--input", type=Path, required=True, help="构建出的 sqlite")
    parser.add_argument("--version", required=True, help="索引版本，如 1.6.3")
    parser.add_argument("--out", type=Path, default=Path("dist"), help="输出目录")
    parser.add_argument(
        "--github", default="lingyun14beta/astrbot-endfield-kb-index", help="owner/repo"
    )
    parser.add_argument(
        "--modelscope", default="lingyun14/astrbot-endfield-kb-index", help="owner/name"
    )
    parser.add_argument("--min-plugin", default="1.1.0", help="插件最低版本")
    args = parser.parse_args()

    meta = read_meta(args.input)
    args.out.mkdir(parents=True, exist_ok=True)

    versioned = args.out / f"endfield_kb-{args.version}.sqlite3.zip"
    sha = write_zip(args.input, versioned)

    latest = args.out / "endfield_kb-latest.sqlite3.zip"
    shutil.copy2(versioned, latest)

    for asset in (versioned, latest):
        (asset.parent / f"{asset.name}.sha256").write_text(
            f"{sha}  {asset.name}\n", encoding="utf-8"
        )

    manifest = {
        "release_id": f"endfield-{args.version}",
        "schema_version": int(meta.get("schema_version", 0) or 0),
        "plugin_min_version": args.min_plugin,
        "documents": int(meta.get("documents", 0) or 0),
        "characters": int(meta.get("characters", 0) or 0),
        "refs": int(meta.get("refs", 0) or 0),
        "built_at": meta.get("built_at", ""),
        "sha256": sha,
        "size": latest.stat().st_size,
        "urls": [
            f"https://github.com/{args.github}/releases/latest/download/{latest.name}",
            "https://www.modelscope.cn/api/v1/datasets/"
            f"{args.modelscope}/repo?Revision=master&FilePath={latest.name}",
        ],
    }
    (args.out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"zip：{versioned}（{versioned.stat().st_size / 1e6:.2f} MB）")
    print(f"sha256：{sha}")
    print(f"manifest：{args.out / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
