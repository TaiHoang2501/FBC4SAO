"""
thesis_eval.py — Đánh giá 5 chỉ số theo Luận văn (Bản tối ưu hóa với bộ tham chiếu mở rộng)

Chỉ số:
  1. Routing Accuracy          : Tỉ lệ router chọn đúng agent (ngưỡng ≥ 0.85)
  2. ROUGE-L                   : Độ khớp chuỗi con dài nhất (ngưỡng chuẩn hóa ≥ 0.10)
  3. Semantic Similarity Score : Độ tương đồng ngữ nghĩa qua BERTScore / LLM Judge (ngưỡng ≥ 0.75)
  4. Citation Compliance Rate  : Tỉ lệ tuân thủ định dạng trích dẫn [n] & nguồn (ngưỡng ≥ 0.80)
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv()

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import call_llm from llm_service if available, else define a shim
try:
    from llm_service import call_llm
except ImportError:
    def call_llm(prompt: str, **kwargs) -> str:
        return "LLM Service not found. Please ensure llm_service.py exists."

THRESHOLD = {
    "routing_accuracy":         0.85,
    "rouge_l":                  0.10,  # Chuẩn hóa thống nhất với README & Luận văn (ngưỡng ≥ 0.10)
    "semantic_similarity":      0.75,
    "citation_compliance_rate": 0.80,
    # Backward compatibility aliases:
    "bertscore_f1":             0.75,
    "citation_accuracy":        0.80,
}


def _find_dataset() -> str:
    candidates = [
        Path(__file__).resolve().parent / "ground_truth_final.json",
        Path("ground_truth_final.json"),
        Path(__file__).resolve().parent / "ground_truth.json",
        Path("ground_truth.json")
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return str(candidates[0])

try:
    with open(_find_dataset(), "r", encoding='utf-8') as f:
        SAMPLE_DATASET = json.load(f)
except Exception:
    SAMPLE_DATASET = [] # Fallback

def compute_rouge_l(reference: str, hypothesis: str) -> float:
    def clean_for_rouge(text: str) -> str:
        if not text: return ""
        # 1. Loại bỏ phần Nguồn: ... ở cuối
        text = re.split(r"Nguồ[n|ns]:", text, flags=re.IGNORECASE)[0]
        # 2. Loại bỏ trích dẫn dạng [1], [2]...
        text = re.sub(r"\[\d+\]", "", text)
        return text

    def lcs(a, b):
        m, n = len(a), len(b)
        dp = [0] * (n + 1)
        for i in range(m):
            new_dp = [0] * (n + 1)
            for j in range(n):
                if a[i] == b[j]: new_dp[j+1] = dp[j] + 1
                else: new_dp[j+1] = max(dp[j+1], new_dp[j])
            dp = new_dp
        return dp[n]
    
    # Clean both before tokenizing
    reference = clean_for_rouge(reference)
    hypothesis = clean_for_rouge(hypothesis)
    
    ref_tokens = re.findall(r'\w+', reference.lower(), re.UNICODE)
    hyp_tokens = re.findall(r'\w+', hypothesis.lower(), re.UNICODE)
    if not ref_tokens or not hyp_tokens: return 0.0
    
    lcs_len = lcs(ref_tokens, hyp_tokens)
    r_lcs = lcs_len / len(ref_tokens)
    p_lcs = lcs_len / len(hyp_tokens)
    if r_lcs + p_lcs == 0: return 0.0
    return (2 * r_lcs * p_lcs) / (r_lcs + p_lcs)

def compute_semantic_similarity(reference: str, hypothesis: str) -> tuple[float, str]:
    """
    Tính độ tương đồng ngữ nghĩa và ghi nhận chính xác phương pháp tính được áp dụng:
    Returns:
        (score, method):
        - score: Điểm số từ 0.0 đến 1.0
        - method:
            * "bert_score": Tính qua thư viện bert_score chuẩn (ngôn ngữ vi).
            * "embedding_cosine": Cosine similarity từ vector embedding (multilingual-e5-large).
            * "llm_judge": Đánh giá bằng mô hình ngôn ngữ (LLM-as-a-Judge rubric).
            * "empty_input": Câu trả lời hoặc tham chiếu rỗng -> gán 0.0 nghiêm ngặt.
    """
    if not reference or not reference.strip() or not hypothesis or not hypothesis.strip():
        return 0.0, "empty_input"

    # 1. Thử dùng bert_score chuẩn
    try:
        from bert_score import score as bscore
        P, R, F1 = bscore([hypothesis], [reference], lang="vi", verbose=False)
        return float(F1[0]), "bert_score"
    except Exception:
        pass

    # 2. Thử dùng cosine similarity từ embedding model
    try:
        from data_loader import embed_texts
        import math
        ref_vec = embed_texts([reference], is_query=False)[0]
        hyp_vec = embed_texts([hypothesis], is_query=False)[0]
        dot = sum(a * b for a, b in zip(ref_vec, hyp_vec))
        nr = math.sqrt(sum(a * a for a in ref_vec))
        nh = math.sqrt(sum(b * b for b in hyp_vec))
        if nr * nh > 0:
            cos_sim = dot / (nr * nh)
            return max(0.0, min(1.0, float(cos_sim))), "embedding_cosine"
    except Exception:
        pass

    # 3. Dự phòng LLM-as-a-Judge
    return evaluate_llm_judge_similarity(reference, hypothesis), "llm_judge"


def compute_bertscore(reference: str, hypothesis: str) -> float:
    """Wrapper trả về điểm số ngữ nghĩa tương thích ngược."""
    score, _ = compute_semantic_similarity(reference, hypothesis)
    return score


def evaluate_llm_judge_similarity(reference: str, hypothesis: str) -> float:
    """
    LLM-as-a-Judge: Đánh giá độ tương đồng ngữ nghĩa giữa Ref và Hyp.
    Nếu hypothesis rỗng hoặc lỗi phân tích, trả về 0.0 (tuyệt đối không dùng fallback điểm cao).
    """
    if not reference or not reference.strip() or not hypothesis or not hypothesis.strip():
        return 0.0

    prompt = f"""Evaluate semantic similarity (0.0 to 1.0) between:
