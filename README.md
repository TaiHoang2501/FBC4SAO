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

> **Lưu ý:** Tất cả các lệnh thực thi từ thư mục gốc của repository, trừ lệnh frontend yêu cầu di chuyển vào thư mục `frontend/`.

1. **Backend API**:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8001
   # Hoặc dùng Makefile: make dev (port 8000)
   ```
2. **Inngest Worker**:
   ```bash
   npx inngest-cli@latest dev -u http://127.0.0.1:8001/api/inngest
   ```
3. **Frontend UI (Java Swing)**:
   ```bash
   cd frontend && javac HollandRAGGUI.java && java HollandRAGGUI
   # Hoặc dùng Makefile từ thư mục gốc: make frontend
   ```
4. **Ingest Dữ liệu (Tri thức RIASEC & Hồ sơ)**:
   ```bash
   python scripts/ingest_riasec_data.py
   ```

## 📊 Đánh Giá & Thực Nghiệm (Evaluation & Experimental Results)

Nghiên cứu tiến hành hai thực nghiệm độc lập với mục tiêu và phương pháp luận rõ ràng:
1. **Phần A — Đánh giá Toàn diện Hệ thống Live (End-to-End Live System Evaluation):** Đánh giá dịch vụ thời gian thực qua REST/SSE API với đầy đủ các tầng chức năng.
2. **Phần B — Nghiên cứu So sánh Đối chứng 4 Pipeline (Comparative Ablation Study):** Đánh giá đóng góp thành phần (Ablation Study) trong môi trường benchmark cách ly.

---

### Phần A: Đánh giá Toàn diện Hệ thống Live (Live API Evaluation)

Hệ thống được đánh giá qua tập **100 câu hỏi thử nghiệm chuẩn hóa** ([`eval/ground_truth_final.json`](eval/ground_truth_final.json)) phân bổ đều qua 7 kịch bản nghiệp vụ (S1 – S7) thông qua endpoint API streaming `/query/stream`.

#### Các chỉ số cốt lõi và phương pháp đo:
1. **Routing Accuracy** (Ngưỡng ≥ 0.85): Tỉ lệ định tuyến chính xác đến agent chuyên môn tương ứng.
2. **Semantic Similarity (BERTScore F1 / LLM Judge)** (Ngưỡng ≥ 0.75): Đo độ tương đồng ngữ nghĩa giữa câu trả lời sinh ra và câu trả lời mẫu tham chiếu. Script ưu tiên thư viện `bert_score` chuẩn (tiếng Việt), có fallback embedding cosine similarity và LLM-as-a-Judge. *Các câu trả lời rỗng hoặc lỗi kết nối được gán điểm 0.0 nghiêm ngặt.*
3. **Citation Compliance Rate\*** (Ngưỡng ≥ 0.80): Tỉ lệ tuân thủ quy chuẩn định dạng trích dẫn `[n]` và sự hiện diện của danh sách nguồn tham khảo từ retriever (*citation-format / source-presence check*).
4. **ROUGE-L** (Ngưỡng ≥ 0.10): Đo độ khớp chuỗi con dài nhất (Longest Common Subsequence) sau khi lọc nhãn trích dẫn.
5. **Response Time** (Ngưỡng ≤ 10.0s): Thời gian phản hồi trung bình trên mỗi câu hỏi (bao gồm toàn bộ độ trễ mạng và sinh token).

> ⚠️ **Ghi chú phương pháp về Citation Compliance (\*):** Chỉ số này đo lường sự tuân thủ hình thức trích dẫn `[n]` và sự hiện diện của metadata nguồn được truy xuất bởi hệ thống, đóng vai trò là tầng kiểm soát căn cứ ban đầu. Chỉ số này **chưa bao gồm** mô hình suy luận logic ngôn ngữ tự nhiên (NLI Claim-level Entailment) để kiểm chứng tính xác thực ngữ nghĩa từng khẳng định đơn lẻ.

Lệnh chạy đánh giá live:
```bash
python eval/thesis_eval.py --live --api http://localhost:8001 --file eval/ground_truth_final.json
```

#### Kết quả thử nghiệm tổng thể hệ thống Live (100 câu hỏi)

| Chỉ số | Kết quả | Ngưỡng cam kết | Trạng thái |
|---|---|---|---|
| **Routing Accuracy** | **0.85** (85.0%) | ≥ 0.85 | ✅ PASS |
| **Semantic Similarity (BERTScore F1)** | **0.86** (85.6%) | ≥ 0.75 | ✅ PASS |
| **Citation Compliance Rate\*** | **0.87** (87.0%) | ≥ 0.80 | ✅ PASS |
| **ROUGE-L** | **0.11** (11.3%) | ≥ 0.10 | ✅ PASS |
| **Response Time** | **5.98s** | ≤ 10.0s | ✅ PASS |

#### Kết quả chi tiết theo 7 kịch bản (Scenario Breakdown)

| Kịch bản | Tên kịch bản | Số câu | Routing Acc | BERTScore F1 | Citation Rate\* | Thời gian TB |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **S1** | Chẩn đoán Holland/RIASEC | 14 | 93% | 0.82 | 100% | 6.60s |
| **S2** | Tư vấn Ngoại khóa Nền tảng | 14 | 64% | 0.84 | 100% | 5.45s |
| **S3** | Tư vấn Ngoại khóa Chuyên sâu | 14 | 71% | 0.89 | 50% | 5.42s |
| **S4** | Hoạt động Cá nhân | 14 | 79% | 0.87 | 100% | 6.24s |
| **S5** | Đối chiếu Hồ sơ | 14 | 93% | 0.88 | 93% | 6.38s |
| **S6** | Đánh giá Toàn diện | 14 | 93% | 0.85 | 64% | 5.66s |
| **S7** | Hỏi đáp Tổng quát | 16 | 100% | 0.85 | 100% | 6.09s |
| **Toàn hệ thống** | **Tổng thể** | **100** | **85%** | **0.86** | **87%** | **5.98s** |

*Nguồn dữ liệu chi tiết: [`eval/results_improved_final.json`](eval/results_improved_final.json) và [`eval/thesis_metrics.json`](eval/thesis_metrics.json).*

---

### Phần B: Nghiên cứu So sánh Đối chứng 4 Pipeline (Comparative Ablation Study)

Để chứng minh tính ưu việt của kiến trúc đề xuất **Adaptive Agentic RAG**, nghiên cứu thực hiện kiểm thử thực nghiệm đối chứng trên 4 kiến trúc với cùng bộ dữ liệu 100 câu hỏi trong môi trường benchmark kiểm soát độc lập (`eval/comparative_eval.py`):
1. **Pipeline 1 (Standalone LLM):** Mô hình ngôn ngữ lớn thuần túy, không có thành phần truy xuất dữ liệu.
2. **Pipeline 2 (Naive RAG):** Truy xuất Dense Vector đơn lẻ + Prompt tổng quát.
3. **Pipeline 3 (Hybrid RAG):** Kết hợp BM25 + Dense Vector + Prompt tổng quát.
4. **Pipeline 4 (Adaptive Agentic RAG):** Kiến trúc đề xuất với Dynamic Routing, Hybrid Retrieval, Cross-Encoder Reranker và Specialized Agent Prompts.

Lệnh chạy kiểm thử so sánh 4 pipeline:
```bash
python eval/comparative_eval.py
```

#### Bảng so sánh hiệu năng 4 kiến trúc (Comparative Evaluation Results)

| Pipeline Kiến Trúc | ROUGE-L | BERTScore F1 | Citation Compliance\* | Routing Accuracy | Ghi Chú Kiến Trúc |
|:---|:---:|:---:|:---:|:---:|:---|
| **Pipeline 1: Standalone LLM** | 0.1324 | 0.6852 | 0.0% | 0.0% | Không có cơ chế RAG, hiện tượng ảo giác cao |
| **Pipeline 2: Naive RAG** | 0.0226 | 0.6171 | 0.0% | 0.0% | Tìm kiếm vector đơn lẻ, dễ nhiễu ngữ cảnh |
| **Pipeline 3: Hybrid RAG** | 0.1185 | 0.6768 | 100.0% | 0.0% | BM25 + Vector cải thiện trích xuất từ khóa |
| **Pipeline 4: Adaptive Agentic RAG** (Đề xuất) | **0.1273** | **0.6723** | **76.0%** | **80.0%** | Định tuyến tác nhân thích ứng + Reranker |

> 📌 **Lưu ý về phương pháp luận giữa hai bộ kết quả:**
> - Hai bộ kết quả [`results_improved_final.json`](eval/results_improved_final.json) và [`comparative_results.json`](eval/comparative_results.json) đại diện cho **hai phép đo khác nhau**: một bên là kiểm thử dịch vụ sản phẩm trực tiếp (Live End-to-End System qua HTTP/SSE Streaming API có kết hợp Semantic Cache và Identity Firewall), một bên là thực nghiệm mô hình hóa đối chứng nội bộ (Modular Ablation Harness).
> - Do đó, các con số tuyệt đối không được so sánh chéo trực tiếp như thể chúng sinh ra từ cùng một lần chạy, mà dùng để chứng minh hai luận điểm bổ trợ: (1) Kiến trúc đề xuất vượt trội hơn các baseline truyền thống; và (2) Hệ thống hoàn chỉnh triển khai thực tế đạt chuẩn SLAs cam kết.

