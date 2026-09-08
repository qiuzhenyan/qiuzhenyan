from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# =============================================================
# 从 rules.json 加载规则
# =============================================================
RULES_FILE = "rules.json"  # 和 app.py 在同一目录

def load_rules():
    try:
        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('rules', [])
    except FileNotFoundError:
        print(f"⚠️ 找不到 {RULES_FILE} 文件")
        return []
    except json.JSONDecodeError:
        print(f"⚠️ {RULES_FILE} 格式错误")
        return []

RULES = load_rules()
print(f"📋 已加载 {len(RULES)} 条规则")

def rule_based_check(question, answer):
    q = question.lower()
    a = answer.lower()
    
    for rule in RULES:
        keywords = rule.get('keywords', [])
        correct_indicators = rule.get('correct_indicators', [])
        message = rule.get('message', '')
        
        # 检查问题是否包含所有关键词
        match = True
        for kw in keywords:
            if kw not in q:
                match = False
                break
        
        if match:
            if any(ind in a for ind in correct_indicators):
                return {"level": "可信 ✅", "message": message}
            else:
                return {"level": "不可信 ❌", "message": message}
    
    return {"level": "存疑 ⚠️", "message": "暂无法判断，建议人工复核"}


@app.route('/check', methods=['POST'])
def check():
    data = request.json
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    
    if not question or not answer:
        return jsonify({"error": "请提供 question 和 answer 参数"}), 400
    
    result = rule_based_check(question, answer)
    return jsonify(result)


@app.route('/reload', methods=['POST'])
def reload_rules():
    """热重载规则（无需重启服务）"""
    global RULES
    RULES = load_rules()
    return jsonify({"message": f"规则已重载，当前 {len(RULES)} 条规则"})


@app.route('/rules', methods=['GET'])
def get_rules():
    return jsonify({"count": len(RULES)})


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': '求真眼API服务运行中',
        'status': 'online',
        'version': 'rule_based',
        'rules_count': len(RULES)
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)