Ref: {reference}
Hyp: {hypothesis}
Output only the numeric score."""
    try:
        messages = [{"role": "user", "content": prompt}]
        response = call_llm(messages)
        score = re.findall(r"0\.\d+|1\.0", response)
        return float(score[0]) if score else 0.0
    except Exception:
        return 0.0


def evaluate_semantic_similarity(reference: str, hypothesis: str) -> float:
    """Wrapper tương thích ngược cho việc đánh giá độ tương đồng ngữ nghĩa."""
    return compute_bertscore(reference, hypothesis)


def evaluate_citation_format_presence(answer: str, sources: list) -> float:
    """
    Kiểm tra tính hợp lệ về hình thức trích dẫn và sự hiện diện của nguồn tài liệu:
    - Yêu cầu: Có ký hiệu trích dẫn dạng [n] trong văn bản VÀ danh sách tài liệu nguồn (sources) không rỗng.
    - Lưu ý học thuật: Đây là citation-format/source-presence check, đo lường sự tuân thủ quy chuẩn
      trích dẫn, chưa phải là phép kiểm chứng ngữ nghĩa từng khẳng định đơn lẻ (claim-level NLI entailment).
    """
    if not answer or not answer.strip():
        return 0.0
    return 1.0 if (re.search(r"\[\d+\]", answer) and sources) else 0.0

def run_evaluation(dataset=None, live=False, api_base="http://localhost:8000"):
    if dataset is None:
        dataset = SAMPLE_DATASET
    results = []
    print(f"Starting evaluation on {len(dataset)} samples...")
    client = httpx.Client(timeout=60.0)
    
    for i, item in enumerate(dataset):
        q = item["question"]
        print(f"[{i+1}/{len(SAMPLE_DATASET)}] Query: {q[:50]}...")
        
        start_time = time.time()
        answer, predicted_agent, sources = "", "", []
        
        if live:
            try:
                params = {"question": q, "session_id": "eval_user"}
                with client.stream("GET", f"{api_base}/query/stream", params=params) as response:
                    for line in response.iter_lines():
                        if isinstance(line, bytes):
                            line = line.decode('utf-8')
                        
                        line = line.strip()
                        if not line.startswith("data:"):
                            continue
                        
                        try:
                            # Load JSON from "data: {...}"
                            raw_data = line[5:].strip()
                            if not raw_data: continue
                            data = json.loads(raw_data)
                            dtype = data.get("type")
                            
                            if dtype == "token":
                                tok = data.get("token", "")
                                answer += tok
                            elif dtype == "cached":
                                answer = data.get("answer", "")
                                predicted_agent = data.get("agent", "")
                                sources = data.get("sources", [])
                            elif dtype == "done":
                                predicted_agent = data.get("agent", predicted_agent)
                                sources = data.get("sources", sources)
                        except Exception:
                            continue
            except Exception as e:
                print(f"Stream Error: {e}")
        
        elapsed = time.time() - start_time
        rouge = compute_rouge_l(item["reference"], answer)
        sem_score, sem_method = compute_semantic_similarity(item["reference"], answer)
        
        AGENT_DISPLAY_MAP = {
            "test_riasec": "Phân loại Holland",
            "hdnk_nentang": "Ngoại khóa Nền tảng",
            "hdnk_chuyenmon": "Ngoại khóa Chuyên môn",
            "hdnk_canhan": "Ngoại khóa Cá nhân",
            "match_hoso": "Case Study 10 năm",
            "danhgia_all": "Đánh giá Toàn diện",
            "hoidapchung": "Hướng nghiệp Tổng quát",
        }
        expected_display = AGENT_DISPLAY_MAP.get(item["expected_agent"], item["expected_agent"])
        routing_ok = 1.0 if predicted_agent == expected_display else 0.0

        # Kiểm tra quy chuẩn trích dẫn và sự hiện diện nguồn tham chiếu
        citation_ok = evaluate_citation_format_presence(answer, sources)

        results.append({
            "scenario": item.get("scenario", ""),
            "question": q,
            "expected_agent": item["expected_agent"],
            "predicted_agent": predicted_agent,
            "routing_correct": routing_ok,
            "rouge_l": rouge,
            "semantic_similarity": sem_score,
            "semantic_metric_method": sem_method,
            "citation_compliance": citation_ok,
            "response_time": elapsed,
            "answer": answer,
            # Backward compatibility aliases:
            "bertscore": sem_score,
            "citation_correct": citation_ok,
        })

    summary = {
        "routing_accuracy": sum(r["routing_correct"] for r in results) / len(results),
        "rouge_l": sum(r["rouge_l"] for r in results) / len(results),
        "semantic_similarity": sum(r["semantic_similarity"] for r in results) / len(results),
        "semantic_metric_methods": {
            m: sum(1 for r in results if r.get("semantic_metric_method") == m)
            for m in sorted(list(set(r.get("semantic_metric_method", "unknown") for r in results)))
        },
        "citation_compliance_rate": sum(r["citation_compliance"] for r in results) / len(results),
        "response_time": sum(r["response_time"] for r in results) / len(results),
        # Backward compatibility aliases:
        "bertscore_f1": sum(r["semantic_similarity"] for r in results) / len(results),
        "citation_accuracy": sum(r["citation_compliance"] for r in results) / len(results),
    }
    return results, summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--api", type=str, default="http://localhost:8000")
    parser.add_argument("--output", type=str, default="results_improved_final.json")
    parser.add_argument("--file", type=str, help="Path to input dataset JSON file")
    args = parser.parse_args()
    
    custom_dataset = None
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            custom_dataset = json.load(f)
            print(f"Loaded custom dataset from {args.file}")
    
    res, summ = run_evaluation(dataset=custom_dataset, live=args.live, api_base=args.api)
    print("\n--- Summary ---")
    print(json.dumps(summ, indent=2))
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"summary": summ, "details": res}, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {args.output}")
