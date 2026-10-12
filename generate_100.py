import json
import random
import copy

with open('ground_truth.json', 'r', encoding='utf-8') as f:
    original_data = json.load(f)

# Ensure we have exactly 35 items
if len(original_data) > 35:
    original_data = original_data[:35]

prefixes = [
    "Cho mình hỏi, ",
    "Dạ cho em hỏi, ",
    "Bạn tư vấn giúp: ",
    "Xin chào, ",
    "Hệ thống cho mình biết, ",
    "Anh/chị ơi, ",
    "Tư vấn giúp em: ",
    "",
    "Câu hỏi của mình là: ",
    "Giải đáp giúp mình với: "
]

suffixes = [
    " Cảm ơn bạn.",
    " Trả lời giúp mình nhé.",
    " Mình đang cần gấp.",
    " Tư vấn chi tiết giúp mình.",
    " Nhờ hệ thống phân tích.",
    "",
    " Xin cảm ơn.",
    " Mong nhận được lời khuyên."
]

replacements = {
    "Em ": "Mình ",
    "Tôi ": "Mình ",
    "em ": "mình ",
    "tôi ": "mình ",
    "thích": "đam mê",
    "không biết": "chưa rõ",
    "phù hợp": "tương thích",
    "hồ sơ": "profile",
    "ngoại khóa": "hoạt động ngoại khóa",
    "làm sao": "cách nào"
}

new_data = copy.deepcopy(original_data)

# Generate variations until we reach ~105 questions (35 original + 70 new)
while len(new_data) < 105:
    for item in original_data:
        if len(new_data) >= 105:
            break
            
        new_item = copy.deepcopy(item)
        q = new_item['question']
        
        # Apply some random string replacements
        for k, v in replacements.items():
            if random.random() < 0.3:
                q = q.replace(k, v)
                
        # Add random prefix and suffix
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        
        # Make the question slightly different
        new_item['question'] = f"{prefix}{q.lower() if prefix else q}{suffix}"
        
        # Mark as auto-generated variation
        new_item['scenario_type'] = "variation"
        
        # Only add if it's uniquely different from existing
        if not any(x['question'] == new_item['question'] for x in new_data):
            new_data.append(new_item)

with open('ground_truth_105.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print(f"Generated 105 questions in ground_truth_105.json")
