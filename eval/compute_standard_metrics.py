"""
compute_standard_metrics.py — Tính toán và chuẩn hóa 5 chỉ số đánh giá theo Luận văn:
  1. Routing Accuracy
  2. ROUGE-L
  3. LLM-as-a-Judge Semantic Similarity
  4. Citation Compliance Rate
  5. Response Time
Hỗ trợ cả Micro-Average (trung bình có trọng số theo mẫu - kết quả chính) và Macro-Average (theo kịch bản).
"""
import json
import os
import glob
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent

# Ưu tiên results_improved_final.json làm nguồn chuẩn mực duy nhất
candidates = [
    EVAL_DIR / "results_improved_final.json",
    Path("results_improved_final.json"),
    EVAL_DIR / "comparative_results.json",
    Path("comparative_results.json"),
]
file_to_load = None
for c in candidates:
    if c.exists():
        file_to_load = str(c)
        break

if not file_to_load:
    json_files = list(EVAL_DIR.glob("*results*.json")) + glob.glob("*results*.json")
    if json_files:
        file_to_load = str(json_files[0])

if not file_to_load or not os.path.exists(file_to_load):
    print("Error: Could not find results file to load.")
    exit(1)

print(f"📊 Đang đọc dữ liệu từ: {file_to_load}")
with open(file_to_load, "r", encoding="utf-8") as f:
    data = json.load(f)

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

print("=" * 125)
print(f"{'Kịch bản Test':35s} {'Số câu':>8s} {'Routing':>10s} {'ROUGE-L':>10s} {'Semantic (LLM)':>16s} {'Citation Rate':>16s} {'Time (s)':>12s}")
print("=" * 125)

all_results = []

for sid, name in scenarios.items():
    items = [d for d in agentic if d.get("scenario") == sid]
    n = len(items)
    if n == 0:
        continue

    routing_acc = sum(d.get("routing_correct", 0) for d in items) / n
    rouge_l = sum(d.get("rouge_l", 0) for d in items) / n
    sem_score = sum(d.get("semantic_similarity", d.get("bertscore", d.get("bertscore_f1", 0))) for d in items) / n
    citation_acc = sum(d.get("citation_compliance", d.get("citation_correct", 0)) for d in items) / n
    response_time = sum(d.get("response_time", 0.0) for d in items) / n

    result = {
        "scenario": sid,
        "name": name,
        "n_samples": n,
        "routing_accuracy": round(routing_acc, 4),
        "rouge_l": round(rouge_l, 4),
        "semantic_similarity": round(sem_score, 4),
        "citation_compliance_rate": round(citation_acc, 4),
        "response_time": round(response_time, 4),
        # Backward compatibility aliases:
        "bertscore": round(sem_score, 4),
        "citation_accuracy": round(citation_acc, 4),
    }
    all_results.append(result)
    print(f"{sid}. {name:32s} {n:8d} {routing_acc:10.2f} {rouge_l:10.2f} {sem_score:16.2f} {citation_acc:16.2f} {response_time:12.2f}")

print("=" * 125)

if all_results:
    total_samples = len(agentic)

    # 1. Micro-average (tổng thể có trọng số theo từng mẫu - KẾT QUẢ CHÍNH CỦA LUẬN VĂN)
    micro_routing = sum(d.get("routing_correct", 0) for d in agentic) / total_samples
    micro_rouge = sum(d.get("rouge_l", 0) for d in agentic) / total_samples
    micro_sem = sum(d.get("semantic_similarity", d.get("bertscore", d.get("bertscore_f1", 0))) for d in agentic) / total_samples
    micro_cit = sum(d.get("citation_compliance", d.get("citation_correct", 0)) for d in agentic) / total_samples
    micro_time = sum(d.get("response_time", 0.0) for d in agentic) / total_samples

    micro_avg = {
        "routing_accuracy": round(micro_routing, 4),
        "rouge_l": round(micro_rouge, 4),
        "semantic_similarity": round(micro_sem, 4),
        "citation_compliance_rate": round(micro_cit, 4),
        "response_time": round(micro_time, 4),
        # Backward compatibility aliases:
        "bertscore": round(micro_sem, 4),
        "citation_accuracy": round(micro_cit, 4),
    }

    # 2. Macro-average (trung bình không trọng số của 7 kịch bản)
    k = len(all_results)
    macro_avg = {
        "routing_accuracy": round(sum(r["routing_accuracy"] for r in all_results) / k, 4),
        "rouge_l": round(sum(r["rouge_l"] for r in all_results) / k, 4),
        "semantic_similarity": round(sum(r["semantic_similarity"] for r in all_results) / k, 4),
        "citation_compliance_rate": round(sum(r["citation_compliance_rate"] for r in all_results) / k, 4),
        "response_time": round(sum(r["response_time"] for r in all_results) / k, 4),
        # Backward compatibility aliases:
        "bertscore": round(sum(r["semantic_similarity"] for r in all_results) / k, 4),
        "citation_accuracy": round(sum(r["citation_compliance_rate"] for r in all_results) / k, 4),
    }

    print(f"{'MICRO-AVERAGE (100 câu - KẾT QUẢ CHÍNH)':35s} {total_samples:8d} {micro_avg['routing_accuracy']:10.2f} {micro_avg['rouge_l']:10.2f} {micro_avg['semantic_similarity']:16.2f} {micro_avg['citation_compliance_rate']:16.2f} {micro_avg['response_time']:12.2f}")
    print(f"{'MACRO-AVERAGE (7 kịch bản)':35s} {total_samples:8d} {macro_avg['routing_accuracy']:10.2f} {macro_avg['rouge_l']:10.2f} {macro_avg['semantic_similarity']:16.2f} {macro_avg['citation_compliance_rate']:16.2f} {macro_avg['response_time']:12.2f}")

    # Đếm phương pháp chấm điểm
    methods_count = {}
    for d in agentic:
        m = d.get("semantic_metric_method", "llm_judge")
        methods_count[m] = methods_count.get(m, 0) + 1

    out_file = EVAL_DIR / "thesis_metrics.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "source_file": Path(file_to_load).name,
                "total_samples": total_samples,
                "total_scenarios": len(all_results),
                "semantic_evaluation_method": "LLM-as-a-Judge (Rubric-based Semantic Similarity)",
                "semantic_metric_breakdown": methods_count,
                "citation_metric": "Citation Compliance Rate (Format [n] & Source Presence)",
                "primary_metric_aggregation": "micro_average (sample-level weighted across 100 benchmark items)",
                "note": "micro_average khớp 100% với results_improved_final.json; macro_average là trung bình không trọng số của 7 kịch bản."
            },
            "per_scenario": all_results,
            "overall_micro_average": micro_avg,
            "overall_macro_average": macro_avg,
            # overall alias trỏ về micro_avg để đảm bảo tính nhất quán cao nhất
            "overall": micro_avg
        }, f, ensure_ascii=False, indent=2)
    print(f"\n📁 Đã lưu: {out_file}")
else:
    print("No valid results found to process.")
