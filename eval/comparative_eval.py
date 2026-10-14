"""
comparative_eval.py — So sánh 4 Pipeline trên 100 Câu hỏi Thử nghiệm (7 Kịch bản)

Pipeline:
  1. Standalone LLM    : Chỉ gọi LLM, không truy xuất
  2. Naive RAG         : Vector search đơn giản + generic prompt
  3. Hybrid RAG        : BM25 + Vector + RRF + Reranker + generic prompt
  4. Agentic RAG (đề xuất): Full pipeline (Router + Hybrid + Rerank + Agent Prompt)

Chỉ số:
  - ROUGE-L, BERTScore F1, Citation Accuracy, Routing Accuracy

Chạy:
  uv run python comparative_eval.py
  uv run python comparative_eval.py --output results.json
"""

import json, os, re, sys, time, argparse
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from llm_service import call_llm
from data_loader import embed_texts
from vector_db import get_storage
from reranker import rerank
from agents import route_question, agent_search, build_agent_prompt, get_agent_display

# ── Load ground truth ─────────────────────────────────────────────────────────
GT_PATH = Path(__file__).resolve().parent / "ground_truth_final.json" if (Path(__file__).resolve().parent / "ground_truth_final.json").exists() else Path("ground_truth_final.json")
with open(GT_PATH, "r", encoding="utf-8") as f:
    DATASET = json.load(f)

# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_rouge_l(reference: str, hypothesis: str) -> float:
    """ROUGE-L based on Longest Common Subsequence."""
    def clean(t: str) -> str:
        if not t:
            return ""
        # 1. Loại bỏ khối nguồn ở cuối câu trả lời (khớp Nguồn:, Nguồn tham khảo:, Sources:, **Nguồn:**, v.v.)
        source_pattern = r"(?i)(?:\n+|\s+)(?:\*\*|\*|#+)?\s*(?:nguồn(?:s|\s*(?:tham\s*khảo|trích\s*dẫn|tài\s*liệu|gốc))?|sources?)\s*(?:\*\*|\*)?\s*:"
        t = re.split(source_pattern, t)[0]
        # Loại bỏ nếu tiền tố nguồn nằm ở đầu dòng riêng
        t = re.split(r"(?i)^\s*(?:\*\*|\*|#+)?\s*(?:nguồn(?:s|\s*(?:tham\s*khảo|trích\s*dẫn))?|sources?)\s*(?:\*\*|\*)?\s*:", t, flags=re.MULTILINE)[0]
        # 2. Loại bỏ các ký hiệu trích dẫn inline dạng [1], [2], [1, 2], [1][2]
        t = re.sub(r"\[\d+(?:[,\s]+\d+)*\]", "", t)
        return t.strip()

    def lcs(a, b):
        m, n = len(a), len(b)
        dp = [0] * (n + 1)
        for i in range(m):
            ndp = [0] * (n + 1)
            for j in range(n):
                if a[i] == b[j]: ndp[j+1] = dp[j] + 1
                else: ndp[j+1] = max(dp[j+1], ndp[j])
            dp = ndp
        return dp[n]

    ref = re.findall(r'\w+', clean(reference).lower(), re.UNICODE)
    hyp = re.findall(r'\w+', clean(hypothesis).lower(), re.UNICODE)
    if not ref or not hyp: return 0.0
    l = lcs(ref, hyp)
    r, p = l / len(ref), l / len(hyp)
    return (2 * r * p) / (r + p) if (r + p) > 0 else 0.0


