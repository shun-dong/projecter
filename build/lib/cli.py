#!/usr/bin/env python3
import json
import os

import click

from distribute import distribute
from collect import collect
from project import project, make_front_matter
import sync as sync_module

# 注意，现在除了sync命令，其余都不会动笔记库

script_dir = os.path.dirname(os.path.abspath(__file__))
config_file_path = os.path.join(script_dir, 'config.json')
has_config = os.path.exists(config_file_path)
if has_config:
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

def make_config():
    config = {}
    project_dir = click.prompt("请输入项目根目录路径", type=str)
    config['project_dir'] = project_dir
    note_dirs = []
    while True:
        note_dir = click.prompt("请输入笔记库目录路径（输入空行结束）", type=str, default='')
        if not note_dir:
            break
        note_dirs.append(note_dir)
    config['note_dirs'] = note_dirs
    with open(config_file_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    return config

@click.group()
def cli():
    if not has_config:
        click.echo("未找到配置文件，开始创建配置...")
        global config
        config = make_config()
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        click.echo("配置文件创建完成。")

@cli.command()
def change_config():
    if has_config:
        if click.confirm("确定要修改配置吗？当前配置会被覆盖", default=False):
            global config
            config = make_config()
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            click.echo("配置文件修改完成。")

@cli.command()
@click.argument('name')
def new(name):
    project_dir = config['project_dir']
    project_path = os.path.join(project_dir, name)
    if os.path.exists(project_path):
        click.echo(f"项目 {name} 已存在，无法创建。")
    else:
        os.makedirs(project_path)
        readme_path = os.path.join(project_path, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(make_front_matter(name))
        click.echo(f"create new project {name}.")

@cli.command()
@click.argument("name")
def delete(name):
    project_dir = config['project_dir']
    project_path = os.path.join(project_dir, name)
    if not os.path.exists(project_path):
        click.echo(f"项目 {name} 不存在，无法删除。")
    else:
        if click.confirm(f"确定要删除项目 {name} 吗？此操作不可恢复！", default=False):
            import shutil
            shutil.rmtree(project_path)
            click.echo(f"项目 {name} 已删除。")



@cli.command()
def sync():
    sync_module.sync(
        config['project_dir'],
        config['note_dirs']
    )
    click.echo("projects synced.")

if __name__ == '__main__':
    cli()