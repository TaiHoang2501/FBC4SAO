# Architecture Specification: FBC4SAO

> **FBC4SAO: A Framework of Building Chatbot to Advise on Extracurricular Activities for Study Abroad Orientation**

---

## 1. Tổng Quan Kiến Trúc (Architecture Overview)

Hệ thống được thiết kế theo kiến trúc **Adaptive Agentic RAG** phân tầng (Layered Architecture):

```mermaid
graph TD
    Client[Frontend / Java Swing / REST Clients] --> API[FastAPI Backend /src/main.py]
    API --> Cache[Semantic Cache /src/semantic_cache.py]
    Cache -- Cache Hit (<5ms) --> Client
    Cache -- Cache Miss --> Router[Agent Router /src/agents.py]
    Router --> Agents[7 Specialized Agents]
    Agents --> Retrieval[Adaptive Hybrid Retrieval]
    Retrieval --> BM25[BM25 Index /data/bm25_index.pkl]
    Retrieval --> Qdrant[Dense Vector Qdrant /data/qdrant_storage]
    Retrieval --> WebFallback[Tavily Web Search]
    Retrieval --> Reranker[Cross-Encoder Reranker /src/reranker.py]
    Reranker --> PromptBuilder[Agent Prompt Builder]
    PromptBuilder --> LLM[LLM Service / Ollama / OpenAI]
    LLM --> SSE[SSE Streaming Token Response]
    SSE --> Client
```

---

## 2. Các Phân Hệ Chính (Core Subsystems)

### 2.1 Backend Core (`src/`)
* **`main.py`**: Điểm vào chính của FastAPI backend, cấu hình SSE endpoints `/query/stream`, quản lý session và lịch sử hội thoại.
* **`agents.py`**: Định nghĩa 7 Agent chuyên trách theo mã Holland RIASEC và hàm `route_question` phân loại ý định người dùng.
* **`vector_db.py`**: Quản lý kết nối Qdrant, nạp vector embedding, tìm kiếm Dense Vector và tìm kiếm BM25 qua RRF.
* **`reranker.py`**: Tái sắp xếp độ ưu tiên của các chunks truy xuất trước khi đưa vào context prompt của LLM.
* **`semantic_cache.py`**: Bộ đệm ngữ nghĩa SQLite lưu embedding các câu hỏi đã trả lời, tự động trả lời lại các câu tương tự mà không cần gọi LLM.
* **`llm_service.py`**: Giao tiếp trừu tượng hóa với các nhà cung cấp LLM (OpenAI API, Ollama local model).
* **`conversation_store.py`**: Quản lý lưu trữ trạng thái phiên làm việc và lịch sử trò chuyện bằng SQLite.

### 2.2 Đánh Giá & Kiểm Thử (`eval/`)
* **`thesis_eval.py`**: Khung đánh giá End-to-End hệ thống Live qua API streaming trên 100 câu hỏi chuẩn hóa ([`eval/ground_truth_final.json`](eval/ground_truth_final.json)), lưu kết quả chi tiết tại [`eval/results_improved_final.json`](eval/results_improved_final.json) và tóm tắt kịch bản tại [`eval/thesis_metrics.json`](eval/thesis_metrics.json).
* **`comparative_eval.py`**: Thực nghiệm so sánh đối chứng (Ablation Study) giữa 4 pipeline độc lập (Standalone LLM, Naive RAG, Hybrid RAG, Adaptive Agentic RAG), lưu tại [`eval/comparative_results.json`](eval/comparative_results.json).

### 2.3 Giao Diện & Client (`frontend/`)
* **`HollandRAGGUI.java`**: Giao diện máy tính viết bằng Java Swing, giao tiếp backend qua HTTP SSE streaming. Khởi chạy bằng `cd frontend && javac HollandRAGGUI.java && java HollandRAGGUI`.

---

## 3. Quy Chuẩn Khởi Chạy & Thực Thi (Deployment & Runtime)

| Thành phần | Lệnh thực thi từ thư mục gốc | Mô tả |
|:---|:---|:---|
| **FastAPI Backend** | `uvicorn src.main:app --port 8001` | Khởi động máy chủ backend tại cổng 8001 |
| **Inngest Engine** | `npx inngest-cli@latest dev -u http://127.0.0.1:8001/api/inngest` | Bộ điều phối sự kiện bất đồng bộ |
| **Java UI** | `cd frontend && javac HollandRAGGUI.java && java HollandRAGGUI` | Giao diện người dùng Java Swing |
| **Data Ingestion** | `python scripts/ingest_riasec_data.py` | Nạp dữ liệu lý thuyết RIASEC & hồ sơ |
| **Live Eval (E2E)** | `python eval/thesis_eval.py --live --api http://localhost:8001` | Đánh giá trực tiếp toàn hệ thống |
| **Comparative Eval** | `python eval/comparative_eval.py` | Đánh giá so sánh 4 mô hình độc lập |

---

## 4. Tài Liệu Tham Khảo Thêm
* Chi tiết thiết kế: [`docs/OVERVIEW.md`](docs/OVERVIEW.md)
* Kiến trúc chi tiết: [`docs/system_architecture.md`](docs/system_architecture.md)
* Sơ đồ luồng: [`DIagram/`](DIagram/)

