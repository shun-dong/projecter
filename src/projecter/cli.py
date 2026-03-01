#!/usr/bin/env python3
"""Projecter CLI - 项目管理工具

简化版命令：
- create: 创建新项目
- delete: 删除项目
- list: 列出所有项目
- tree: 生成项目文件树
- collect: 项目 → 笔记（单向同步）
- distribute: 笔记 → 项目（单向同步）
- diff: 查看差异
- link: 手动关联（可选）
- config: 配置管理
"""

import json
import os
import sys
from pathlib import Path

import click

from .scanner import scan_projects, scan_notes
from .matcher import match_project_to_notes
from .collect import collect as collect_module
from .distribute import distribute as distribute_module
from .distribute import distribute
from .diff import diff


# 配置文件路径
CONFIG_DIR = Path.home() / '.config' / 'projecter'
CONFIG_FILE = CONFIG_DIR / 'config.json'


def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_config(config):
    """保存配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_config():
    """获取配置，如果没有则引导创建"""
    config = load_config()
    if config is None:
        click.echo("首次使用，需要配置...")
        config = create_config_interactive()
    return config


def create_config_interactive():
    """交互式创建配置"""
    click.echo("\n=== Projecter 配置 ===")
    
    project_dir = click.prompt("项目根目录路径", type=str)
    while not os.path.isdir(project_dir):
        click.echo(f"目录不存在: {project_dir}")
        project_dir = click.prompt("项目根目录路径", type=str)
    
    note_dirs = []
    click.echo("\n笔记目录（可添加多个，输入空行结束）")
    while True:
        note_dir = click.prompt("笔记目录路径", type=str, default='')
        if not note_dir:
            break
        if os.path.isdir(note_dir):
            note_dirs.append(note_dir)
            click.echo(f"已添加: {note_dir}")
        else:
            click.echo(f"目录不存在: {note_dir}")
    
    if not note_dirs:
        click.echo("错误: 至少需要指定一个笔记目录")
        sys.exit(1)
    
    config = {
        'project_dir': project_dir,
        'note_dirs': note_dirs
    }
    
    save_config(config)
    click.echo(f"\n配置已保存到: {CONFIG_FILE}")
    return config


@click.group()
@click.version_option(version='2.0.0')
def cli():
    """Projecter - 管理项目 README 和笔记同步"""
    pass


@cli.command()
@click.argument('name')
def create(name):
    """创建新项目"""
    config = get_config()
    project_dir = config['project_dir']
    project_path = os.path.join(project_dir, name)
    
    if os.path.exists(project_path):
        click.echo(f"错误: 项目 '{name}' 已存在")
        sys.exit(1)
    
    # 创建项目目录
    os.makedirs(project_path)
    
    # 创建 README.md
    readme_path = os.path.join(project_path, 'README.md')
    content = f"""---
project: {name}
tags:
---

# {name}

项目描述...
"""
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    click.echo(f"✓ 创建项目: {name}")
    click.echo(f"  路径: {project_path}")
    click.echo(f"  README: {readme_path}")


@cli.command()
@click.argument('name')
@click.confirmation_option(prompt='确定要删除这个项目吗？此操作不可恢复！')
def delete(name):
    """删除项目"""
    config = get_config()
    project_dir = config['project_dir']
    project_path = os.path.join(project_dir, name)
    
    if not os.path.exists(project_path):
        click.echo(f"错误: 项目 '{name}' 不存在")
        sys.exit(1)
    
    import shutil
    shutil.rmtree(project_path)
    click.echo(f"✓ 已删除项目: {name}")


@cli.command()
def list():
    """列出所有项目"""
    config = get_config()
    projects = scan_projects(config['project_dir'])
    
    if not projects:
        click.echo("没有找到项目")
        return
    
    click.echo(f"\n找到 {len(projects)} 个项目:\n")
    click.echo(f"{'名称':<20} {'Project 字段'}")
    click.echo("-" * 40)
    
    for project in projects:
        project_field = project.yaml_front.get('project', '-')
        click.echo(f"{project.name:<20} {project_field}")


@cli.command()
@click.argument('name')
def tree(name):
    """生成项目文件树"""
    config = get_config()
    project_dir = config['project_dir']
    project_path = os.path.join(project_dir, name)
    
    if not os.path.exists(project_path):
        click.echo(f"错误: 项目 '{name}' 不存在")
        sys.exit(1)
    
    # 生成文件树
    click.echo(f"\n{name}")
    items = sorted(os.listdir(project_path))
    
    # 确保 README.md 在最前面
    if 'README.md' in items:
        items.remove('README.md')
        items.insert(0, 'README.md')
    
    for i, item in enumerate(items):
        item_path = os.path.join(project_path, item)
        is_dir = os.path.isdir(item_path)
        suffix = "/" if is_dir else ""
        
        # 最后一个用 └──，其他用 ├──
        prefix = "└── " if i == len(items) - 1 else "├── "
        click.echo(f"{prefix}[{item}{suffix}]({item}{suffix})")
    
    click.echo("\n文件树已生成，请复制使用")


@cli.command()
@click.option('--dry-run', is_flag=True, help='预览模式，不实际执行')
def collect(dry_run):
    """项目 → 笔记同步（单向）"""
    config = get_config()
    projects = scan_projects(config['project_dir'])
    collect_module(projects, config['note_dirs'], dry_run)


@cli.command()
@click.option('--dry-run', is_flag=True, help='预览模式，不实际执行')
def distribute(dry_run):
    """笔记 → 项目同步（单向）"""
    config = get_config()
    projects = scan_projects(config['project_dir'])
    notes = scan_notes(config['note_dirs'])
    distribute_module(notes, projects, dry_run)


@cli.command()
@click.argument('project_name', required=False)
@click.option('-v', '--verbose', is_flag=True, help='显示详细差异')
def diff_cmd(project_name, verbose):
    """查看项目和笔记的差异"""
    config = get_config()
    projects = scan_projects(config['project_dir'])
    notes = scan_notes(config['note_dirs'])
    
    if project_name:
        # 只检查指定项目
        project = next((p for p in projects if p.name == project_name), None)
        if not project:
            click.echo(f"错误: 项目 '{project_name}' 不存在")
            sys.exit(1)
        
        note_map = {n.yaml_front.get('project') or n.name: n for n in notes}
        note = note_map.get(project_name)
        
        from .diff import diff_project_note, print_diff
        result = diff_project_note(project, note)
        print_diff(result, verbose)
    else:
        # 检查所有项目
        diff(projects, notes, verbose)


@cli.command()
@click.argument('project')
@click.argument('note')
def link(project, note):
    """手动关联项目和笔记（通过修改 YAML）"""
    # 这个功能可选实现
    click.echo(f"关联功能待实现: {project} <-> {note}")
    click.echo("提示: 可以直接编辑笔记的 YAML front-matter 添加 project 字段")


@cli.command()
def config():
    """修改配置"""
    current_config = load_config()
    
    if current_config:
        click.echo("\n当前配置:")
        click.echo(f"  项目目录: {current_config['project_dir']}")
        click.echo(f"  笔记目录: {', '.join(current_config['note_dirs'])}")
    
    if click.confirm("\n要重新配置吗？"):
        create_config_interactive()


# 入口点
def main():
    cli()


if __name__ == '__main__':
    main()
