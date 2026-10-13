# Weekly Journal — FBC4SAO Project

> Nhật ký tiến độ và quyết định kiến trúc dự án FBC4SAO (Adaptive Agentic RAG).

---

## Giai đoạn Nghiên cứu & Phát triển

### Mục tiêu chính
- [x] Xây dựng kiến trúc Multi-Agent Router phân loại 7 nhóm chuyên gia hướng nghiệp Holland.
- [x] Tích hợp Hybrid Search (BM25 + Dense Vector Qdrant) kết hợp Cross-Encoder Reranker.
- [x] Tối ưu hóa Semantic Caching giảm độ trễ phản hồi truy vấn thường gặp (<5ms).
- [x] Chuẩn hóa tập Benchmark 100 câu hỏi đánh giá theo 4 chỉ số Luận văn: Routing Accuracy, BERTScore F1, Citation Accuracy, ROUGE-L.
- [x] Tái cấu trúc dự án theo layout chuẩn doanh nghiệp (Enterprise Monorepo Structure).

### Quyết định Kỹ thuật
- Sử dụng Qdrant làm Vector Database chính, hỗ trợ fallback Local storage khi không có server Docker.
- Sử dụng BM25 Okapi cho lexical search, kết hợp thuật toán Reciprocal Rank Fusion (RRF) để xếp hạng hợp nhất.
- Tích hợp Inngest cho xử lý sự kiện bất đồng bộ và hỗ trợ streaming SSE trực tiếp lên Frontend.
