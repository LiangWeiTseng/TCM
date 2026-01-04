import sys
import os

# 確保能找到 src 下的模組
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# 導入你的介面（根據你的專案結構）
from formula_altsearch.gui import demo 

if __name__ == "__main__":
    # HF 規定的固定埠口 7860
    demo.launch(server_name="0.0.0.0", server_port=7860)
