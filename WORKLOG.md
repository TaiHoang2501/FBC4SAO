# Worklog — FBC4SAO Project

> Nhật ký ghi nhận các hạng mục công việc đã thực hiện trong hệ thống FBC4SAO.

---

## Lịch sử công việc

| Thời gian | Hạng mục công việc | Trạng thái | Đầu ra |
|---|---|---|---|
| Phase 1 | Khởi tạo mô hình Hybrid Search (BM25 + Dense Vector) | ✅ Done | `src/vector_db.py`, `src/reranker.py` |
| Phase 2 | Thiết kế 7 chuyên gia Multi-Agent & Router phân loại ý định | ✅ Done | `src/agents.py`, `src/llm_service.py` |
| Phase 3 | Xây dựng bộ đệm ngữ nghĩa Semantic Cache & SQLite Store | ✅ Done | `src/semantic_cache.py`, `src/conversation_store.py` |
| Phase 4 | Phát triển Giao diện Desktop Java Swing & SSE API Bridge | ✅ Done | `frontend/HollandRAGGUI.java`, `src/java_bridge.py` |
| Phase 5 | Thiết kế bộ thực nghiệm 100 câu hỏi & bộ đo chỉ số luận văn | ✅ Done | `eval/ground_truth_final.json`, `eval/thesis_eval.py` |
| Phase 6 | Thực nghiệm đối chuẩn 4 Pipelines RAG | ✅ Done | `eval/comparative_eval.py`, `eval/comparative_results.json` |
| Phase 7 | Tái cấu trúc chuẩn hóa toàn bộ dự án theo cấu trúc Enterprise | ✅ Done | Layout `src/`, `eval/`, `frontend/`, `data/`, `docs/`, `presentation/` |
