# 终末地知识库 · 索引数据

《明日方舟：终末地》中文知识库的**构建脚本、版本清单与发布资产**。本仓库不包含、也不重新分发原始语料。

- 插件仓库：<https://github.com/lingyun14beta/astrbot_plugin_endfield_kb>
- 本仓库：<https://github.com/lingyun14beta/astrbot-endfield-kb-index>
- ModelScope 镜像：<https://modelscope.cn/datasets/lingyun14/astrbot-endfield-kb-index>

## 目录

| 路径 | 作用 |
|---|---|
| `tools/build_index.py` | 从 PRTS 语料构建 sqlite（复用插件的清洗与索引逻辑，不复制实现） |
| `scripts/package.py` | 打包 zip、算 sha256、生成 manifest |
| `scripts/publish.py` | 发布 GitHub Release，可选同步 ModelScope |
| `manifest.example.json` | 清单格式示例 |
| `LICENSE-INDEX.txt` | 索引数据许可与来源声明（索引不适用插件代码的 AGPL） |

构建产物（`dist/`）与 Release 资产不进 git：

```
dist/
├─ endfield_kb-1.6.3.sqlite3.zip
├─ endfield_kb-latest.sqlite3.zip
├─ *.sha256
└─ manifest.json
```

## 版本约定

- Tag：`data-v1.6.3`，一版一 tag，资产只读
- 版本化资产：`endfield_kb-1.6.3.sqlite3.zip`
- 别名资产：`endfield_kb-latest.sqlite3.zip`，覆盖更新
- zip 使用固定成员名 `endfield_kb.sqlite3` 与固定时间戳，**同样的 sqlite 每次打包得到同样的 sha256**

## 构建

前置：本机有 PRTS 语料发布包（`~/.dsh/prts-corpus/releases/`），以及插件仓库。

```bash
# 生成 sqlite（约 30–60 秒）
python tools/build_index.py --out dist/endfield_kb.sqlite3

# 语料目录不是最新时手动指定
python tools/build_index.py --corpus ~/.dsh/prts-corpus/releases/<release> \
    --out dist/endfield_kb.sqlite3

# 插件仓库不在同级目录时
python tools/build_index.py --plugin-dir ../astrbot_plugin_endfield_kb \
    --out dist/endfield_kb.sqlite3
```

## 打包

```bash
python scripts/package.py --input dist/endfield_kb.sqlite3 --version 1.6.3 --out dist
```

产出 zip、`.sha256` 与 `manifest.json`。`manifest.json` 的字段：

| 字段 | 用途 |
|---|---|
| `release_id` | 与索引内 `meta.release` 对应 |
| `schema_version` | 必须与插件一致，否则拒绝加载 |
| `plugin_min_version` | 低于该版本的插件不提示升级 |
| `sha256` / `size` | 下载后校验 |
| `urls` | 按顺序尝试；GitHub 优先，ModelScope 兜底 |

## 发布

```bash
# 只发 GitHub
python scripts/publish.py --version 1.6.3

# 同时上传 ModelScope
python scripts/publish.py --version 1.6.3 --mirror
```

依赖：`gh`（已登录）与 `ms`（`pip install modelscope` 后登录）。
没有 `gh` 时也可以网页建 Release，把 `dist/` 里的文件拖上去。

发布后确认两个直链都可下载：

```
https://github.com/lingyun14beta/astrbot-endfield-kb-index/releases/latest/download/endfield_kb-latest.sqlite3.zip

https://www.modelscope.cn/api/v1/datasets/lingyun14/astrbot-endfield-kb-index/repo?Revision=master&FilePath=endfield_kb-latest.sqlite3.zip
```

> `releases/latest/download/...` 只有在发布过非 draft、非 prerelease 的 Release 之后才有效。

## 插件如何消费

1. 请求 manifest（多源、3–5 秒超时），拿到 `urls` 与 `sha256`
2. manifest 全部失败时，直接尝试 `endfield_kb-latest.sqlite3.zip`
3. 下载 → 校验 sha256 → SQLite 完整性 → `schema_version`
4. 通过后原子替换，保留最近两个版本

## 更新节奏

跟随游戏版本：PRTS 发布新语料 → 重建 → 打包 → 发布新 tag。
全量重建 30–60 秒，不做增量构建——语料规模在百万字级，全量更简单可靠。

## 许可

本仓库有意采用与上游 PRTS.chat 相同的分层写法：代码与数据分开授权，数据不挂
一个自造的 SPDX 标识。

- **索引数据**：保留权利，仅授予下载与本地检索使用；条款见 [LICENSE-INDEX.txt](LICENSE-INDEX.txt)。
  不使用 SPDX 许可标识，也不适用插件代码的 AGPL
- **构建脚本**：复用插件仓库的实现，随插件采用 AGPL-3.0-or-later
- **原始语料**：不随本仓库分发，需求方自行从 PRTS.chat 资料集下载（该数据集标注为 `other`）
- **游戏内容**：名称、文本及相关内容的权利归上海鹰角开拓者网络科技有限公司及相关权利人
- **整理内容**：剧情总结、角色 Wiki、世界实体资料的权利归 PRTS.chat
- **未纳入**：PRTS Wiki《泰拉年表》（CC BY-NC-SA 4.0）与《明日方舟》语料

数据来源：PRTS.chat 终末地资料集（release 1.6.3）
<https://modelscope.cn/datasets/HTiantian/prts-agent-corpus-endfield>

本项目为非官方社区项目，与游戏开发商、发行商无隶属或背书关系。
