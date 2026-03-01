# Projecter 2.0

简化版项目管理工具，专注于 README 和笔记的同步。

## 特性

- **简化匹配**：优先匹配 YAML front-matter 的 `project` 字段，其次匹配文件名
- **手动同步方向**：不再自动解决冲突，用户根据 `diff` 结果选择 `collect` 或 `distribute`
- **显式文件树**：`tree` 命令生成文件树到 stdout，用户自行复制使用
- **Git Hook 可选**：留给用户自行处理

## 安装

```bash
pip install -e .
```

## 配置

首次运行时会引导配置：

```bash
projecter create my-project
```

或手动创建配置文件 `~/.config/projecter/config.json`：

```json
{
    "project_dir": "/path/to/projects",
    "note_dirs": ["/path/to/notes"]
}
```

## CLI 命令

```bash
# 项目管理
projecter create <name>          # 创建新项目
projecter delete <name>          # 删除项目
projecter list                   # 列出所有项目
projecter tree <name>            # 生成项目文件树

# 同步（手动方向选择）
projecter diff [name]            # 查看差异
projecter collect [--dry-run]    # 项目 → 笔记
projecter distribute [--dry-run] # 笔记 → 项目

# 配置
projecter link <project> <note>  # 手动关联（可选）
projecter config                 # 修改配置
```

## 工作流示例

```bash
# 1. 创建项目
projecter create my-app

# 2. 在 Obsidian 中编辑笔记

# 3. 查看差异
projecter diff

# 4. 根据差异选择同步方向
projecter distribute  # 如果笔记较新
# 或
projecter collect     # 如果项目较新
```

## 匹配机制

1. **优先**：YAML front-matter 的 `project` 字段
2. **其次**：文件名（不含 .md）
3. **歧义**：打印警告，让用户手动解决

## 与旧版的区别

| 功能 | 旧版 | 新版 |
|------|------|------|
| 匹配 | `!` 前缀文件名 | YAML `project` 字段优先 |
| 同步 | `sync` 自动双向 | `diff` + 手动选择方向 |
| 冲突 | 自动合并 | 只打印消息 |
| 文件树 | 自动插入 README | `tree` 命令，用户复制 |
| Git Hook | 计划集成 | 用户自行处理 |

## 项目结构

```
src/projecter/
├── __init__.py
├── __main__.py
├── cli.py          # CLI 命令
├── scanner.py      # 项目和笔记扫描
├── matcher.py      # 匹配逻辑
├── collect.py      # 项目 → 笔记
├── distribute.py   # 笔记 → 项目
└── diff.py         # 差异检测
```

## License

MIT
