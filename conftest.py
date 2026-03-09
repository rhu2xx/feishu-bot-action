import sys
import os

# 把 src/ 加入 Python 路径，让测试文件可以直接 import core/bot/bitable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