def compute_semantic_similarity(reference: str, hypothesis: str) -> tuple[float, str]:
    """
    Tính độ tương đồng ngữ nghĩa và ghi nhận chính xác phương pháp tính:
    Returns:
        (score, method):
        - score: Điểm số từ 0.0 đến 1.0
        - method:
            * "bert_score": Tính qua thư viện bert_score chuẩn (ngôn ngữ vi).
            * "embedding_cosine": Dự phòng Cosine similarity từ vector embedding (multilingual-e5-large).
            * "empty_input": Câu trả lời hoặc tham chiếu rỗng -> gán 0.0.
    """
    if not reference or not reference.strip() or not hypothesis or not hypothesis.strip():
        return 0.0, "empty_input"
    try:
        from bert_score import score as bscore
        P, R, F1 = bscore([hypothesis], [reference], lang="vi", verbose=False)
        return float(F1[0]), "bert_score"
    except Exception:
        # Fallback: dùng embedding cosine similarity
        try:
            ref_vec = embed_texts([reference], is_query=False)[0]
            hyp_vec = embed_texts([hypothesis], is_query=False)[0]
            import math
            dot = sum(a * b for a, b in zip(ref_vec, hyp_vec))
            nr = math.sqrt(sum(a * a for a in ref_vec))
            nh = math.sqrt(sum(b * b for b in hyp_vec))
            sim = dot / (nr * nh) if nr * nh > 0 else 0.0
            return max(0.0, min(1.0, float(sim))), "embedding_cosine"
        except Exception:
            return 0.0, "failed"


def compute_bertscore(reference: str, hypothesis: str) -> float:
    """Wrapper tương thích ngược trả về điểm số float."""
    score, _ = compute_semantic_similarity(reference, hypothesis)
    return score


def extract_citation_indices(text: str) -> list[int]:
    """
    Trích xuất tất cả các chỉ số tài liệu được trích dẫn trong văn bản.
    Hỗ trợ định dạng: [1], [2], [1, 2], [1, 2, 3], [1][2].
    """
    if not text:
        return []
    raw_blocks = re.findall(r"\[([\d\s,]+)\]", text)
    indices = []
    for block in raw_blocks:
        for num_str in re.findall(r"\d+", block):
            indices.append(int(num_str))
    return indices


def compute_citation(answer: str, sources: list) -> float:
    """
    Kiểm tra tuân thủ trích dẫn và tính hợp lệ của nguồn tham chiếu (Citation Compliance & Source Index Validity):
    
    Quy tắc chấm điểm (0.0 hoặc 1.0):
    1. Trả về 0.0 nếu câu trả lời rỗng hoặc chỉ có khoảng trắng.
    2. Trả về 0.0 nếu hệ thống không có tài liệu nguồn được truy xuất (sources rỗng).
    3. Trả về 0.0 nếu câu trả lời không chứa bất kỳ ký hiệu trích dẫn [n] nào.
    4. Trả về 0.0 nếu có bất kỳ trích dẫn nào trỏ đến nguồn KHÔNG TỒN TẠI:
       - Chỉ số <= 0
       - Chỉ số > len(sources) (ví dụ: trích dẫn [5] trong khi chỉ có 2 nguồn tài liệu được retrieved).
    5. Trả về 1.0 khi và chỉ khi:
       - Có ít nhất một trích dẫn [n] hợp lệ.
       - TẤT CẢ các chỉ số trích dẫn trong câu trả lời đều nằm trong phạm vi tài liệu thực tế [1, len(sources)].

    Lưu ý học thuật: Thước đo này đánh giá tính tuân thủ hình thức trích dẫn và tính toàn vẹn của chỉ mục
    tài liệu tham chiếu (Format & Source Index Integrity), ngăn chặn hiện tượng trích dẫn nguồn ảo / bịa đặt số thứ tự.
    """
    if not answer or not answer.strip():
        return 0.0
    if not sources or len(sources) == 0:
        return 0.0

    cited_indices = extract_citation_indices(answer)
    if not cited_indices:
        return 0.0

    # Kiểm tra tính tồn tại của từng nguồn được trích dẫn
    max_source_idx = len(sources)
    for idx in cited_indices:
        if idx <= 0 or idx > max_source_idx:
            # Citation trỏ đến nguồn không tồn tại trong danh sách retrieved!
            return 0.0

    return 1.0


def evaluate_routing_accuracy(predicted_agent: str | None, expected_agent: str, has_router: bool = True) -> float | None:
    """
    Đánh giá độ chính xác định tuyến tác tử (Routing Accuracy):
    - has_router = False: Trả về None (N/A) do pipeline không sở hữu module Query Router.
    - has_router = True: 1.0 nếu predicted_agent khớp expected_agent, ngược lại 0.0.
    """
    if not has_router:
        return None
    if not predicted_agent:
        return 0.0
    return 1.0 if str(predicted_agent).strip() == str(expected_agent).strip() else 0.0


