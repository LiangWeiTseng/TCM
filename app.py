import sys
import os

# 取得目前檔案所在的絕對路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
# 確保系統能找到 src 資料夾
sys.path.append(os.path.join(current_dir, "src"))

# 導入你的介面
from formula_altsearch.gui import demo 

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
