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
2. **Phần B — Nghiên cứu So sánh 4 Pipeline (Comparative Pipeline Evaluation):** Đánh giá so sánh hiệu năng và sự đánh đổi (trade-offs) giữa 4 kiến trúc trong môi trường benchmark kiểm soát độc lập.

---

### Phần A: Đánh giá Toàn diện Hệ thống Live (Live API Evaluation)

Hệ thống được đánh giá qua tập **100 câu hỏi thử nghiệm chuẩn hóa** ([`eval/ground_truth_final.json`](eval/ground_truth_final.json)) phân bổ đều qua 7 kịch bản nghiệp vụ (S1 – S7) thông qua endpoint API streaming `/query/stream`.

#### Các chỉ số cốt lõi và phương pháp đo lường:
1. **Routing Accuracy** (Ngưỡng ≥ 0.85): Tỉ lệ định tuyến chính xác đến agent chuyên môn tương ứng.
2. **LLM-as-a-Judge Semantic Similarity** (Ngưỡng ≥ 0.75): Đo độ tương đồng ngữ nghĩa giữa câu trả lời sinh ra và câu trả lời mẫu tham chiếu (Ground Truth Reference).
   - **Phương pháp chấm:** Sử dụng mô hình ngôn ngữ lớn (LLM-as-a-Judge) đánh giá theo rubric ngữ nghĩa trên thang điểm chuẩn hóa từ `0.0` đến `1.0`.
   - **Rubric đánh giá:** Kiểm tra mức độ bảo toàn ý nghĩa cốt lõi, tính chính xác về thông tin phân loại mật mã Holland (RIASEC), và sự liên quan trực tiếp đến định hướng ngoại khóa.
   - **Độ tin cậy & Tính minh bạch:** Toàn bộ 100 câu hỏi trong bộ kết quả đều được ghi nhận phương pháp này qua trường `"semantic_metric_method": "llm_judge"`. Các trường hợp câu trả lời rỗng hoặc lỗi phân tích được gán điểm `0.0` nghiêm ngặt (loại bỏ hoàn toàn điểm fallback mặc định).
3. **Citation Compliance Rate\*** (Ngưỡng ≥ 0.80): Tỉ lệ tuân thủ quy chuẩn định dạng trích dẫn `[n]` và sự hiện diện của danh sách tài liệu nguồn tham khảo hợp lệ từ retriever (*citation-format / source-presence check*).
4. **ROUGE-L** (Ngưỡng chuẩn hóa ≥ 0.10): Đo độ khớp chuỗi con chung dài nhất (Longest Common Subsequence). Ngưỡng ≥ 0.10 là tiêu chuẩn phù hợp cho bài toán tư vấn học thuật tiếng Việt với câu trả lời phân tích mở dài, cho phép mô hình diễn giải tự nhiên mà vẫn bảo toàn từ vựng cốt lõi.
5. **Response Time** (Ngưỡng ≤ 10.0s): Thời gian phản hồi trung bình trên mỗi câu hỏi (bao gồm toàn bộ độ trễ mạng HTTP/SSE, sinh token và xử lý bộ đệm).

> ⚠️ **Ghi chú phương pháp về Citation Compliance (\*):** Chỉ số này đo lường sự tuân thủ hình thức trích dẫn `[n]` và sự hiện diện của metadata nguồn được truy xuất bởi hệ thống, đóng vai trò là tầng kiểm soát căn cứ ban đầu. Chỉ số này **chưa bao gồm** mô hình suy luận logic ngôn ngữ tự nhiên (NLI Claim-level Entailment) để kiểm chứng tính xác thực ngữ nghĩa từng khẳng định đơn lẻ.

Lệnh chạy đánh giá live:
```bash
python eval/thesis_eval.py --live --api http://localhost:8001 --file eval/ground_truth_final.json
```

#### Kết quả thử nghiệm tổng thể hệ thống Live (100 câu hỏi chuẩn hóa)

| Chỉ số | Micro-Average *(Kết quả chính - 100 câu)* | Macro-Average *(Trung bình 7 kịch bản)* | Ngưỡng cam kết | Trạng thái |
|---|:---:|:---:|:---:|:---:|
| **Routing Accuracy** | **0.85** (85.0%) | 0.85 (84.7%) | ≥ 0.85 | ✅ PASS |
| **LLM-as-a-Judge Semantic Similarity** | **0.86** (85.6%) | 0.86 (85.6%) | ≥ 0.75 | ✅ PASS |
| **Citation Compliance Rate\*** | **0.87** (87.0%) | 0.87 (86.7%) | ≥ 0.80 | ✅ PASS |
| **ROUGE-L** | **0.11** (11.3%) | 0.11 (11.3%) | ≥ 0.10 | ✅ PASS |
| **Response Time** | **5.98s** | 5.98s | ≤ 10.0s | ✅ PASS |

