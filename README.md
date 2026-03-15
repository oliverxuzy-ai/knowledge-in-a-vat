# vault-mcp

[English](#english) | [中文](#中文)

---

<a id="english"></a>

## English

Personal knowledge vault MCP server for Claude Desktop. Capture thoughts, search notes, and read files from a local markdown-based knowledge vault.

---

### Quick Start (Docker — Recommended)

**Step 1.** Make sure [Docker Desktop](https://www.docker.com/products/docker-desktop/) is running.

**Step 2.** Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "vault": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/Users/yourname/my-vault:/vault",
        "ghcr.io/oliverxuzy-ai/obsidian-in-a-vat:latest"
      ]
    }
  }
}
```

Replace `/Users/yourname/my-vault` with the absolute path to your local vault directory.

**Step 3.** Fully quit and reopen Claude Desktop. The `vault` tools will appear automatically.

> **Don't have a vault yet?** Copy the included template:
> ```bash
> cp -r example_vault /Users/yourname/my-vault
> ```

#### Updating to the Latest Version

When a new version is released, pull the latest image before restarting Claude Desktop:

```bash
docker pull ghcr.io/oliverxuzy-ai/obsidian-in-a-vat:latest
```

---

### Alternative Setup (Python / uv)

If you prefer not to use Docker:

```bash
# Install
uv venv && source .venv/bin/activate
uv pip install -e .
```

Claude Desktop config:

```json
{
  "mcpServers": {
    "vault": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "vault_mcp"],
      "env": {
        "VAULT_LOCAL_PATH": "/Users/yourname/my-vault"
      }
    }
  }
}
```

> Use the absolute path to the venv's python — Claude Desktop does not inherit your shell PATH.

---

### Tools

#### vault_capture

Capture a refined insight into the vault. Claude will refine your thought into a concise insight, confirm with you, then store it.

- **title** (str): Plain-text title (≤50 characters)
- **insight** (str): Core insight in 1–3 sentences
- **source_type** (str, optional): Origin — `"conversation"` (default), `"article"`, or `"flash"`
- **original** (str, optional): Verbatim original material for reference
- **tags** (list[str], optional): Tags to categorize (auto-extracted if omitted)

Auto-generates a timestamped filename, extracts tags from content, and writes using the capture template format. Returns the file path and related existing captures.

#### vault_promote

Promote one or more captures into a structured note with auto-wikilink insertion.

- **capture_paths** (list[str]): Capture file paths to promote
- **title** (str): Title for the new note
- **summary** (str): One-sentence summary of the core idea
- **domain** (str): Knowledge domain (e.g. `"ai"`, `"productivity"`)
- **content** (str): Synthesized note body in markdown
- **tags** (list[str], optional): Tags (inherits from captures if omitted)
- **aliases** (list[str], optional): Alternative names for the note
- **confidence** (float, optional): Confidence level 0.0–1.0 (default 0.7)
- **auto_link** (bool, optional): Auto-insert wikilinks to existing notes (default true)

Handles file creation, frontmatter, wikilink insertion, and marks source captures as promoted.

#### vault_search

Search the vault for notes matching a query.

- **query** (str): Text to search for in filenames and content
- **directory** (str, optional): Subdirectory to search within
- **tags** (list[str], optional): Filter results by frontmatter tags

Returns matching files with path, title, status, tags, created date, and a 200-char preview.

#### vault_read

Read the full content of a vault note.

- **path** (str): Relative path to the file within the vault

Returns the complete markdown content including frontmatter.

#### vault_list_captures

List captures filtered by status, sorted newest first.

- **status** (str, optional): `"capture"` (default), `"promoted"`, or `"all"`
- **limit** (int, optional): Maximum results (default 50)

---

### Auto-Tag Extraction

Tags are extracted from capture text using three sources (in priority order):

1. **tags.yaml** — Custom tags and synonym mappings at the vault root
2. **Existing notes** — Tags collected from existing vault files' frontmatter
3. **Default domains** — Fallback: ai, llm, productivity, writing, coding, design, business, learning, health, finance, philosophy, psychology

Example `tags.yaml` in your vault root:

```yaml
tags:
  ai: [artificial intelligence, machine learning, ML, deep learning]
  coding: [programming, software, development, code]
  design: [UX, UI, user experience]
```

---

### Development

```bash
# Build image locally
docker build -t vault-mcp .

# Test the container starts (Ctrl+C to stop)
echo '{}' | docker run -i --rm -v $(pwd)/example_vault:/vault vault-mcp

# Syntax check
python -m py_compile src/vault_mcp/server.py

