import requests
import csv
import time

API_URL = "http://127.0.0.1:8080/check"

def load_data():
    """加载 TruthfulQA 中文版测试数据"""
    test_cases = []
    with open("processed/TrufulQA_zh.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            question = row.get("Question", "")
            correct = row.get("Correct Answers", "")
            incorrect = row.get("Incorrect Answers", "")
            
            try:
                correct_list = eval(correct) if correct else []
            except:
                correct_list = [c.strip() for c in correct.split(";")] if correct else []
            
            try:
                incorrect_list = eval(incorrect) if incorrect else []
            except:
                incorrect_list = [i.strip() for i in incorrect.split(";")] if incorrect else []
            
            for ans in correct_list:
                if ans and ans.strip():
                    test_cases.append((question, ans.strip(), "correct"))
            for ans in incorrect_list:
                if ans and ans.strip():
                    test_cases.append((question, ans.strip(), "incorrect"))
    return test_cases

def test_one(question, answer, expected):
    try:
        resp = requests.post(API_URL, json={"question": question, "answer": answer}, timeout=10)
        if resp.status_code != 200:
            return "error", f"HTTP {resp.status_code}", False
        data = resp.json()
        level = data.get("level", "")
        matched = "存疑" not in level
        if expected == "correct":
            correct = "可信" in level
        else:
            correct = "不可信" in level or "错误" in level
        return "pass" if correct else "fail", level, matched
    except Exception as e:
        return "error", str(e)[:30], False

print("=" * 60)
print("求真眼 - 817条规则全量测试")
print("=" * 60)

test_cases = load_data()
total = len(test_cases)
print(f"加载测试用例: {total} 条\n")

passed = 0
failed = 0
matched = 0
unmatched = 0

for i, (q, a, exp) in enumerate(test_cases, 1):
    status, level, is_matched = test_one(q, a, exp)
    if is_matched:
        matched += 1
        if status == "pass":
            passed += 1
        else:
            failed += 1
    else:
        unmatched += 1
    
    if i % 50 == 0:
        print(f"进度: {i}/{total}")

print("=" * 60)
print("测试完成!")
print("=" * 60)
print(f"总计: {total} 个测试用例")
print(f"匹配命中: {matched} 条 ({(matched/total*100):.1f}%)")
print(f"匹配失败(存疑): {unmatched} 条 ({(unmatched/total*100):.1f}%)")
print(f"其中判断正确: {passed} 条")
print(f"其中判断错误: {failed} 条")
if matched > 0:
    print(f"准确率(仅统计匹配命中的): {(passed/matched*100):.1f}%")
print("=" * 60)