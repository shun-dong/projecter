import os
import json

from project import project
from distribute import distribute
from collect import collect

def sync(PROJECT_DIR, TARGET_READMES_DIRS):
    project(PROJECT_DIR)
    collect(PROJECT_DIR, TARGET_READMES_DIRS)
    for target_readmes_dir in TARGET_READMES_DIRS:
        distribute(PROJECT_DIR, target_readmes_dir)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(script_dir, 'config.json')
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    sync(config['project_dir'], config['note_dirs'])