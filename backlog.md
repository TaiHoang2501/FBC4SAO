# Product Backlog: FBC4SAO (Adaptive Agentic RAG)

> **Mục tiêu:** Hệ thống trợ lý AI tư vấn hoạt động ngoại khóa định hướng du học theo mật mã Holland (RIASEC).

---

## 1. Tính Năng Đã Hoàn Thành (Done)
- [x] **Router Intent Classification:** Phân loại câu hỏi người dùng thành 7 nhóm Agent với độ chính xác > 85%.
- [x] **Hybrid Search Retrieval:** Kết hợp BM25 Okapi và Dense Vector trên Qdrant, kết hợp RRF (Reciprocal Rank Fusion).
- [x] **Cross-Encoder Reranking:** Tái xếp hạng các đoạn văn bản truy xuất nhằm nâng cao độ liên quan ngữ cảnh.
- [x] **Dynamic Web Fallback:** Tự động mở rộng tìm kiếm qua Tavily Search khi tài liệu nội bộ không đủ thông tin.
- [x] **Semantic Cache Engine:** Giảm thiểu chi phí gọi LLM và độ trễ phản hồi cho các câu hỏi trùng lặp phổ biến.
- [x] **Evaluation Framework:** Bộ đo thực nghiệm 100 câu hỏi (Routing, BERTScore F1, Citation Accuracy, ROUGE-L).
- [x] **Desktop Client:** Giao diện Java Swing Desktop kết nối SSE streaming.

## 2. Kế Hoạch Nâng Cấp Tiếp Theo (Future Backlog)
- [ ] Mở rộng giao diện người dùng Web (Next.js / React) phục vụ đa nền tảng.
- [ ] Tích hợp tính năng phân tích trực tiếp CV định dạng PDF / DOCX bằng mô hình OCR + Vision LLM.
- [ ] Nâng cấp cơ chế Active Feedback từ học sinh và chuyên gia hướng nghiệp để tự động tinh chỉnh Prompt và Reranker.
