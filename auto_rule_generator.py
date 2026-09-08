import csv
import json
import re
import shutil
from pathlib import Path

DATA_FOLDER = "new_data"
PROCESSED_FOLDER = "processed"
RULES_FILE = "rules.json"
SUPPORTED_EXTENSIONS = ['.csv', '.txt']

def extract_keywords(text, max_keywords=3):
    words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', text)
    words = [w for w in words if len(w) >= 2]
    return words[:max_keywords] if words else [text[:2]]

def process_csv(filepath):
    rules = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                question = row.get('Question', '') or row.get('问题', '') or row.get('question', '')
                correct = row.get('Correct Answers', '') or row.get('正确答案', '') or row.get('correct', '')
                if not question or not correct:
                    continue
                keywords = extract_keywords(question, 3)
                correct_indicators = extract_keywords