import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "src"))

try:
    from formula_altsearch.gui import create_app
except ImportError as e:
    print(f"導入失敗：{e}")
    print("當前路徑內容:", os.listdir(os.path.join(current_dir, "src", "formula_altsearch")))
    raise

if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)
