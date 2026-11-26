import sys
import time
import subprocess
from pathlib import Path

DATA_FOLDER = "new_data"
PROCESSED_FOLDER = "processed"
CHECK_INTERVAL = 10

def run_generator():
    try:
        result = subprocess.run(
            [sys.executable, "auto_rule_generator.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    except Exception as e:
        print(f"RUN ERROR: {e}")

RELOAD_FLAG = Path(__file__).with_name(".rules_updated")


def notify_server():
    """生成完规则后发一个信号，让 app.py 那边立刻重载 rules.json。
    有没有这个文件都不影响功能：app.py 每次请求也会比对文件修改时间。"""
    try:
        RELOAD_FLAG.write_text(str(time.time()), encoding="utf-8")
    except Exception as e:
        print(f"NOTIFY ERROR: {e}")


def get_file_list(folder):
    path = Path(folder)
    if not path.exists():
        return set()
    return set(f.name for f in path.iterdir() if f.is_file())

def main():
    print("=" * 50)
    print("Qiuzhenyan Watcher STARTED")
    print(f"Watching: {DATA_FOLDER}/  interval: {CHECK_INTERVAL}s")
    print("Put CSV/TXT into new_data/ -> rules auto generated")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    Path(DATA_FOLDER).mkdir(exist_ok=True)
    Path(PROCESSED_FOLDER).mkdir(exist_ok=True)
    current_files = get_file_list(DATA_FOLDER)

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            new_files = get_file_list(DATA_FOLDER)
            added = new_files - current_files
            if added:
                print(f"\nNEW FILE: {', '.join(added)}")
                run_generator()
                notify_server()
                current_files = get_file_list(DATA_FOLDER)
    except KeyboardInterrupt:
        print("\nWatcher stopped")
main()