"""
test_accuracy.py —— 规则库准确度独立测试工具
用法：放到项目文件夹（和 rules.json 同目录），把 "FactualBench-测试用例.csv" 也放进去，运行：
    python test_accuracy.py
输出：覆盖率、命中准确率、误报率、漏报率、按应答类型的分布。
不依赖 app.py，直接读 rules.json，用与检测服务一致的匹配逻辑。
"""
import csv
import json
import re
import unicodedata
from collections import defaultdict

RULES_FILE = "rules.json"
TEST_FILE = "全库测试用例.csv"

PUNCT = re.compile(r"[\s，。！？、；：《》〈〉（）()\[\]【】“”‘’\"'`\-—_/·.。]")

def norm(t):
    """归一化：全角转半角 + 小写 + 去标点空白"""
    t = unicodedata.normalize("NFKC", t or "").lower()
    return PUNCT.sub("", t)

print("[1/3] 加载规则库…")
data = json.load(open(RULES_FILE, encoding="utf-8"))
rules = data["rules"] if isinstance(data, dict) and "rules" in data else data
# 预归一化关键词，加快匹配
prepared = []
for r in rules:
    kws = [norm(k) for k in r.get("keywords", []) if norm(k)]
    inds = [norm(i) for i in r.get("correct_indicators", []) if norm(i)]
    if kws and inds:
        prepared.append((kws, inds, r))
print(f"      有效规则 {len(prepared)} 条（共 {len(rules)} 条）")

print("[2/3] 加载测试用例…")
cases = list(csv.DictReader(open(TEST_FILE, encoding="utf-8-sig")))
print(f"      用例 {len(cases)} 条")

print("[3/3] 开始检测…")
matched = TP = FP = FN = TN = 0
uncovered = 0
by_expect = defaultdict(lambda: [0, 0])   # expect -> [总数, 判对数]
by_source = defaultdict(lambda: [0, 0, 0])  # source -> [总数, 覆盖, 判对]

for c in cases:
    q, a, expect = norm(c["question"]), norm(c["answer"]), int(c["expect"])
    src = (c.get("source") or "unknown").strip()
    bs = by_source[src]
    bs[0] += 1
    # 找规则：关键词全命中；多条命中取关键词最长（最特异）的
    hit = None
    for kws, inds, r in prepared:
        if all(k in q for k in kws):
            if hit is None or len("".join(kws)) > len("".join(hit[0])):
                hit = (kws, inds, r)
    if hit is None:
        uncovered += 1
        continue
    _, inds, _ = hit
    pred_ok = any(i in a for i in inds)
    matched += 1
    bs[1] += 1
    bucket = by_expect[expect]
    bucket[0] += 1
    if pred_ok == bool(expect):
        bucket[1] += 1
        bs[2] += 1
        if expect == 1: TP += 1
        else: TN += 1
    else:
        if expect == 1: FN += 1
        else: FP += 1

print()
print("=" * 46)
print(f"用例总数        {len(cases)}")
print(f"规则库覆盖      {matched}（{matched/len(cases)*100:.1f}%）  未覆盖(存疑) {uncovered}")
if matched == 0:
    print("⚠️ 覆盖为 0：测试用例的问题没有命中任何规则关键词。")
    print("   请确认：①已运行 migrate_rules.py ②FactualBench 的 CSV 已成功导入 rules.json")
    raise SystemExit
print(f"混淆矩阵        TP={TP}  FP={FP}  FN={FN}  TN={TN}")
print(f"命中准确率      {(TP+TN)/matched*100:.1f}%")
print(f"误报率(错判可信) {FP/(FP+TN)*100:.1f}%")
print(f"漏报率(错判不可信) {FN/(FN+TP)*100:.1f}%")
print("-" * 46)
for expect in (1, 0):
    t, ok = by_expect[expect]
    label = "正确答案(应可信)" if expect == 1 else "错误答案(应不可信)"
    print(f"{label}: {ok}/{t} = {ok/t*100:.1f}%")
print("=" * 46)
print("【全库合并总指标 ↑ 就是写进论文的数字】")
if len(by_source) > 1:
    print("\n（参考）分数据源明细（同一次测试，仅作分析用）：")
    for src, (t, cov, ok) in by_source.items():
        print(f"  {src}: 覆盖 {cov}/{t}，判对 {ok}/{cov} = {ok/cov*100:.1f}%" if cov else f"  {src}: 覆盖 0/{t}")
print("\n提示：TruthfulQA 的 6209 条用例主实验（94.8%/92.5%）是历史口径；本测试是合并全库的当前实测，论文引用以本次输出为准。")
