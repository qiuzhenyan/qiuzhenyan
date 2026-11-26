"""
test_full.py —— 规模化基准测试与结果评估
【结项版】相比中期版的改动：
  改动1：用例构建从"1正1错"扩展为"1正 + 2错 + 同义改写1条"
  改动2：新增混淆矩阵（TP/FP/FN/TN）
  改动3：新增误报率、漏报率指标
  改动4：新增按规则类别的分层评估
  改动5：新增错误样本归因（自动归为三类）
  改动6：结果一次性打印成评估报告，可一键复现
"""
import os
from collections import defaultdict
from app import match_rule, verify_answer, RULES

# 构造"错误回答"用的通用错答池
WRONG_POOL = [
    "这个问题我不确定", "大概是错的说法", "完全没问题，肯定正确", "没有这回事", "42"
]
# 构造"同义改写问题"用的替换表（验证语义扩展是否生效）
PARAPHRASE = {
    "升起": "升起来", "落": "下山", "多少": "几度", "多久": "多长时间",
    "几天": "多少天", "看到": "看见", "几秒": "多少秒", "多高": "身高多少"
}
# 陷阱用例：否定句里含正确词，用来检验"误报"是否会被评估体系抓到（规则1、3各一条）
TRAP_RULE_IDS = {1, 3}


def build_cases():
    """每条规则展开成：1条正确回答 + 2条错误回答 + 1条同义改写问题"""
    cases = []
    for rule in RULES:
        q = "、".join(rule["keywords"])
        right = rule["correct_indicators"][0]

        # 1) 正确回答 -> 期望判可信
        cases.append({"q": q, "a": right, "expect_ok": True, "type": "正确回答", "rule": rule})
        # 2) 错误回答（取错答池）-> 期望判不可信
        for w in WRONG_POOL[:2]:
            cases.append({"q": q, "a": w, "expect_ok": False, "type": "错误回答", "rule": rule})
        # 3) 同义改写问题 + 正确回答 -> 期望判可信（检验语义扩展）
        pq = q
        for k, v in PARAPHRASE.items():
            pq = pq.replace(k, v)
        cases.append({"q": pq, "a": right, "expect_ok": True, "type": "同义改写", "rule": rule})
        # 4) 陷阱用例：否定句含正确词 -> 期望判不可信（检验误报检测能力）
        if rule["id"] in TRAP_RULE_IDS:
            cases.append({"q": q, "a": f"并不是{right}，这种说法不准确",
                          "expect_ok": False, "type": "否定句陷阱", "rule": rule})
    return cases


def attribute_error(case):
    """错误归因：把判错的用例自动归入三类典型错误"""
    if case["expect_ok"] and not case["pred_ok"]:
        return "正确答案表述变体未被指示词覆盖"
    if (not case["expect_ok"]) and case["pred_ok"]:
        return "关键词过泛/指示词过短导致误判可信"
    return "规则优先级冲突"


def main():
    cases = build_cases()
    total = len(cases)
    matched = 0
    TP = FP = FN = TN = 0
    by_cat = defaultdict(lambda: {"total": 0, "correct": 0})
    errors = defaultdict(int)

    for c in cases:
        rule = match_rule(c["q"])
        by_cat[c["rule"].get("category", "未分类")]["total"] += 1
        if rule is None:
            continue                      # 未匹配 = 未覆盖，不计入准确率
        matched += 1
        pred = verify_answer(rule, c["a"])
        c["pred_ok"] = pred

        if c["expect_ok"] and pred:
            TP += 1
        elif (not c["expect_ok"]) and pred:
            FP += 1
        elif c["expect_ok"] and not pred:
            FN += 1
        else:
            TN += 1

        if pred == c["expect_ok"]:
            by_cat[c["rule"].get("category", "未分类")]["correct"] += 1
        else:
            errors[attribute_error(c)] += 1

    coverage = matched / total * 100 if total else 0
    accuracy = (TP + TN) / matched * 100 if matched else 0
    fp_rate = FP / (FP + TN) * 100 if (FP + TN) else 0
    fn_rate = FN / (FN + TP) * 100 if (FN + TP) else 0

    print("=" * 52)
    print("求真眼 · 结项版评估报告")
    print("=" * 52)
    print(f"用例总数            : {total}")
    print(f"匹配到规则（已覆盖） : {matched}  -> 覆盖率 {coverage:.1f}%")
    print(f"未匹配（存疑）       : {total - matched}")
    print("-" * 52)
    print("混淆矩阵（以'回答是否正确'为真值）")
    print(f"  TP 正确判可信 : {TP:4d}    FP 错答判可信（误报）: {FP:4d}")
    print(f"  FN 对答判不可信（漏报）: {FN:4d}    TN 正确判不可信 : {TN:4d}")
    print("-" * 52)
    print(f"命中准确率 : {accuracy:.1f}%")
    print(f"误报率     : {fp_rate:.1f}%")
    print(f"漏报率     : {fn_rate:.1f}%")
    print("-" * 52)
    print("分层评估（按规则类别）")
    for cat, s in sorted(by_cat.items()):
        acc = s["correct"] / s["total"] * 100 if s["total"] else 0
        print(f"  {cat:4s} 用例 {s['total']:3d}  正确 {s['correct']:3d}  准确率 {acc:.1f}%")
    print("-" * 52)
    print("错误样本归因")
    if errors:
        for k, v in errors.items():
            print(f"  {k}: {v} 条")
    else:
        print("  无错误样本")
    print("=" * 52)


if __name__ == "__main__":
    main()