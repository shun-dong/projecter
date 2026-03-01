"""Collect - 将项目 README 同步到笔记

功能：项目 → 笔记
- 相对路径 → 绝对路径
- 不自动解决冲突
- 只操作 .md 文件
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional

from .scanner import ProjectInfo, NoteInfo, read_file_content, parse_yaml_front_matter


def convert_relative_to_absolute(content: str, project_path: str) -> str:
    """将内容中的相对链接转换为绝对链接
    
    Args:
        content: README 内容
        project_path: 项目目录路径
        
    Returns:
        转换后的内容
    """
    def replace_link(match):
        label = match.group(1)
        rel_path = match.group(2)
        
        # 跳过外部链接和绝对路径
        if (rel_path.startswith('http') or 
            rel_path.startswith('/') or
            rel_path.startswith('\\') or
            rel_path.endswith('.com') or
            rel_path.endswith('.cn') or
            rel_path.endswith('.org')):
            return match.group(0)
        
        # 转换为绝对路径
        abs_path = os.path.abspath(os.path.join(project_path, rel_path))
        abs_path = abs_path.replace('\\', '/')
        
        return f'[{label}]({abs_path})'
    
    # 匹配 [label](path) 格式
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    return re.sub(pattern, replace_link, content)


def collect_project_to_note(
    project_info: ProjectInfo,
    note_dirs: list,
    dry_run: bool = False
) -> bool:
    """将项目 README 同步到笔记
    
    Args:
        project_info: 项目信息
        note_dirs: 笔记目录列表
        dry_run: 如果为 True，只显示操作不执行
        
    Returns:
        是否成功
    """
    # 读取项目 README
    project_content = read_file_content(project_info.readme_path)
    yaml_front, body = parse_yaml_front_matter(project_content)
    
    # 转换路径
    converted_body = convert_relative_to_absolute(body, project_info.path)
    
    # 构建新内容（保留 YAML front-matter，确保包含 project 字段）
    if not yaml_front.get('project'):
        yaml_front['project'] = project_info.name
    
    new_content = "---\n"
    for key, value in yaml_front.items():
        new_content += f"{key}: {value}\n"
    new_content += "---\n\n"
    new_content += converted_body
    
    # 确定目标笔记路径
    # 优先使用第一个笔记目录
    target_dir = note_dirs[0] if note_dirs else None
    if not target_dir or not os.path.exists(target_dir):
        print(f"错误: 笔记目录不存在: {target_dir}")
        return False
    
    # 笔记文件名使用项目名称 + .md（不再使用 ! 前缀）
    note_filename = f"{project_info.name}.md"
    note_path = os.path.join(target_dir, note_filename)
    
    # 检查笔记是否已存在
    if os.path.exists(note_path):
        # 读取现有笔记
        existing_content = read_file_content(note_path)
        
        if existing_content.strip() == new_content.strip():
            print(f"  {project_info.name}: 内容相同，无需同步")
            return True
        
        if not dry_run:
            # 备份现有笔记
            backup_path = note_path + '.backup'
            shutil.copy2(note_path, backup_path)
            print(f"  {project_info.name}: 已备份现有笔记到 {backup_path}")
    
    if dry_run:
        print(f"  [dry-run] 将同步 {project_info.name} → {note_path}")
        return True
    
    # 写入笔记
    try:
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✓ {project_info.name} → {note_path}")
        return True
    except Exception as e:
        print(f"  ✗ {project_info.name}: 写入失败 - {e}")
        return False


def collect(projects: list, note_dirs: list, dry_run: bool = False) -> None:
    """批量收集项目到笔记
    
    Args:
        projects: ProjectInfo 列表
        note_dirs: 笔记目录列表
        dry_run: 如果为 True，只显示操作不执行
    """
    if not projects:
        print("没有找到可同步的项目")
        return
    
    if not note_dirs:
        print("错误: 没有配置笔记目录")
        return
    
    print(f"\n收集项目到笔记（{'预览模式' if dry_run else '执行模式'}）...")
    print(f"项目数: {len(projects)}")
    print(f"目标笔记目录: {', '.join(note_dirs)}\n")
    
    success_count = 0
    for project in projects:
        if collect_project_to_note(project, note_dirs, dry_run):
            success_count += 1
    
    print(f"\n完成: {success_count}/{len(projects)} 个项目已同步")