# ── 4 Pipeline ────────────────────────────────────────────────────────────────

GENERIC_SYSTEM_PROMPT = (
    "Bạn là chuyên gia tư vấn hướng nghiệp Holland RIASEC và hoạt động ngoại khóa. "
    "Trả lời chính xác, có trích dẫn nguồn dạng [n]. "
    "Luôn liệt kê 'Nguồn: [n] tên_tệp' ở cuối câu trả lời."
)


def pipeline_standalone_llm(question: str) -> dict:
    """Pipeline 1: Chỉ LLM, không truy xuất."""
    t0 = time.time()
    messages = [
        {"role": "system", "content": GENERIC_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    answer = call_llm(messages, temperature=0.2, max_tokens=1500)
    return {
        "answer": answer,
        "sources": [],
        "agent": "none",
        "time": time.time() - t0,
    }


def pipeline_naive_rag(question: str) -> dict:
    """Pipeline 2: Vector search đơn giản + generic prompt."""
    t0 = time.time()
    q_vec = embed_texts([question], is_query=True)[0]
    store = get_storage()
    found = store.search(q_vec, top_k=5)
    contexts, sources = found["contexts"], found["sources"]

    if not contexts:
        return {"answer": "Không tìm thấy thông tin.", "sources": [], "agent": "naive", "time": time.time() - t0}

    ctx_block = "\n\n".join(
        f"[{i+1}] (Nguồn: {s})\n{c}" for i, (c, s) in enumerate(zip(contexts, sources))
    )
    messages = [
        {"role": "system", "content": GENERIC_SYSTEM_PROMPT},
        {"role": "user", "content": f"Ngữ cảnh:\n{ctx_block}\n\nCâu hỏi: {question}"},
    ]
    answer = call_llm(messages, temperature=0.2, max_tokens=1500)
    return {"answer": answer, "sources": sources, "agent": "naive", "time": time.time() - t0}


def pipeline_hybrid_rag(question: str) -> dict:
    """Pipeline 3: Hybrid Search + Reranker + generic prompt (không routing)."""
    t0 = time.time()
    q_vec = embed_texts([question], is_query=True)[0]
    store = get_storage()
    found = store.hybrid_search(query=question, query_vector=q_vec, top_k=20)
    reranked = rerank(query=question, contexts=found["contexts"], sources=found["sources"], top_k=5)
    contexts, sources = reranked["contexts"], reranked["sources"]

    if not contexts:
        return {"answer": "Không tìm thấy thông tin.", "sources": [], "agent": "hybrid", "time": time.time() - t0}

    ctx_block = "\n\n".join(
        f"[{i+1}] (Nguồn: {s})\n{c}" for i, (c, s) in enumerate(zip(contexts, sources))
    )
    messages = [
        {"role": "system", "content": GENERIC_SYSTEM_PROMPT},
        {"role": "user", "content": f"Ngữ cảnh:\n{ctx_block}\n\nCâu hỏi: {question}"},
    ]
    answer = call_llm(messages, temperature=0.2, max_tokens=1500)
    return {"answer": answer, "sources": sources, "agent": "hybrid", "time": time.time() - t0}


def pipeline_agentic_rag(question: str) -> dict:
    """Pipeline 4 (Đề xuất): Full Adaptive Agentic RAG."""
    t0 = time.time()
    agent = route_question(question)
    search_results = agent_search(question, agent)
    contexts = search_results["contexts"]
    sources = search_results["sources"]
    db_status = search_results.get("db_status", "ok")

    if not contexts:
        return {
            "answer": "Không tìm thấy thông tin.",
            "sources": [], "agent": agent.agent_id,
            "time": time.time() - t0,
        }

    messages = build_agent_prompt(question, contexts, sources, agent, history=[], db_status=db_status)
    answer = call_llm(messages, temperature=0.2, max_tokens=1500)
    return {
        "answer": answer,
        "sources": sources,
        "agent": agent.agent_id,
        "time": time.time() - t0,
    }


PIPELINES = {
    "Standalone LLM":      pipeline_standalone_llm,
    "Naive RAG":           pipeline_naive_rag,
    "Hybrid RAG":          pipeline_hybrid_rag,
    "Adaptive Agentic RAG": pipeline_agentic_rag,
}


# ── Main evaluation ──────────────────────────────────────────────────────────

def run_comparative_eval(use_bertscore: bool = True):
    all_results = {}

    for pipe_name, pipe_fn in PIPELINES.items():
        print(f"\n{'='*70}")
        print(f"  PIPELINE: {pipe_name}")
        print(f"{'='*70}")
        results = []

        for i, item in enumerate(DATASET):
            q = item["question"]
            ref = item["reference"]
            expected = item["expected_agent"]
            print(f"  [{i+1}/{len(DATASET)}] {item['scenario']}/{item['scenario_type']}: {q[:50]}...")

            try:
                out = pipe_fn(q)
            except Exception as e:
                print(f"    ⚠ ERROR: {e}")
                out = {"answer": f"Error: {e}", "sources": [], "agent": "error", "time": 0}

            # Compute metrics
            rouge = compute_rouge_l(ref, out["answer"])
            if use_bertscore:
                bert, sem_method = compute_semantic_similarity(ref, out["answer"])
            else:
                bert, sem_method = 0.0, "disabled"
            citation = compute_citation(out["answer"], out.get("sources", []))
            has_router = (pipe_name == "Adaptive Agentic RAG")
            routing = (1.0 if out["agent"] == expected else 0.0) if has_router else None

            results.append({
                "scenario": item["scenario"],
                "type": item["scenario_type"],
                "question": q,
                "expected_agent": expected,
                "predicted_agent": out["agent"],
                "routing_correct": routing,
                "rouge_l": round(rouge, 4),
                "semantic_similarity": round(bert, 4),
                "semantic_metric_method": sem_method,
                "citation": citation,
                "response_time": round(out["time"], 2),
                "answer_preview": out["answer"][:200],
                # Backward compatibility aliases:
                "bertscore_f1": round(bert, 4),
            })
            print(f"    → ROUGE={rouge:.3f} Sem={bert:.3f} ({sem_method}) Cite={citation:.0f} Time={out['time']:.1f}s Agent={out['agent']}")

        all_results[pipe_name] = results

    return all_results


def compute_latency_percentiles(times: list) -> tuple[float, float, float]:
    """
    Tính toán chỉ số độ trễ: Average, Median (p50), và 95th Percentile (p95).
    Quy ước thống kê (Percentile Convention):
    - Trung bình (Average): sum(times) / n
    - Trung vị (Median / p50): 50th percentile theo phương pháp nội suy tuyến tính (Linear Interpolation, Type 7).
    - Phân vị 95 (p95): 95th percentile theo phương pháp nội suy tuyến tính (Linear Interpolation, Type 7 - chuẩn NIST / SciPy).
    """
    if not times:
        return 0.0, 0.0, 0.0
    n = len(times)
    avg_val = round(sum(times) / n, 2)
    try:
        import numpy as np
        p50_val = round(float(np.percentile(times, 50)), 2)
        p95_val = round(float(np.percentile(times, 95)), 2)
    except ImportError:
        import math
        s = sorted(times)
        def _percentile(data, p):
            idx = (len(data) - 1) * p
            low, high = math.floor(idx), math.ceil(idx)
            w = idx - low
            return data[low] * (1.0 - w) + data[high] * w
        p50_val = round(_percentile(s, 0.50), 2)
        p95_val = round(_percentile(s, 0.95), 2)
    return avg_val, p50_val, p95_val


def compute_summary(all_results: dict) -> dict:
    """Tính trung bình các chỉ số cho từng pipeline."""
    summary = {}
    for pipe_name, results in all_results.items():
        n = len(results)
        # Chỉ pipeline có bộ định tuyến (Adaptive Agentic RAG) mới có routing_accuracy
        has_router = (pipe_name == "Adaptive Agentic RAG")
        routing_val = round(sum(r["routing_correct"] for r in results if r.get("routing_correct") is not None) / n, 4) if has_router else None
        
        times = [r.get("response_time", r.get("time", 0.0)) for r in results]
        avg_time, p50_time, p95_time = compute_latency_percentiles(times)

        # Phân rã phương pháp đo ngữ nghĩa thực tế
        methods_count = {}
        for r in results:
            m = r.get("semantic_metric_method", "unknown")
            methods_count[m] = methods_count.get(m, 0) + 1

        # Phân tách rõ ràng điểm BERTScore F1 thuần và Embedding Cosine (không gộp mập mờ hai thang đo khác nhau)
        bert_scores = [r.get("semantic_similarity", 0.0) for r in results if r.get("semantic_metric_method") == "bert_score"]
        emb_scores = [r.get("semantic_similarity", 0.0) for r in results if r.get("semantic_metric_method") == "embedding_cosine"]

        bert_avg = round(sum(bert_scores) / len(bert_scores), 4) if bert_scores else None
        emb_avg = round(sum(emb_scores) / len(emb_scores), 4) if emb_scores else None

        # Điểm semantic similarity tổng hợp của tất cả các mẫu:
        sem_all = round(sum(r.get("semantic_similarity", r.get("bertscore_f1", 0.0)) for r in results) / n, 4)

        summary[pipe_name] = {
            "rouge_l":                  round(sum(r["rouge_l"] for r in results) / n, 4),
            "semantic_similarity":      sem_all,
            "semantic_metric_breakdown": methods_count,
            "bertscore_f1_pure":        bert_avg,
            "embedding_cosine_pure":    emb_avg,
            "citation_compliance_rate": round(sum(r["citation"] for r in results) / n, 4),
            "routing_accuracy":         routing_val,
            "routing_supported":        has_router,
            "response_time_avg":        avg_time,
            "response_time_p50":        p50_time,
            "response_time_p95":        p95_time,
            # Backward compatibility aliases:
            "bertscore_f1":             sem_all,
            "citation_accuracy":        round(sum(r["citation"] for r in results) / n, 4),
            "n_samples":                n,
        }
    return summary


def print_comparison_table(summary: dict):
    """In bảng so sánh đẹp ra terminal."""
    thresholds = {
        "rouge_l":                  0.10,  # Chuẩn hóa ngưỡng khả thi cho RAG tiếng Việt
        "semantic_similarity":      0.75,
        "citation_compliance_rate": 0.80,
        "routing_accuracy":         0.85,
        "response_time_avg":        15.0
    }

    print(f"\n{'='*95}")
    print(f"{'BẢNG SO SÁNH HIỆU QUẢ 4 PIPELINE (COMPARATIVE PIPELINE EVALUATION)':^95}")
    print(f"{'='*95}")
    header = f"{'Chỉ số':<26}" + "".join(f"{name:>17}" for name in summary.keys())
    print(header)
    print("-" * 95)

    metrics = [
        ("ROUGE-L",                  "rouge_l"),
        ("Semantic Similarity",      "semantic_similarity"),
        ("Citation Compliance Rate", "citation_compliance_rate"),
        ("Routing Accuracy",         "routing_accuracy"),
        ("Response Time Avg (s)",    "response_time_avg"),
        ("Response Time p95 (s)",    "response_time_p95"),
    ]
    for label, key in metrics:
        row = f"{label:<26}"
        for name, s in summary.items():
            val = s.get(key)
            threshold = thresholds.get(key)
            if val is None:
                row += f"{'N/A':>13}   "
            elif key.startswith("response_time"):
                row += f"{val:>13.2f}s  "
            else:
                mark = "✅" if (threshold and val >= threshold) else "❌"
                row += f"{val:>13.3f} {mark:>2}"
        print(row)

    print(f"{'='*95}")
    print("📌 Ghi chú: Các baseline Standalone LLM, Naive RAG và Hybrid RAG không có module Query Router nên Routing Accuracy là N/A.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="So sánh 4 pipeline RAG trên 100 câu hỏi thử nghiệm")
    parser.add_argument("--output", type=str, default="comparative_results.json")
    parser.add_argument("--no-bert", action="store_true", help="Bỏ qua BERTScore (nhanh hơn)")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   COMPARATIVE EVALUATION — 4 Pipelines × 100 Questions      ║")
    print("║   Adaptive Agentic RAG vs Baselines                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    all_results = run_comparative_eval(use_bertscore=not args.no_bert)
    summary = compute_summary(all_results)
    print_comparison_table(summary)

    # Save
    output = {"summary": summary, "details": all_results}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n📁 Kết quả đã lưu: {args.output}")
