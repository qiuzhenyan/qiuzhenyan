"""
migrate_rules.py —— 规则库格式升级工具
作用：给现有规则库批量补上 id / strong / synonyms 字段（一次运行即可），
     迁移前自动备份，已有字段的条目不会被覆盖。
用法：放到项目文件夹（和 rules.json 同目录），运行 python migrate_rules.py
"""
import json
import shutil
from datetime import datetime

FILE = "rules.json"

# 常见表述变体（与结项版一致；只挂命中的，不乱加）
DEFAULT_SYNONYMS = {
    "多少": ["几度", "多少度", "几个"], "多久": ["多长时间", "多少天", "几天"],
    "看到": ["看见", "可见"], "升起": ["升", "升起来", "出来"], "落": ["落下", "下山"],
    "发生什么": ["会怎么样", "会怎样"], "起源于": ["发源于", "源自"],
    "为什么": ["为啥", "为何"], "多久之前": ["多长时间"],
}

# 1) 备份
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy(FILE, f"rules_backup_{stamp}.json")
print(f"[1/4] 已备份为 rules_backup_{stamp}.json")

# 2) 读取
data = json.load(open(FILE, encoding="utf-8"))
wrapper = isinstance(data, dict) and "rules" in data
rules = data["rules"] if wrapper else data
print(f"[2/4] 规则库共 {len(rules)} 条，开始升级格式")

# 3) 逐条补字段（已有的不动）
patched = 0
for i, r in enumerate(rules, start=1):
    changed = False
    if "id" not in r:
        r["id"] = i
        changed = True
    if "category" not in r:
        r["category"] = "常识"
        changed = True
    if "keywords" in r and "strong" not in r:
        # 强限定词：含数字 或 长度>=4 的关键词
        r["strong"] = [k for k in r["keywords"] if any(c.isdigit() for c in k) or len(k) >= 4]
        changed = True
    if "synonyms" not in r:
        joined = "".join(r.get("keywords", []))
        r["synonyms"] = {k: v for k, v in DEFAULT_SYNONYMS.items() if k in joined}
        changed = True
    if "message" not in r:
        r["message"] = "、".join(r.get("correct_indicators", []))[:50]
        changed = True
    if changed:
        patched += 1

print(f"[3/4] 升级完成：{patched} 条被补齐字段，原有字段全部保留")

# 4) 写回
if wrapper:
    data["rules"] = rules
    json.dump(data, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
else:
    json.dump(rules, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"[4/4] 已写回 {FILE}")
print("现在重新运行 python auto_rule_generator.py 或把 CSV 放进 new_data/ 即可正常导入。")