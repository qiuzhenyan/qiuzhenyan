"""
auto_rule_generator.py —— 自动化规则生成工具
【结项版】相比中期版的改动：
  改动1：生成规则时自动补 "strong" 字段 —— 含数字或长度>=3 的关键词视为强限定词
  改动2：生成规则时自动补 "synonyms" 字段 —— 常见单位/说法变体自动建表
  其余（扫描文件夹、解析CSV/TXT、合并入库、归档挪走）与中期版一致。
"""
import json
import csv
import os
import shutil

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="ignore")


BASE_DIR = os.path.dirname(__file__)
NEW_DATA_DIR = os.path.join(BASE_DIR, "new_data")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
RULES_FILE = os.path.join(BASE_DIR, "rules.json")

os.makedirs(NEW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# 【结项版·新增】常见表述变体表：生成规则时自动挂上，缓解"同义不同词"漏匹配
DEFAULT_SYNONYMS = {
    "多少": ["几度", "多少度", "几个", "几"],
    "多久": ["多长时间", "多少天", "几天"],
    "看到": ["看见", "可见", "看得到"],
    "升起": ["升", "升起来", "出来"],
    "落": ["落下", "下山"],
}


def load_rules():
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_rules(data):
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_txt(filepath):
    pairs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "," in line:
                q, a = line.split(",", 1)
                pairs.append((q.strip(), a.strip()))
    return pairs


def parse_csv(filepath):
    pairs = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            q = (row.get("question") or "").strip()
            a = (row.get("answer") or "").strip()
            if q and a:
                pairs.append((q, a))
    return pairs


def extract_keywords(q):
    """停用词过滤 + 按标点切词（遇到停用词先保存再清空，修复中期版丢词的bug）"""
    stopwords = set("的的了吗呢吧啊在是和与对关于什么多少怎么请问一下有会能吗?")
    words, buf = [], ""

    def flush():
        nonlocal buf
        if len(buf) >= 2 and buf not in stopwords:
            words.append(buf)
        buf = ""

    for ch in q:
        if ch.isspace() or ch in ",，。?？!！":
            flush()
        elif ch not in stopwords:
            buf += ch
        else:
            flush()
    flush()
    return words


def make_rule(q, a, next_id):
    words = extract_keywords(q)
    if not words:
        return None
    keywords = words[:4]
    # 【结项版·新增】自动标注强限定词：含数字，或长度>=4的实体词
    # （长度>=4 是因为 2-3 字常出现"圈需要""长时间"这类切词残缺，不具特异性）
    strong = [w for w in keywords if any(c.isdigit() for c in w) or len(w) >= 4]
    # 【结项版·新增】自动挂载同义词表（只挂命中的那几条，避免每条规则都带一大坨）
    synonyms = {k: v for k, v in DEFAULT_SYNONYMS.items() if k in "".join(keywords)}

    return {
        "id": next_id,
        "category": "自动导入",
        "keywords": keywords,
        "strong": strong,
        "synonyms": synonyms,
        "correct_indicators": [a],
        "message": f"正确参考答案：{a}",
    }


def main():
    data = load_rules()
    rules = data["rules"]
    next_id = max((r["id"] for r in rules), default=0) + 1
    added = 0

    for fname in sorted(os.listdir(NEW_DATA_DIR)):
        path = os.path.join(NEW_DATA_DIR, fname)
        if not os.path.isfile(path):
            continue
        if fname.endswith(".csv"):
            pairs = parse_csv(path)
        elif fname.endswith(".txt"):
            pairs = parse_txt(path)
        else:
            continue

        for q, a in pairs:
            rule = make_rule(q, a, next_id)
            if rule:
                rules.append(rule)
                next_id += 1
                added += 1

        shutil.move(path, os.path.join(PROCESSED_DIR, fname))
        print(f"[完成] {fname}: 提取 {len(pairs)} 条问答对")

    save_rules(data)
    print(f"本次新增 {added} 条规则，规则库现有 {len(rules)} 条")


if __name__ == "__main__":
    main()