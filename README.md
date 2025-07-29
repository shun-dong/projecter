---
project: projecter
tags: 
---

projecter
├── [README.md](README.md)
├── [.git/](.git)
└── [projecter.py](projecter.py)



# 项目简介

本项目用于为 project 目录下的每个非空子项目自动生成和维护结构化的 `README.md` 文件，内容包括：

- `README.md`文件的生成和维护
  
  - 自动补充 YAML front-matter（项目名、标签） 
  
  - 展示项目一级文件树结构，并为所有文件/文件夹生成相对 Markdown 链接
  
  - 保持已有 `README.md` 内容不被破坏，仅增补必需内容

- 将每个项目的`README.md`集中到一起维护
  
  - 合并项目文件内的`README.md`和集中文件夹内的`README.md`

# 用法

配置 `update_readme.py` 脚本中的 `PROJECT_DIR`, `TARGET_READMES_DIR` 路径为自己的 project 目录。

你可以在每个 `README.md` 的 YAML front-matter 中补充标签，简介部分写明项目内容，便于个人或团队管理和检索。
