# Vault Template

[English](#english) | [中文](#中文)

---

<a id="english"></a>

## English

A ready-to-use vault template for **Obsidian-in-a-Vat** MCP server.

### Quick Start

1. Copy this directory:
   ```bash
   cp -r template_vault /path/to/my-vault
   ```

2. Set the environment variable:
   ```bash
   export VAULT_LOCAL_PATH=/path/to/my-vault
   ```

3. Start capturing ideas via the MCP server.

### Directory Structure

| Directory | Purpose |
|-----------|---------|
| `captures/` | Raw ideas and quick notes (auto-written by `vault_capture`) |
| `notes/` | Evergreen notes distilled from captures |
| `topics/` | Higher-level topic pages aggregating related notes |
| `maps/` | Relationship maps for navigating connections |
| `outputs/` | Generated deliverables: drafts, summaries, reports |
| `.brain/` | Machine-readable graph data (auto-maintained) |
| `templates/` | Markdown templates used by MCP tools |
| `.obsidian/` | Obsidian app configuration |

### Workflow

```
capture → note → topic → output
   ↓         ↓       ↓
        .brain/ (graph auto-maintained)
```

### Customization

- Edit `tags.yaml` to define your own tag synonyms for auto-tagging
- Modify templates in `templates/` to adjust frontmatter fields

---

<a id="中文"></a>

## 中文

**Obsidian-in-a-Vat** MCP 服务器的即用型 vault 模板。

### 快速开始

1. 复制此目录：
   ```bash
   cp -r template_vault /path/to/my-vault
   ```

2. 设置环境变量：
   ```bash
   export VAULT_LOCAL_PATH=/path/to/my-vault
   ```

3. 通过 MCP 服务器开始记录想法。

### 目录结构

| 目录 | 用途 |
|------|------|
| `captures/` | 原始想法和快速记录（由 `vault_capture` 自动写入） |
| `notes/` | 从 capture 提炼的常青笔记 |
| `topics/` | 汇聚相关笔记的主题页 |
| `maps/` | 关系导航图 |
| `outputs/` | 生成的交付物：草稿、摘要、报告 |
| `.brain/` | 机器可读的图谱数据（自动维护） |
| `templates/` | MCP 工具使用的 markdown 模板 |
| `.obsidian/` | Obsidian 应用配置 |

### 自定义

- 编辑 `tags.yaml` 定义你自己的标签同义词
- 修改 `templates/` 中的模板来调整 frontmatter 字段
