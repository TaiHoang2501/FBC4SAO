"""
compute_standard_metrics.py — Tính toán 5 chỉ số đánh giá theo định nghĩa ở Mục 4.2:
  1. Routing Accuracy
  2. ROUGE-L
  3. BERTScore (F1)
  4. Citation Accuracy
  5. Response Time
"""
import json
import os
import glob

# Try to find the latest results file, or default to comparative_results.json / results_improved_final.json
file_to_load = "results_improved_final.json"
if not os.path.exists(file_to_load):
    if os.path.exists("comparative_results.json"):
        file_to_load = "comparative_results.json"
    else:
        # Just use the first json that looks like results
        json_files = glob.glob("*results*.json")
        if json_files:
            file_to_load = json_files[0]

if not os.path.exists(file_to_load):
    print(f"Error: Could not find results file to load.")
    exit(1)

with open(file_to_load, "r", encoding="utf-8") as f:
    data = json.load(f)

# The data format might be {"details": {"Adaptive Agentic RAG": [...]}} or {"details": [...]}
if isinstance(data.get("details"), dict) and "Adaptive Agentic RAG" in data["details"]:
    agentic = data["details"]["Adaptive Agentic RAG"]
elif isinstance(data.get("details"), list):
    agentic = data["details"]
else:
    print("Warning: Unrecognized data format, trying to parse as list of results.")
    agentic = data if isinstance(data, list) else data.get("details", [])

scenarios = {
    "S1": "Chẩn đoán Holland/RIASEC",
    "S2": "Tư vấn Ngoại khóa Nền tảng",
    "S3": "Tư vấn Ngoại khóa Chuyên sâu",
    "S4": "Hoạt động Cá nhân",
    "S5": "Đối chiếu Hồ sơ",
    "S6": "Đánh giá Toàn diện",
    "S7": "Hỏi đáp Tổng quát",
}

print("=" * 115)
print(f"{'Kịch bản Test':35s} {'Routing Acc':>12s} {'ROUGE-L':>10s} {'BERTScore':>10s} {'Citation Acc':>14s} {'Response Time(s)':>18s}")
print("=" * 115)

all_results = []

for sid, name in scenarios.items():
    items = [d for d in agentic if d.get("scenario") == sid]
    n = len(items)
    if n == 0:
        continue

    routing_acc = sum(d.get("routing_correct", 0) for d in items) / n
    rouge_l = sum(d.get("rouge_l", 0) for d in items) / n
    bertscore = sum(d.get("bertscore", d.get("bertscore_f1", 0)) for d in items) / n
    citation_acc = sum(d.get("citation_correct", 0) for d in items) / n
    response_time = sum(d.get("response_time", 0.0) for d in items) / n

    result = {
        "scenario": sid, "name": name,
        "routing_accuracy": round(routing_acc, 2),
        "rouge_l": round(rouge_l, 2),
        "bertscore": round(bertscore, 2),
        "citation_accuracy": round(citation_acc, 2),
        "response_time": round(response_time, 2)
    }
    all_results.append(result)
    print(f"{sid}. {name:32s} {routing_acc:12.2f} {rouge_l:10.2f} {bertscore:10.2f} {citation_acc:14.2f} {response_time:18.2f}")

print("=" * 115)

if all_results:
    # Overall
    oa = sum(r["routing_accuracy"] for r in all_results) / len(all_results)
    orouge = sum(r["rouge_l"] for r in all_results) / len(all_results)
    obert = sum(r["bertscore"] for r in all_results) / len(all_results)
    ocit = sum(r["citation_accuracy"] for r in all_results) / len(all_results)
    otime = sum(r["response_time"] for r in all_results) / len(all_results)
    print(f"{'TRUNG BÌNH':35s} {oa:12.2f} {orouge:10.2f} {obert:10.2f} {ocit:14.2f} {otime:18.2f}")

    with open("thesis_metrics.json", "w", encoding="utf-8") as f:
        json.dump({"per_scenario": all_results, "overall": {
            "routing_accuracy": round(oa, 2), "rouge_l": round(orouge, 2),
            "bertscore": round(obert, 2), "citation_accuracy": round(ocit, 2),
            "response_time": round(otime, 2)
        }}, f, ensure_ascii=False, indent=2)
    print(f"\n📁 Đã lưu: thesis_metrics.json")
else:
    print("No valid results found to process.")