*Ghi chú về hai phương pháp tổng hợp:*
- **Micro-Average (Primary):** Tính trung bình có trọng số theo từng câu hỏi trên toàn bộ 100 mẫu benchmark — phản ánh chính xác kết quả tổng thể trong [`eval/results_improved_final.json`](eval/results_improved_final.json).
- **Macro-Average:** Tính trung bình không trọng số của 7 kịch bản — được đối chiếu song song trong [`eval/thesis_metrics.json`](eval/thesis_metrics.json).

#### Kết quả chi tiết theo 7 kịch bản nghiệp vụ (Scenario Breakdown)

| Kịch bản | Tên kịch bản | Số câu | Routing Acc | Semantic (LLM) | Citation Rate\* | Thời gian TB |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **S1** | Chẩn đoán Holland/RIASEC | 14 | 93% | 0.82 | 100% | 6.60s |
| **S2** | Tư vấn Ngoại khóa Nền tảng | 14 | 64% | 0.84 | 100% | 5.45s |
| **S3** | Tư vấn Ngoại khóa Chuyên sâu | 14 | 71% | 0.89 | 50% | 5.42s |
| **S4** | Hoạt động Cá nhân | 14 | 79% | 0.87 | 100% | 6.24s |
| **S5** | Đối chiếu Hồ sơ | 14 | 93% | 0.88 | 93% | 6.38s |
| **S6** | Đánh giá Toàn diện | 14 | 93% | 0.85 | 64% | 5.66s |
| **S7** | Hỏi đáp Tổng quát | 16 | 100% | 0.85 | 100% | 6.09s |
| **Toàn hệ thống (Micro)** | **Tổng thể 100 câu** | **100** | **85%** | **0.86** | **87%** | **5.98s** |
| **Toàn hệ thống (Macro)** | **Trung bình 7 nhóm** | **100** | **85%** | **0.86** | **87%** | **5.98s** |

*Nguồn dữ liệu chi tiết: [`eval/results_improved_final.json`](eval/results_improved_final.json) và [`eval/thesis_metrics.json`](eval/thesis_metrics.json).*

---

### Phần B: Nghiên cứu So sánh 4 Pipeline (Comparative Pipeline Evaluation)

Để phân tích khách quan hiệu quả và sự đánh đổi (trade-offs) của từng giải pháp kỹ thuật, nghiên cứu thực hiện kiểm thử so sánh độc lập giữa 4 kiến trúc trên cùng tập benchmark 100 câu hỏi (`eval/comparative_eval.py`):
1. **Pipeline 1 (Standalone LLM):** Mô hình ngôn ngữ lớn thuần túy, không có thành phần truy xuất dữ liệu.
2. **Pipeline 2 (Naive RAG):** Truy xuất Dense Vector đơn lẻ + Prompt tổng quát.
3. **Pipeline 3 (Hybrid RAG):** Kết hợp BM25 + Dense Vector + Prompt tổng quát.
4. **Pipeline 4 (Adaptive Agentic RAG):** Kiến trúc đề xuất với Dynamic Routing 7 Agents, Hybrid Retrieval, Cross-Encoder Reranker và Specialized Prompts.

Lệnh chạy kiểm thử so sánh:
```bash
python eval/comparative_eval.py
```

#### Bảng so sánh hiệu năng & độ trễ 4 kiến trúc (Comparative Pipeline Evaluation)