# Interactive MCP Inspector
mcp dev src/vault_mcp/server.py
```

---

<a id="中文"></a>

## 中文

个人知识库 MCP 服务器，适配 Claude Desktop。捕获想法、搜索笔记、读取本地 markdown 知识库中的文件。

---

### 快速开始（Docker — 推荐）

**第一步.** 确保 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 正在运行。

**第二步.** 添加到 Claude Desktop 配置文件（`~/Library/Application Support/Claude/claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "vault": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/Users/yourname/my-vault:/vault",
        "ghcr.io/oliverxuzy-ai/obsidian-in-a-vat:latest"
      ]
    }
  }
}
```

将 `/Users/yourname/my-vault` 替换为你本地 vault 目录的绝对路径。

**第三步.** 完全退出并重新打开 Claude Desktop，`vault` 工具会自动出现。

> **还没有 vault？** 复制内置模板：
> ```bash
> cp -r example_vault /Users/yourname/my-vault
> ```

#### 更新到最新版本

当有新版本发布时，在重启 Claude Desktop 前先拉取最新镜像：

```bash
docker pull ghcr.io/oliverxuzy-ai/obsidian-in-a-vat:latest
```

---

### 备选安装方式（Python / uv）

如果不想使用 Docker：

```bash
# 安装
uv venv && source .venv/bin/activate
uv pip install -e .
```

Claude Desktop 配置：

```json
{
  "mcpServers": {
    "vault": {
      "command": "/绝对路径/.venv/bin/python",
      "args": ["-m", "vault_mcp"],
      "env": {
        "VAULT_LOCAL_PATH": "/Users/yourname/my-vault"
      }
    }
  }
}
```

> 必须使用 venv 内 python 的绝对路径 — Claude Desktop 不继承你的 shell PATH。

---

### 工具

#### vault_capture

捕获精炼后的洞察到 vault 中。Claude 会将你的想法提炼为简洁的洞察，经你确认后存储。

- **title** (str)：纯文本标题（≤50 字符）
- **insight** (str)：核心洞察，1–3 句话
- **source_type** (str, 可选)：来源 — `"conversation"`（默认）、`"article"` 或 `"flash"`
- **original** (str, 可选)：原始素材的原文
- **tags** (list[str], 可选)：分类标签（省略则自动提取）

自动生成时间戳文件名，从内容中提取标签，使用 capture 模板格式写入。返回文件路径和相关的已有 captures。

#### vault_promote

将一个或多个 capture 提升为结构化笔记，自动插入 wikilinks。

- **capture_paths** (list[str])：要提升的 capture 文件路径
- **title** (str)：新笔记标题
- **summary** (str)：核心思想的一句话总结
- **domain** (str)：知识领域（如 `"ai"`、`"productivity"`）
- **content** (str)：综合笔记正文（markdown 格式）
- **tags** (list[str], 可选)：标签（省略则继承 capture 标签）
- **aliases** (list[str], 可选)：笔记别名
- **confidence** (float, 可选)：置信度 0.0–1.0（默认 0.7）
- **auto_link** (bool, 可选)：自动插入指向已有笔记的 wikilinks（默认开启）

处理文件创建、frontmatter、wikilink 插入，并将源 captures 标记为已提升。

#### vault_search

搜索 vault 中匹配查询的笔记。

- **query** (str)：在文件名和内容中搜索的文本
- **directory** (str, 可选)：搜索的子目录
- **tags** (list[str], 可选)：按 frontmatter 标签过滤结果

返回匹配的文件，包含路径、标题、状态、标签、创建日期和 200 字符预览。

#### vault_read

读取 vault 笔记的完整内容。

- **path** (str)：vault 内文件的相对路径

返回完整的 markdown 内容（含 frontmatter）。

#### vault_list_captures

按状态筛选 captures，按时间倒序排列。

- **status** (str, 可选)：`"capture"`（默认）、`"promoted"` 或 `"all"`
- **limit** (int, 可选)：最大返回数量（默认 50）

---

### 自动标签提取

标签从 capture 文本中提取，使用三个来源（按优先级排序）：

1. **tags.yaml** — vault 根目录的自定义标签和同义词映射
2. **已有笔记** — 收集已有 vault 文件 frontmatter 中的标签进行匹配
3. **默认领域** — 兜底列表：ai, llm, productivity, writing, coding, design, business, learning, health, finance, philosophy, psychology

`tags.yaml` 示例（放在 vault 根目录）：

```yaml
tags:
  ai: [artificial intelligence, machine learning, ML, deep learning]
  coding: [programming, software, development, code]
  design: [UX, UI, user experience]
```

---

### 开发

```bash
# 本地构建镜像
docker build -t vault-mcp .

# 测试容器启动（Ctrl+C 停止）
echo '{}' | docker run -i --rm -v $(pwd)/example_vault:/vault vault-mcp

# 语法检查
python -m py_compile src/vault_mcp/server.py

# 使用 MCP Inspector 交互测试
mcp dev src/vault_mcp/server.py
```
