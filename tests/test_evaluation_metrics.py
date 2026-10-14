"""
tests/test_evaluation_metrics.py — Kiểm chứng độc lập các hàm tính toán chỉ số đánh giá (Evaluation Metrics Unit Tests)

Mục đích:
Xác thực chính xác tính đúng đắn toán học và hành vi biên của các hàm tính chỉ số trong eval/comparative_eval.py:
1. Citation Compliance & Source Index Validity (câu trả lời rỗng, trích dẫn ảo, trỏ nguồn không tồn tại, trích dẫn hợp lệ).
2. ROUGE-L (chuẩn hóa tiền tố nguồn, câu trả lời rỗng, trùng khớp hoàn toàn, không trùng khớp).
3. Semantic Similarity (BERTScore chuẩn, cơ chế dự phòng embedding cosine, ghi nhận phương pháp tính).
4. Routing Accuracy (định tuyến đúng, sai, khuyết tật, và đối xử công bằng giữa pipeline có/không có router).
5. Phân vị độ trễ (Percentiles Type 7 chuẩn).
6. Tổng hợp chỉ số (phân tách rõ ràng BERTScore F1 thuần và Cosine, không gộp mập mờ).
"""

import math
import pytest
from unittest.mock import patch

from eval.comparative_eval import (
    extract_citation_indices,
    compute_citation,
    compute_rouge_l,
    compute_semantic_similarity,
    evaluate_routing_accuracy,
    compute_latency_percentiles,
    compute_summary,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. KIỂM THỬ CITATION COMPLIANCE & SOURCE INDEX VALIDITY
# ─────────────────────────────────────────────────────────────────────────────

class TestCitationMetric:
    def test_citation_empty_answer(self):
        """Câu trả lời rỗng hoặc toàn khoảng trắng phải trả về 0.0."""
        assert compute_citation("", ["doc1.pdf"]) == 0.0
        assert compute_citation("   \n\t   ", ["doc1.pdf"]) == 0.0

    def test_citation_empty_sources(self):
        """Hệ thống không truy xuất được tài liệu nguồn nào (sources rỗng) phải trả về 0.0."""
        assert compute_citation("Nhóm R phù hợp kỹ thuật [1].", []) == 0.0
        assert compute_citation("Nhóm R phù hợp kỹ thuật [1].", None) == 0.0

    def test_citation_no_inline_brackets(self):
        """Câu trả lời có nguồn nhưng không chứa bất kỳ ký hiệu trích dẫn [n] nào phải trả về 0.0."""
        assert compute_citation("Bạn thuộc nhóm Realistic kỹ thuật.", ["holland.pdf"]) == 0.0

    def test_citation_out_of_bounds_index(self):
        """
        NGUY CƠ CHẤM SAI QUAN TRỌNG:
        Trích dẫn trỏ đến nguồn không tồn tại (chỉ số > len(sources)) phải trả về 0.0 (chống bịa đặt trích dẫn).
        """
        # Sources có 2 tài liệu (chỉ mục hợp lệ: 1, 2), nhưng câu trả lời trích dẫn [3] hoặc [99]
        sources = ["source_1.pdf", "source_2.pdf"]
        assert compute_citation("Theo tài liệu [3], bạn có năng khiếu kỹ thuật.", sources) == 0.0
        assert compute_citation("Thông tin từ nghiên cứu [99].", sources) == 0.0

    def test_citation_zero_or_negative_index(self):
        """Chỉ mục <= 0 là không hợp lệ theo quy ước trích dẫn [1..N]."""
        sources = ["source_1.pdf"]
        assert compute_citation("Theo tài liệu [0], bạn thích máy móc.", sources) == 0.0

    def test_citation_mixed_valid_and_invalid(self):
        """Nếu có một trích dẫn hợp lệ nhưng lẫn một trích dẫn ảo (out-of-bounds), toàn bộ câu trả lời phải coi là không hợp lệ (0.0)."""
        sources = ["source_1.pdf", "source_2.pdf"]
        # [1] hợp lệ, nhưng [3] trỏ đến nguồn không tồn tại
        assert compute_citation("Nhóm R [1] và ngành cơ khí [3].", sources) == 0.0

    def test_citation_valid_single(self):
        """Trích dẫn đơn hợp lệ [1] với 1 nguồn phải trả về 1.0."""
        sources = ["holland_data.pdf"]
        assert compute_citation("Bạn có xu hướng nhóm Realistic [1]. Nguồn: [1] holland_data.pdf", sources) == 1.0

    def test_citation_valid_multiple_formats(self):
        """Hỗ trợ nhiều trích dẫn hợp lệ dạng [1], [2], [1, 2] hoặc [1][2]."""
        sources = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
        ans1 = "Phân loại theo Holland [1, 2] và định hướng [3]."
        assert compute_citation(ans1, sources) == 1.0

        ans2 = "Kỹ năng chuyên môn [1][2] rất quan trọng [3]."
        assert compute_citation(ans2, sources) == 1.0

    def test_extract_citation_indices_utility(self):
        """Kiểm tra hàm bóc tách chỉ số trích dẫn."""
        assert extract_citation_indices("Không có trích dẫn") == []
        assert extract_citation_indices("Trích dẫn [1] và [2]") == [1, 2]
        assert extract_citation_indices("Trích dẫn nhóm [1, 2, 4]") == [1, 2, 4]
        assert extract_citation_indices("Trích dẫn liền [1][3]") == [1, 3]


# ─────────────────────────────────────────────────────────────────────────────
# 2. KIỂM THỬ ROUGE-L & CHUẨN HÓA TIỀN TỐ NGUỒN
# ─────────────────────────────────────────────────────────────────────────────

class TestRougeMetric:
    def test_rouge_empty_inputs(self):
        """Đầu vào rỗng phải trả về 0.0."""
        assert compute_rouge_l("", "Có nội dung") == 0.0
        assert compute_rouge_l("Có nội dung", "") == 0.0
        assert compute_rouge_l("", "") == 0.0

    def test_rouge_identical_texts(self):
        """Hai chuỗi giống hệt nhau phải đạt điểm tối đa 1.0."""
        text = "bạn có xu hướng thuộc nhóm realistic kỹ thuật"
        assert compute_rouge_l(text, text) == 1.0

    def test_rouge_source_stripping(self):
        """
        Khối nguồn ở cuối hoặc ký hiệu trích dẫn inline phải được bóc tách sạch sẽ
        để không làm giảm điểm nội dung chính.
        """
        ref = "Bạn có xu hướng thuộc nhóm Realistic kỹ thuật."
        
        # Biến thể 1: Có trích dẫn inline và khối 'Nguồn: [1] tailieu.pdf'
        hyp1 = "Bạn có xu hướng thuộc nhóm Realistic kỹ thuật [1].\n\nNguồn: [1] tailieu.pdf"
        assert compute_rouge_l(ref, hyp1) == 1.0

        # Biến thể 2: 'Nguồn tham khảo:'
        hyp2 = "Bạn có xu hướng thuộc nhóm Realistic kỹ thuật [1, 2].\nNguồn tham khảo: [1] a.pdf, [2] b.pdf"
        assert compute_rouge_l(ref, hyp2) == 1.0

        # Biến thể 3: '**Nguồn:**'
        hyp3 = "Bạn có xu hướng thuộc nhóm Realistic kỹ thuật.\n\n**Nguồn:** [1] cv.pdf"
        assert compute_rouge_l(ref, hyp3) == 1.0

        # Biến thể 4: 'Sources:'
        hyp4 = "Bạn có xu hướng thuộc nhóm Realistic kỹ thuật.\n\nSources: [1] web"
        assert compute_rouge_l(ref, hyp4) == 1.0

    def test_rouge_completely_different(self):
        """Hai câu hoàn toàn khác nhau về token phải có ROUGE-L = 0.0."""
        assert compute_rouge_l("học bổng du học mỹ canada", "sửa chữa ô tô xe máy") == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 3. KIỂM THỬ SEMANTIC SIMILARITY & DỰ PHÒNG EMBEDDING COSINE
# ─────────────────────────────────────────────────────────────────────────────

class TestSemanticSimilarityMetric:
    def test_semantic_empty_inputs(self):
        """Đầu vào rỗng phải trả về điểm 0.0 với phương thức 'empty_input'."""
        score, method = compute_semantic_similarity("", "Nội dung câu trả lời")
        assert score == 0.0
        assert method == "empty_input"

        score, method = compute_semantic_similarity("Nội dung tham chiếu", "")
        assert score == 0.0
        assert method == "empty_input"

    def test_semantic_bertscore_success(self):
        """Khi bert_score hoạt động bình thường, phương thức trả về phải là 'bert_score'."""
        # Giả lập bert_score trả về điểm F1 = 0.85
        with patch("bert_score.score") as mock_bscore:
            import torch
            mock_bscore.return_value = (None, None, torch.tensor([0.85]))
            score, method = compute_semantic_similarity("Xin chào bạn", "Chào bạn nhé")
            assert method == "bert_score"
            assert abs(score - 0.85) < 1e-4

    def test_semantic_fallback_to_embedding_cosine(self):
        """Khi bert_score gặp lỗi (ví dụ thiếu GPU hoặc lỗi thư viện), phải fallback sang 'embedding_cosine'."""
        with patch("bert_score.score", side_effect=ImportError("No bert_score")):
            # Giả lập embed_texts trả về 2 vector trực giao (cosine = 0.0)
            with patch("eval.comparative_eval.embed_texts") as mock_embed:
                mock_embed.side_effect = lambda texts, is_query=False: [[1.0, 0.0]] if "ref" in texts[0] else [[0.0, 1.0]]
                score, method = compute_semantic_similarity("ref text", "hyp text")
                assert method == "embedding_cosine"
                assert score == 0.0

    def test_semantic_failure_when_both_fail(self):
        """Khi cả BERTScore và Embedding model đều thất bại, phải trả về 0.0 với method 'failed'."""
        with patch("bert_score.score", side_effect=RuntimeError("BERT error")):
            with patch("eval.comparative_eval.embed_texts", side_effect=RuntimeError("Embed error")):
                score, method = compute_semantic_similarity("ref", "hyp")
                assert score == 0.0
                assert method == "failed"


# ─────────────────────────────────────────────────────────────────────────────
# 4. KIỂM THỬ ĐỘ CHÍNH XÁC ĐỊNH TUYẾN (ROUTING ACCURACY)
# ─────────────────────────────────────────────────────────────────────────────

class TestRoutingAccuracyMetric:
    def test_routing_without_router(self):
        """Các pipeline không có module Router (has_router=False) phải trả về None (N/A)."""
        assert evaluate_routing_accuracy("none", "test_riasec", has_router=False) is None
        assert evaluate_routing_accuracy("naive", "test_riasec", has_router=False) is None
        assert evaluate_routing_accuracy("hybrid", "test_riasec", has_router=False) is None

    def test_routing_with_router_correct(self):
        """Khi agent dự đoán khớp chính xác expected agent, điểm là 1.0."""
        assert evaluate_routing_accuracy("test_riasec", "test_riasec", has_router=True) == 1.0
        assert evaluate_routing_accuracy("danhgia_all", "danhgia_all", has_router=True) == 1.0

    def test_routing_with_router_incorrect(self):
        """Khi agent dự đoán sai, điểm là 0.0."""
        assert evaluate_routing_accuracy("hoidapchung", "test_riasec", has_router=True) == 0.0

    def test_routing_missing_predicted_agent(self):
        """Nếu predicted agent là None hoặc chuỗi rỗng, điểm phải là 0.0 (không đạt)."""
        assert evaluate_routing_accuracy(None, "test_riasec", has_router=True) == 0.0
        assert evaluate_routing_accuracy("", "test_riasec", has_router=True) == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 5. KIỂM THỬ PHÂN VỊ ĐỘ TRỄ (TYPE 7 PERCENTILES)
# ─────────────────────────────────────────────────────────────────────────────

class TestLatencyPercentiles:
    def test_empty_latency_list(self):
        """Danh sách độ trễ rỗng trả về (0.0, 0.0, 0.0)."""
        assert compute_latency_percentiles([]) == (0.0, 0.0, 0.0)

    def test_single_element(self):
        """Một phần tử thì avg, p50, p95 đều bằng chính giá trị đó."""
        assert compute_latency_percentiles([5.5]) == (5.5, 5.5, 5.5)

    def test_known_values_interpolation(self):
        """Kiểm tra đối chiếu chuẩn xác Type 7 interpolation với chuỗi 1..5."""
        # Dữ liệu: [1.0, 2.0, 3.0, 4.0, 5.0]
        # avg = 3.0, p50 = 3.0
        # p95 = idx (4 * 0.95 = 3.8) -> 4.0*0.2 + 5.0*0.8 = 4.8
        avg, p50, p95 = compute_latency_percentiles([1.0, 2.0, 3.0, 4.0, 5.0])
        assert avg == 3.0
        assert p50 == 3.0
        assert p95 == 4.8


# ─────────────────────────────────────────────────────────────────────────────
# 6. KIỂM THỬ TỔNG HỢP SUMMARY & PHÂN TÁCH PHƯƠNG PHÁP NGỮ NGHĨA
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeSummary:
    def test_summary_pure_bertscore_breakdown(self):
        """Khi 100% mẫu đều dùng bert_score, bertscore_f1_pure phải bằng semantic_similarity."""
        mock_results = {
            "Adaptive Agentic RAG": [
                {
                    "rouge_l": 0.20,
                    "semantic_similarity": 0.80,
                    "semantic_metric_method": "bert_score",
                    "citation": 1.0,
                    "routing_correct": 1.0,
                    "response_time": 10.0,
                },
                {
                    "rouge_l": 0.10,
                    "semantic_similarity": 0.70,
                    "semantic_metric_method": "bert_score",
                    "citation": 1.0,
                    "routing_correct": 1.0,
                    "response_time": 12.0,
                },
            ]
        }
        summary = compute_summary(mock_results)
        rag_summary = summary["Adaptive Agentic RAG"]
        assert rag_summary["semantic_metric_breakdown"] == {"bert_score": 2}
        assert rag_summary["bertscore_f1_pure"] == 0.75
        assert rag_summary["embedding_cosine_pure"] is None
        assert rag_summary["routing_supported"] is True
        assert rag_summary["routing_accuracy"] == 1.0

    def test_summary_mixed_methods_clear_separation(self):
        """
        NGUY CƠ CHẤM SAI QUAN TRỌNG:
        Khi có câu bị fallback sang embedding_cosine, summary phải báo cáo phân tách rõ ràng
        giữa bertscore_f1_pure và embedding_cosine_pure, không được coi chúng là tương đương.
        """
        mock_results = {
            "Hybrid RAG": [
                {
                    "rouge_l": 0.15,
                    "semantic_similarity": 0.80,
                    "semantic_metric_method": "bert_score",
                    "citation": 1.0,
                    "routing_correct": None,
                    "response_time": 8.0,
                },
                {
                    "rouge_l": 0.10,
                    "semantic_similarity": 0.60,
                    "semantic_metric_method": "embedding_cosine",
                    "citation": 1.0,
                    "routing_correct": None,
                    "response_time": 6.0,
                },
            ]
        }
        summary = compute_summary(mock_results)
        hybrid_summary = summary["Hybrid RAG"]
        assert hybrid_summary["semantic_metric_breakdown"] == {"bert_score": 1, "embedding_cosine": 1}
        # Điểm BERTScore thuần chỉ tính trên mẫu dùng bert_score (0.80)
        assert hybrid_summary["bertscore_f1_pure"] == 0.80
        # Điểm Embedding Cosine thuần chỉ tính trên mẫu dùng embedding_cosine (0.60)
        assert hybrid_summary["embedding_cosine_pure"] == 0.60
        # Pipeline không có router:
        assert hybrid_summary["routing_supported"] is False
        assert hybrid_summary["routing_accuracy"] is None
