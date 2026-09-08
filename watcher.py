import os
import time
import subprocess
from pathlib import Path

DATA_FOLDER = "new_data"
PROCESSED_FOLDER = "processed"
CHECK_INTERVAL = 10  # 每10秒检查一次

def run_generator():
    """运行规则生成器"""
    try:
        result = subprocess.run(
            ["python", "auto_rule_generator.py"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        print(result.stdout)
        if result.stderr:
            print("错误:", result.stderr)
    except Exception as e:
        print(f"运行出错: {e}")

def get_file_list(folder):
    """获取文件夹里的文件列表"""
    path = Path(folder)
    if not path.exists():
        return set()
    return set(f.name for f in path.iterdir() if f.is_file())

def main():
    print("=" * 50)
    print("📁 求真眼 - 文件监控器")
    print(f"📂 监控文件夹: {DATA_FOLDER}/")
    print(f"⏱️  检查间隔: {CHECK_INTERVAL} 秒")
    print("=" * 50)
    print("📌 将 CSV 或 TXT 文件放入 new_data/ 文件夹")
    print("📌 系统会自动处理并生成规则")
    print("📌 按 Ctrl+C 停止监控")
    print("=" * 50)

    # 创建必要的文件夹
    Path(DATA_FOLDER).mkdir(exist_ok=True)
    Path(PROCESSED_FOLDER).mkdir(exist_ok=True)

    # 记录当前文件列表
    current_files = get_file_list(DATA_FOLDER)

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            new_files = get_file_list(DATA_FOLDER)

            # 检查是否有新文件
            added = new_files - current_files
            if added:
                print(f"\n🔔 检测到新文件: {', '.join(added)}")
                run_generator()
                current_files = get_file_list(DATA_FOLDER)  # 更新列表

    except KeyboardInterrupt:
        print("\n\n👋 监控已停止")

if __name__ == "__main__":
    main()