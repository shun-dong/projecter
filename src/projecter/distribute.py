"""Distribute - 将笔记同步回项目 README

功能：笔记 → 项目
- 绝对路径 → 相对路径
- 去除 log 区块
- 不自动解决冲突
- 只操作 README.md
"""

import os
import re
import shutil
from typing import Optional

from .scanner import ProjectInfo, NoteInfo, read_file_content, parse_yaml_front_matter


def convert_absolute_to_relative(content: str, project_path: str) -> str:
    """将内容中的绝对链接转换为相对链接
    
    Args:
        content: 笔记内容
        project_path: 项目目录路径（用于判断哪些是绝对路径）
        
    Returns:
        转换后的内容
    """
    def replace_link(match):
        label = match.group(1)
        abs_path = match.group(2)
        
        # 跳过外部链接
        if (abs_path.startswith('http') or 
            abs_path.startswith('www.') or
            abs_path.startswith('//')):
            return match.group(0)
        
        # 规范化路径
        abs_path_norm = abs_path.replace('\\', '/')
        project_norm = project_path.replace('\\', '/')
        
        # 如果路径在项目目录下，转换为相对路径
        if abs_path_norm.startswith(project_norm):
            rel_path = os.path.relpath(abs_path, project_path).replace('\\', '/')
            return f'[{label}]({rel_path})'
        
        # 其他绝对路径保持不变
        return match.group(0)
    
    # 匹配 [label](path) 格式
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    return re.sub(pattern, replace_link, content)


def remove_log_block(content: str) -> str:
    """去除 log 区块
    
    Log 区块是以 # log 或 ## log 开头的区块
    一直持续到下一个同级或更高级标题
    
    Args:
        content: 内容
        
    Returns:
        去除 log 区块后的内容
    """
    lines = content.split('\n')
    result = []
    skipping = False
    log_header_level = 0
    
    for line in lines:
        stripped = line.strip()
        
        # 检测 log 标题 (# log, ## log, etc.)
        log_match = re.match(r'^(#+)\s*log\b', stripped, re.IGNORECASE)
        if log_match:
            skipping = True
            log_header_level = len(log_match.group(1))
            continue
        
        if skipping:
            # 检测是否到达新的同级或更高级标题
            header_match = re.match(r'^(#+)\s', stripped)
            if header_match:
                header_level = len(header_match.group(1))
                if header_level <= log_header_level:
                    # 新的区块开始，结束跳过
                    skipping = False
                    result.append(line)
            # 否则继续跳过
            continue
        
        result.append(line)
    
    return '\n'.join(result)


def distribute_note_to_project(
    note_info: NoteInfo,
    project_info: ProjectInfo,
    dry_run: bool = False
) -> bool:
    """将笔记同步到项目 README
    
    Args:
        note_info: 笔记信息
        project_info: 项目信息
        dry_run: 如果为 True，只显示操作不执行
        
    Returns:
        是否成功
    """
    # 读取笔记内容
    note_content = read_file_content(note_info.path)
    yaml_front, body = parse_yaml_front_matter(note_content)
    
    # 转换路径
    converted_body = convert_absolute_to_relative(body, project_info.path)
    
    # 去除 log 区块
    cleaned_body = remove_log_block(converted_body)
    
    # 构建新内容（保留 YAML front-matter，确保包含 project 字段）
    if not yaml_front.get('project'):
        yaml_front['project'] = project_info.name
    
    new_content = "---\n"
    for key, value in yaml_front.items():
        new_content += f"{key}: {value}\n"
    new_content += "---\n\n"
    new_content += cleaned_body
    
    # 检查现有 README
    readme_path = project_info.readme_path
    if os.path.exists(readme_path):
        existing_content = read_file_content(readme_path)
        
        if existing_content.strip() == new_content.strip():
            print(f"  {project_info.name}: 内容相同，无需同步")
            return True
        
        if not dry_run:
            # 备份现有 README
            backup_path = readme_path + '.backup'
            shutil.copy2(readme_path, backup_path)
            print(f"  {project_info.name}: 已备份现有 README 到 {backup_path}")
    
    if dry_run:
        print(f"  [dry-run] 将同步 {note_info.path} → {project_info.name}/README.md")
        return True
    
    # 写入 README
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✓ {note_info.name} → {project_info.name}/README.md")
        return True
    except Exception as e:
        print(f"  ✗ {project_info.name}: 写入失败 - {e}")
        return False


def distribute(notes: list, projects: list, dry_run: bool = False) -> None:
    """批量分发笔记到项目
    
    Args:
        notes: NoteInfo 列表
        projects: ProjectInfo 列表
        dry_run: 如果为 True，只显示操作不执行
    """
    if not notes:
        print("没有找到可同步的笔记")
        return
    
    if not projects:
        print("没有找到目标项目")
        return
    
    # 创建项目名称到项目的映射
    project_map = {p.name: p for p in projects}
    
    print(f"\n分发笔记到项目（{'预览模式' if dry_run else '执行模式'}）...")
    print(f"笔记数: {len(notes)}")
    print(f"目标项目数: {len(projects)}\n")
    
    success_count = 0
    unmatched_notes = []
    
    for note in notes:
        # 从 YAML 或文件名获取项目名
        project_name = note.yaml_front.get('project') or note.name
        
        if project_name in project_map:
            if distribute_note_to_project(note, project_map[project_name], dry_run):
                success_count += 1
        else:
            unmatched_notes.append(note)
    
    if unmatched_notes:
        print(f"\n未匹配的笔记（未找到对应项目）:")
        for note in unmatched_notes:
            print(f"  - {note.name} ({note.path})")
    
    print(f"\n完成: {success_count}/{len(notes)} 个笔记已同步")
