"""
求真眼 —— AI生成内容可信度检测插件
【结项版 app.py】相比中期版的改动：
  改动1：新增 normalize()  —— 输入归一化（全角转半角、大小写、去标点空白）
  改动2：新增 expand()     —— 同义词/表述变体扩展（"东边""东方"都归一成"东"）
  改动3：match_rule() 重写 —— 由"第一个命中就返回"改为"收集候选 + 特异性评分 + 优先匹配"
  改动4：/check 返回体     —— 增加命中规则ID、类别、判断依据（结果可解释性）
  改动5：新增 "/" 首页路由 —— 直接提供网页版检测界面（index.html，落实评审"交互软件设计"意见）
  改动6：新增 /check_batch —— 批量检测接口（落实"提升使用性"意见）
其余（Flask 骨架、三级标签、rules.json 加载方式）与中期版一致。
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import re
import unicodedata

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(__file__)
RULES_FILE = os.path.join(BASE_DIR, "rules.json")


def load_rules():
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        rules = json.load(f)["rules"]
    # 规则集里部分条目缺 id / category / strong / synonyms，这里补默认值，避免 KeyError
    for i, rule in enumerate(rules, start=1):
        rule.setdefault("id", i)
        rule.setdefault("category", "常识")
        rule.setdefault("strong", [])
        rule.setdefault("synonyms", {})
    return rules


# 【热重载】规则库改动后不用重启服务：每次请求比对 rules.json 的修改时间，
# 变了就重新加载（watcher.py / auto_rule_generator.py 写入新规则后立即生效）
RULES = load_rules()
_rules_mtime = os.path.getmtime(RULES_FILE) if os.path.exists(RULES_FILE) else 0


def refresh_rules():
    """规则文件变了就重载，返回当前规则列表。加载失败时沿用内存里的旧规则。"""
    global RULES, _rules_mtime
    try:
        mtime = os.path.getmtime(RULES_FILE)
    except OSError:
        return RULES
    if mtime != _rules_mtime:
        try:
            RULES = load_rules()
            _rules_mtime = mtime
            print(f"[热重载] rules.json 已更新，当前共 {len(RULES)} 条规则")
        except Exception as exc:  # 文件正在写入或 JSON 暂时不完整
            print(f"[热重载] 读取失败，继续使用旧规则：{exc}")
    return RULES

PUNCT = r"[\s，。！？、；：,.!?;:\"'“”‘’（）()\[\]【】\-—_/]"


def normalize(text: str) -> str:
    """【结项版·新增】输入归一化：全角转半角 + 小写 + 去标点空白"""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.lower()
    return re.sub(PUNCT, "", text)


def expand(text: str, synonyms: dict) -> str:
    """【结项版·新增】同义词扩展：把各种变体统一替换成标准词
    例：synonyms={"东": ["东边", "东方", "东侧"]}
        输入"太阳从东方升起" -> 变成"太阳从东升起"，与关键词"东"就能对上
    """
    for std, variants in (synonyms or {}).items():
        for v in variants:
            if v in text:
                text = text.replace(v, std)
    return text


def match_rule(question: str):
    """【结项版·重写】先收集所有候选规则，再按特异性评分排序，取最高的一条
    - 关键词：全部命中才成为候选（弱限定词也要求全部命中，防误触发）
    - 特异性评分：关键词越多越特异；强限定词（数字/专名）额外加权，排前面
    """
    q = normalize(question)
    candidates = []
    for rule in refresh_rules():
        q2 = expand(q, rule.get("synonyms", {}))
        if all(normalize(k) in q2 for k in rule["keywords"]):
            strong = rule.get("strong", [])
            score = len(rule["keywords"]) + 2 * sum(1 for s in strong if normalize(s) in q2)
            candidates.append((score, rule))

    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]


def verify_answer(rule, answer: str) -> bool:
    """校验回答：扩展同义词后，看是否包含任一正确答案指示词"""
    a = expand(normalize(answer), rule.get("synonyms", {}))
    return any(normalize(ind) in a for ind in rule["correct_indicators"])


@app.route("/check", methods=["POST"])
def check():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "")
    answer = data.get("answer", "")

    if not question or not answer:
        return jsonify({"code": 400, "message": "question 和 answer 不能为空"}), 400

    rule = match_rule(question)
    if rule is None:
        return jsonify({
            "score": None, "level": "存疑 ⚠️", "matched": False,
            "message": "规则库暂未覆盖该问题，建议人工核实。"
        })

    ok = verify_answer(rule, answer)
    result = {
        "score": 0.0 if ok else 1.0,
        "level": "可信 ✅" if ok else "不可信 ❌",
        "matched": True,
        # 【结项版·新增】可解释性：给出依据
        "rule_id": rule["id"],
        "category": rule.get("category", ""),
        "message": rule["message"],
    }
    return jsonify(result)


# 首页不缓存：改了 index.html 或规则库，刷新立刻看到，不会被浏览器旧副本挡住
@app.after_request
def no_cache_for_page(resp):
    if request.path in ("/", "/index.html"):
        resp.headers["Cache-Control"] = "no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
    return resp


@app.route("/stats", methods=["GET"])
def stats():
    rules = refresh_rules()
    cats = {}
    for r in rules:
        key = r.get("category") or "未分类"
        cats[key] = cats.get(key, 0) + 1
    return jsonify({
        "total_rules": len(rules),
        "by_category": cats,
        # 规则库最后一次更新的时间，页面据此显示"规则库已更新"
        "updated_at": os.path.getmtime(RULES_FILE) if os.path.exists(RULES_FILE) else None,
    })


# 【结项版·新增5】首页：直接提供网页版检测界面
@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


# 【结项版·新增6】批量检测接口：一次提交多条，返回全部结果
@app.route("/check_batch", methods=["POST"])
def check_batch():
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    if not isinstance(items, list) or not items:
        return jsonify({"code": 400, "message": "items 不能为空"}), 400
    if len(items) > 500:
        return jsonify({"code": 400, "message": "单次最多500条"}), 400

    refresh_rules()
    results = []
    for it in items:
        question = (it.get("question") or "").strip()
        answer = (it.get("answer") or "").strip()
        rule = match_rule(question) if question and answer else None
        if not question or not answer:
            results.append({"level": "参数错误 ⚠️", "matched": False,
                            "message": "question 和 answer 不能为空"})
        elif rule is None:
            results.append({"level": "存疑 ⚠️", "matched": False,
                            "message": "规则库暂未覆盖该问题，建议人工核实。"})
        else:
            ok = verify_answer(rule, answer)
            results.append({
                "level": "可信 ✅" if ok else "不可信 ❌",
                "matched": True,
                "rule_id": rule["id"],
                "category": rule.get("category", ""),
                "message": rule["message"],
            })
    ok_count = sum(1 for r in results if r["level"].startswith("可信") and "不可信" not in r["level"])
    bad_count = sum(1 for r in results if "不可信" in r["level"])
    return jsonify({
        "total": len(results),
        "ok": ok_count,
        "bad": bad_count,
        "doubt": len(results) - ok_count - bad_count,
        "results": results,
    })


if __name__ == "__main__":
    print(f"求真眼（结项版）已启动，规则库共 {len(RULES)} 条规则（改 rules.json 会自动热重载）")
    print(f"检测界面: http://127.0.0.1:8080/    接口: /check /check_batch /stats")
    app.run(host="0.0.0.0", port=8080)