# FBC4SAO: Adaptive Agentic RAG Chatbot for Study Abroad Orientation

> **FBC4SAO**: *A Framework of Building Chatbot to Advise on Extracurricular Activities for Study Abroad Orientation*

Hệ thống RAG đa tác nhân thích ứng (Adaptive Agentic RAG) được thiết kế để tư vấn hoạt động ngoại khóa và hướng nghiệp du học dựa trên lý thuyết mật mã Holland (RIASEC). Hệ thống kết hợp khả năng suy luận của LLM với hạ tầng sự kiện bất đồng bộ (Inngest) và tìm kiếm lai (Hybrid Search BM25 + Dense Vector).

## 🚀 Các Tính Năng Chính

- **Multi-Agent Architecture**: Tự động định tuyến câu hỏi đến 7 chuyên gia (agent) khác nhau dựa trên ý định của người dùng.
- **Hybrid Search**: Kết hợp tìm kiếm theo từ khóa (BM25) và tìm kiếm ngữ nghĩa (Vector Cosine similarity) trên Qdrant.
- **Dynamic Web Fallback**: Tự động cào dữ liệu từ Internet (Tavily) nếu tài liệu nội bộ không chứa câu trả lời.
- **Semantic Cache**: Phản hồi tức thì (<5ms) cho các câu hỏi trùng lặp phổ biến bằng SQLite.
- **Explainable AI (XAI)**: Cung cấp luồng suy nghĩ (Thinking) và báo cáo độ tin cậy kèm trích dẫn nguồn [n].

## 🛠️ Hướng Dẫn Cài Đặt & Chạy

### 1. Chuẩn bị Môi trường
- Python 3.12+
- Docker (để chạy Qdrant server - tùy chọn)
- Ollama (với model `qwen3.5:0.8b` hoặc tương đương)

### 2. Khởi tạo Cơ sở dữ liệu & Model
```bash
# Docker Qdrant (Nếu dùng server)
docker run -p 6333:6333 qdrant/qdrant

# Kéo model Ollama
ollama pull qwen3.5:0.8b
```

### 3. Cài đặt Phụ thuộc
```bash
python -m venv .venv312
source .venv312/bin/activate  # macOS
pip install -r requirements.txt  # Hoặc dùng uv: uv sync
```

### 4. Chạy Hệ thống (4 Terminal)

1. **Backend API**: `uvicorn main:app --port 8001`
2. **Inngest Worker**: `npx inngest-cli@latest dev -u http://127.0.0.1:8001/api/inngest`
3. **Frontend UI**: `javac HollandRAGGUI.java && java HollandRAGGUI`
4. **Ingest Dữ liệu**: `python scripts/ingest_riasec_data.py` (để nạp tài liệu tham khảo)

## 📊 Đánh Giá & Thực Nghiệm (Evaluation & Experimental Results)

Hệ thống được đánh giá qua tập **100 câu hỏi thử nghiệm chuẩn hóa** (`ground_truth_final.json`) phân bổ đều qua 7 kịch bản nghiệp vụ (S1 – S7) với các chỉ số cốt lõi:

1. **Routing Accuracy** (≥ 0.85): Tỉ lệ định tuyến chính xác đến agent chuyên môn.
2. **BERTScore F1** (≥ 0.75): Độ tương đồng ngữ nghĩa câu trả lời so với câu trả lời mẫu.
3. **Citation Accuracy** (≥ 0.80): Tỉ lệ trích dẫn nguồn `[n]` hợp lệ và có căn cứ.
4. **ROUGE-L** (≥ 0.10): Độ khớp chuỗi con dài nhất (LCS).
5. **Response Time** (≤ 10.0s): Thời gian phản hồi trung bình trên mỗi câu hỏi.

Chạy đánh giá live:
```bash
python thesis_eval.py --live --api http://localhost:8001 --file ground_truth_final.json
```

### Kết quả thử nghiệm tổng thể (100 câu hỏi)

| Chỉ số | Kết quả | Ngưỡng cam kết | Trạng thái |
|---|---|---|---|
| **Routing Accuracy** | **0.85** (85%) | ≥ 0.85 | ✅ PASS |
| **BERTScore F1** | **0.86** (85.7%) | ≥ 0.75 | ✅ PASS |
| **Citation Accuracy** | **0.86** (86%) | ≥ 0.80 | ✅ PASS |
| **ROUGE-L** | **0.11** | ≥ 0.10 | ✅ PASS |
| **Response Time** | **5.98s** | ≤ 10.0s | ✅ PASS |

### Kết quả chi tiết theo 7 kịch bản (Scenario Breakdown)

| Kịch bản | Tên kịch bản | Số câu | Routing Acc | BERTScore | Citation | Thời gian TB |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **S1** | Chẩn đoán Holland/RIASEC | 14 | 93% | 0.82 | 93% | 6.60s |
| **S2** | Tư vấn Ngoại khóa Nền tảng | 14 | 64% | 0.84 | 100% | 5.45s |
| **S3** | Tư vấn Ngoại khóa Chuyên sâu | 14 | 71% | 0.89 | 50% | 5.42s |
| **S4** | Hoạt động Cá nhân | 14 | 79% | 0.87 | 100% | 6.24s |
| **S5** | Đối chiếu Hồ sơ | 14 | 93% | 0.88 | 93% | 6.38s |
| **S6** | Đánh giá Toàn diện | 14 | 93% | 0.85 | 64% | 5.66s |
| **S7** | Hỏi đáp Tổng quát | 16 | 100% | 0.85 | 100% | 6.09s |
| **Toàn hệ thống** | **Tổng thể** | **100** | **85%** | **0.86** | **86%** | **5.98s** |

*Chi tiết kết quả xem tại: [`results_improved_final.json`](results_improved_final.json), [`thesis_metrics.json`](thesis_metrics.json) và [`comparative_results.json`](comparative_results.json).*

