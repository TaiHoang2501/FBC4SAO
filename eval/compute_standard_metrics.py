"""
compute_standard_metrics.py — Tính toán và chuẩn hóa 5 chỉ số đánh giá theo Luận văn:
  1. Routing Accuracy
  2. ROUGE-L
  3. LLM-as-a-Judge Semantic Similarity
  4. Citation Compliance Rate
  5. Response Time
Hỗ trợ cả Micro-Average (trung bình có trọng số theo mẫu - kết quả chính) và Macro-Average (theo kịch bản).
Chỉ chấp nhận dữ liệu từ giao thức đánh giá Live API E2E (results_improved_final.json),
nghiêm cấm fallback sai loại sang tệp của bài thử nghiệm khác (như comparative_results.json).
"""
import argparse
import json
import os
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent

SCENARIOS = {
    "S1": "Chẩn đoán Holland/RIASEC",
    "S2": "Tư vấn Ngoại khóa Nền tảng",
    "S3": "Tư vấn Ngoại khóa Chuyên sâu",
    "S4": "Hoạt động Cá nhân",
    "S5": "Đối chiếu Hồ sơ",
    "S6": "Đánh giá Toàn diện",
    "S7": "Hỏi đáp Tổng quát",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Tính toán Micro/Macro metrics cho Luận văn từ kết quả Live E2E")
    parser.add_argument("--file", type=str, default=None, help="Đường dẫn tệp kết quả Live E2E (mặc định: results_improved_final.json)")
    parser.add_argument("--output", type=str, default=None, help="Đường dẫn tệp xuất kết quả (mặc định: thesis_metrics.json)")
    return parser.parse_args()


def resolve_live_results_file(custom_path: str = None) -> Path:
    if custom_path:
        p = Path(custom_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Không tìm thấy tệp chỉ định: {custom_path}")
        return p

    candidates = [
        EVAL_DIR / "results_improved_final.json",
        Path("results_improved_final.json"),
        Path("eval/results_improved_final.json"),
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()

    raise FileNotFoundError(
        "Lỗi: Không tìm thấy tệp kết quả Live E2E 'results_improved_final.json'.\n"
        "Hệ thống từ chối tự động fallback sang 'comparative_results.json' vì đây là hai giao thức thực nghiệm hoàn toàn khác nhau "
        "(Live API đo bằng LLM-as-a-Judge vs Comparative Benchmark đo bằng BERTScore vi).\n"
        "Vui lòng chạy lại 'python eval/thesis_eval.py --live' hoặc cung cấp tệp qua tham số '--file'."
    )


def validate_and_extract_live_data(file_path: Path) -> tuple[list, dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Chặn trường hợp nạp nhầm comparative_results.json
    if isinstance(data, dict):
        prov = data.get("_provenance", {})
        if prov.get("evaluation_protocol") == "Comparative Pipeline Evaluation (4 architectures on 100 test queries)":
            raise ValueError(
                f"Lỗi chặn dữ liệu sai loại: Tệp '{file_path.name}' thuộc bài thử nghiệm 'Comparative Pipeline Evaluation' (đo bằng BERTScore), "
                f"không thể dùng để tổng hợp 'thesis_metrics.json' (vốn dành riêng cho hệ thống Live E2E). "
                f"Vui lòng cung cấp đúng tệp 'results_improved_final.json'."
            )
        if isinstance(data.get("details"), dict) and "Adaptive Agentic RAG" in data["details"]:
            raise ValueError(
                f"Lỗi chặn dữ liệu sai loại: Tệp '{file_path.name}' chứa cấu trúc phân rã của 4 pipeline so sánh đối chứng, "
                f"không phải kết quả đơn luồng Live API E2E chuẩn mực."
            )

    # 2. Trích xuất danh sách câu hỏi
    if isinstance(data, dict) and "details" in data and isinstance(data["details"], list):
        items = data["details"]
    elif isinstance(data, dict) and "results" in data and isinstance(data["results"], list):
        items = data["results"]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError(f"Cấu trúc tệp '{file_path.name}' không hợp lệ (không tìm thấy danh sách 'details' hoặc 'results').")

    if not items:
        raise ValueError(f"Tệp '{file_path.name}' rỗng, không có dữ liệu mẫu nào.")

    return items, data if isinstance(data, dict) else {}


def compute_metrics(items: list, file_path: Path, output_path: Path):
    print(f"📊 Đang đọc dữ liệu Live E2E chuẩn mực từ: {file_path}")
    print("=" * 125)
    print(f"{'Kịch bản Test':35s} {'Số câu':>8s} {'Routing':>10s} {'ROUGE-L':>10s} {'Semantic (LLM)':>16s} {'Citation Rate':>16s} {'Time (s)':>12s}")
    print("=" * 125)

    all_scenarios = []

    for sid, name in SCENARIOS.items():
        s_items = [d for d in items if d.get("scenario") == sid]
        n = len(s_items)
        if n == 0:
            continue

        routing_acc = sum(d.get("routing_correct", 0) for d in s_items) / n
        rouge_l = sum(d.get("rouge_l", 0) for d in s_items) / n
        sem_score = sum(d.get("semantic_similarity", d.get("bertscore", d.get("bertscore_f1", 0))) for d in s_items) / n
        citation_acc = sum(d.get("citation_compliance", d.get("citation_correct", 0)) for d in s_items) / n
        response_time = sum(d.get("response_time", 0.0) for d in s_items) / n

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
        all_scenarios.append(result)
        print(f"{sid}. {name:32s} {n:8d} {routing_acc:10.2f} {rouge_l:10.2f} {sem_score:16.2f} {citation_acc:16.2f} {response_time:12.2f}")

    print("=" * 125)

    total_samples = len(items)

    # 1. Micro-average (trung bình có trọng số theo từng mẫu - KẾT QUẢ CHÍNH CỦA LUẬN VĂN)
    micro_routing = sum(d.get("routing_correct", 0) for d in items) / total_samples
    micro_rouge = sum(d.get("rouge_l", 0) for d in items) / total_samples
    micro_sem = sum(d.get("semantic_similarity", d.get("bertscore", d.get("bertscore_f1", 0))) for d in items) / total_samples
    micro_cit = sum(d.get("citation_compliance", d.get("citation_correct", 0)) for d in items) / total_samples
    micro_time = sum(d.get("response_time", 0.0) for d in items) / total_samples

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
    k = len(all_scenarios)
    macro_avg = {
        "routing_accuracy": round(sum(r["routing_accuracy"] for r in all_scenarios) / k, 4),
        "rouge_l": round(sum(r["rouge_l"] for r in all_scenarios) / k, 4),
        "semantic_similarity": round(sum(r["semantic_similarity"] for r in all_scenarios) / k, 4),
        "citation_compliance_rate": round(sum(r["citation_compliance_rate"] for r in all_scenarios) / k, 4),
        "response_time": round(sum(r["response_time"] for r in all_scenarios) / k, 4),
        # Backward compatibility aliases:
        "bertscore": round(sum(r["semantic_similarity"] for r in all_scenarios) / k, 4),
        "citation_accuracy": round(sum(r["citation_compliance_rate"] for r in all_scenarios) / k, 4),
    }

    print(f"{'MICRO-AVERAGE (100 câu - KẾT QUẢ CHÍNH)':35s} {total_samples:8d} {micro_avg['routing_accuracy']:10.2f} {micro_avg['rouge_l']:10.2f} {micro_avg['semantic_similarity']:16.2f} {micro_avg['citation_compliance_rate']:16.2f} {micro_avg['response_time']:12.2f}")
    print(f"{'MACRO-AVERAGE (7 kịch bản)':35s} {total_samples:8d} {macro_avg['routing_accuracy']:10.2f} {macro_avg['rouge_l']:10.2f} {macro_avg['semantic_similarity']:16.2f} {macro_avg['citation_compliance_rate']:16.2f} {macro_avg['response_time']:12.2f}")

    # Đếm phương pháp chấm điểm ngữ nghĩa thực tế
    methods_count = {}
    for d in items:
        m = d.get("semantic_metric_method", "llm_judge")
        methods_count[m] = methods_count.get(m, 0) + 1

    # Xác định nhãn phương pháp ngữ nghĩa một cách khách quan dựa trên dữ liệu thực tế
    if list(methods_count.keys()) == ["llm_judge"]:
        sem_eval_desc = "LLM-as-a-Judge (Rubric-based Semantic Similarity, model: qwen2.5:7b-instruct-q4_K_M)"
    elif list(methods_count.keys()) == ["bert_score"]:
        sem_eval_desc = "BERTScore F1 (lang='vi') via bert_score library"
    else:
        sem_eval_desc = f"Hybrid/Cascaded Evaluation: {methods_count}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "source_file": file_path.name,
                "total_samples": total_samples,
                "total_scenarios": len(all_scenarios),
                "semantic_evaluation_method": sem_eval_desc,
                "semantic_metric_breakdown": methods_count,
                "citation_metric": "Citation Compliance Rate (Format [n] & Source Presence)",
                "primary_metric_aggregation": "micro_average (sample-level weighted across 100 benchmark items)",
                "note": "micro_average khớp 100% với results_improved_final.json; macro_average là trung bình không trọng số của 7 kịch bản."
            },
            "per_scenario": all_scenarios,
            "overall_micro_average": micro_avg,
            "overall_macro_average": macro_avg,
            # overall alias trỏ về micro_avg để đảm bảo tính nhất quán cao nhất
            "overall": micro_avg
        }, f, ensure_ascii=False, indent=2)

    print(f"\n📁 Đã lưu kết quả chuẩn hóa vào: {output_path}")


def main():
    args = parse_args()
    file_path = resolve_live_results_file(args.file)
    output_path = Path(args.output).resolve() if args.output else (EVAL_DIR / "thesis_metrics.json")
    items, raw_data = validate_and_extract_live_data(file_path)
    compute_metrics(items, file_path, output_path)


if __name__ == "__main__":
    main()
