from projecter import project
from distribute import distribute
from collect import collect


# 你自己的项目主目录（包含各项目子文件夹）
PROJECT_DIR = r"C:\Users\liuSu\Projects"   # 替换为你的实际路径
# 要同步到的目录
TARGET_READMES_DIR = r"C:\Users\liuSu\iCloudDrive\iCloud~md~obsidian\Note\Projects"  # 替换为你的实际路径

project(PROJECT_DIR)
distribute(PROJECT_DIR, TARGET_READMES_DIR)
collect(PROJECT_DIR, TARGET_READMES_DIR)
# TD检测冲突