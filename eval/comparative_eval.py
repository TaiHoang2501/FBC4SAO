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
    def clean(t):
        if not t: return ""
        t = re.split(r"Nguồ[n|ns]:", t, flags=re.IGNORECASE)[0]
        t = re.sub(r"\[\d+\]", "", t)
        return t
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


def compute_citation(answer: str, sources: list) -> float:
    """Kiểm tra tuân thủ hình thức trích dẫn và sự hiện diện nguồn (Citation Format & Source Presence).
    1.0 nếu có ký hiệu trích dẫn [n] hợp lệ VÀ hệ thống có tài liệu nguồn tham chiếu.
    Trả về 0.0 nếu câu trả lời rỗng."""
    if not answer or not answer.strip():
        return 0.0
    return 1.0 if (re.search(r"\[\d+\]", answer) and sources) else 0.0


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


def compute_summary(all_results: dict) -> dict:
    """Tính trung bình các chỉ số cho từng pipeline."""
    summary = {}
    for pipe_name, results in all_results.items():
        n = len(results)
        # Chỉ pipeline có bộ định tuyến (Adaptive Agentic RAG) mới có routing_accuracy
        has_router = (pipe_name == "Adaptive Agentic RAG")
        routing_val = round(sum(r["routing_correct"] for r in results if r.get("routing_correct") is not None) / n, 4) if has_router else None
        
        times = [r.get("response_time", r.get("time", 0.0)) for r in results]
        times_sorted = sorted(times) if times else [0.0]
        avg_time = round(sum(times) / n, 2) if n else 0.0
        p50_time = round(times_sorted[n // 2], 2) if n else 0.0
        p95_time = round(times_sorted[int(n * 0.95)], 2) if n else 0.0

        # Phân rã phương pháp đo ngữ nghĩa thực tế
        methods_count = {}
        for r in results:
            m = r.get("semantic_metric_method", "unknown")
            methods_count[m] = methods_count.get(m, 0) + 1

        summary[pipe_name] = {
            "rouge_l":                  round(sum(r["rouge_l"] for r in results) / n, 4),
            "semantic_similarity":      round(sum(r.get("semantic_similarity", r.get("bertscore_f1", 0.0)) for r in results) / n, 4),
            "semantic_metric_breakdown": methods_count,
            "citation_compliance_rate": round(sum(r["citation"] for r in results) / n, 4),
            "routing_accuracy":         routing_val,
            "response_time_avg":        avg_time,
            "response_time_p50":        p50_time,
            "response_time_p95":        p95_time,
            # Backward compatibility aliases:
            "bertscore_f1":             round(sum(r.get("semantic_similarity", r.get("bertscore_f1", 0.0)) for r in results) / n, 4),
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
