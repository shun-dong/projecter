from projecter import project
from distribute import distribute
from collect import collect


# 你自己的项目主目录（包含各项目子文件夹）
PROJECT_DIR = r"C:\Users\liuSu\Projects"   # 替换为你的实际路径
# 要同步到的目录
TARGET_READMES_DIR1 = r"C:\Users\liuSu\iCloudDrive\iCloud~md~obsidian\Note\Public"  # 替换为你的实际路径
TARGET_READMES_DIR2 = r"C:\Users\liuSu\iCloudDrive\iCloud~md~obsidian\Note\Flow"  # 替换为你的实际路径


project(PROJECT_DIR)
collect(PROJECT_DIR, [TARGET_READMES_DIR1, TARGET_READMES_DIR2])
distribute(PROJECT_DIR, TARGET_READMES_DIR1)
distribute(PROJECT_DIR, TARGET_READMES_DIR2)