| Pipeline Kiến Trúc | ROUGE-L | Semantic Similarity | Citation Compliance Rate\* | Routing Accuracy | Response Time (Avg / p95) | Phân Tích Đánh Đổi Kiến Trúc (Trade-offs) |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Pipeline 1: Standalone LLM** | **0.1324** | **0.6852** | 0.0% | N/A *(Không có Router)* | **4.18s** / 7.07s | Phản hồi tự do theo tri thức pretrain, ROUGE cao nhưng không có retriever dẫn đến **0% Citation** |
| **Pipeline 2: Naive RAG** | 0.0226 | 0.6171 | 0.0% | N/A *(Không có Router)* | **0.41s** / 0.60s | Vector đơn lẻ cực nhanh nhưng dễ nhiễu ngữ cảnh; ROUGE và điểm tương đồng ngữ nghĩa thấp nhất |
| **Pipeline 3: Hybrid RAG** | 0.1185 | 0.6768 | **100.0%** | N/A *(Không có Router)* | 9.46s / 14.12s | BM25 + Vector ép trích dẫn nguồn 100%, nhưng thiếu chuyên biệt hóa theo kịch bản nghiệp vụ |
| **Pipeline 4: Adaptive Agentic RAG** (Đề xuất) | 0.1273 | 0.6723 | 76.0% | **80.0%** | 12.39s / 24.28s *(Live Cache: **5.98s**)* | Cân bằng tối ưu: đạt **80% Routing** đúng chuyên gia, **76% Citation** có căn cứ, vượt trội hoàn toàn so với Naive RAG |

> 📌 **Phân tích học thuật & Sự đánh đổi khách quan (Trade-offs Analysis):**
> 1. **Routing Accuracy:** Đối với các baseline (Standalone LLM, Naive RAG, Hybrid RAG), chỉ số này được ghi nhận chính xác là **N/A** vì các hệ thống này không trang bị mô-đun Query Router. Gán 0% sẽ gây hiểu lầm là hệ thống định tuyến sai, trong khi bản chất là chúng không thực hiện chức năng này.
> 2. **Đánh đổi giữa Citation và Sự tự do ngôn ngữ:** Standalone LLM đạt điểm ROUGE-L (0.1324) và Semantic Similarity (0.6852) cao hơn đôi chút do phản hồi mượt mà không bị ràng buộc bởi các trích đoạn văn bản thực tế. Tuy nhiên, theo định nghĩa giao thức, nó hoàn toàn không có khả năng dẫn chứng nguồn (`Citation Compliance = 0.0%`). Trong bài toán tư vấn học thuật và hướng nghiệp, câu trả lời bắt buộc phải có nguồn chứng thực minh bạch. Adaptive Agentic RAG chấp nhận độ phân tán từ ngữ để đổi lấy **76.0% Citation Compliance** và **80.0% Routing Accuracy**.
> 3. **Đánh đổi về Độ trễ (Latency Trade-off):** Trong môi trường benchmark không bộ đệm, Adaptive Agentic RAG có độ trễ trung bình cao hơn (12.39s) do phải thực thi qua 2 chặng suy luận (Query Router LLM + Hybrid Search + Reranker + Agent Specialized Prompt LLM). Tuy nhiên, khi vận hành thực tế tại môi trường Live với **Semantic Cache (<5ms)**, độ trễ trung bình toàn hệ thống giảm xuống chỉ còn **5.98s** (đáp ứng SLA ≤ 10.0s).
> 4. **So sánh với Naive RAG:** Adaptive Agentic RAG vượt trội rõ rệt so với Naive RAG truyền thống: ROUGE-L tăng gấp **5.6 lần** (0.1273 vs 0.0226) và Semantic Similarity tăng từ 0.6171 lên 0.6723.

---

### 📂 Ma trận Nguồn gốc Tệp Dữ liệu Thực nghiệm (Provenance Matrix)

| Tệp Dữ Liệu | Mục Đích Sử Dụng | Phương Pháp Đánh Giá | Trạng Thái Học Thuật |
|:---|:---|:---|:---|
| [`eval/results_improved_final.json`](eval/results_improved_final.json) | Đánh giá E2E hệ thống Live qua API | LLM-as-a-Judge Semantic Rubric, Citation Presence, ROUGE-L | **Chính thức (Canonical)** — 100 câu |
| [`eval/thesis_metrics.json`](eval/thesis_metrics.json) | Bảng phân rã 7 kịch bản S1–S7 | Tổng hợp Micro-Average (100 câu) & Macro-Average (7 nhóm) | **Chính thức (Canonical)** — Báo cáo Luận văn |
| [`eval/comparative_results.json`](eval/comparative_results.json) | So sánh 4 Pipeline đối chứng | Benchmark so sánh độc lập (có đo Latency Avg/p95) | **Chính thức (Canonical)** — Phân tích Kiến trúc |
| [`eval/archive/standard_metrics_legacy.json`](eval/archive/standard_metrics_legacy.json) | Kết quả sơ khai từ commit `261a8f1` | Đo độ phủ nhị phân và token overlap ban đầu | **Lưu trữ lịch sử (Deprecated Archive)** |

