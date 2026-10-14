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
- Ollama (Khuyến nghị: `qwen2.5:7b-instruct-q4_K_M` — model chuẩn được sử dụng trong nghiên cứu & benchmark; hoặc `qwen3.5:0.8b` cho kiểm thử chức năng nhẹ)

### 2. Khởi tạo Cơ sở dữ liệu & Model
```bash
# Docker Qdrant (Nếu dùng server tách rời; mặc định hệ thống có sẵn local storage tại data/qdrant_storage)
docker run -p 6333:6333 qdrant/qdrant

# Kéo model chuẩn thực nghiệm:
ollama pull qwen2.5:7b-instruct-q4_K_M

# (Tùy chọn) Kéo model nhẹ phục vụ smoke test:
ollama pull qwen3.5:0.8b
```

### 3. Cài đặt Phụ thuộc
```bash
python -m venv .venv312
source .venv312/bin/activate  # macOS / Linux
pip install -r requirements.txt  # Hoặc dùng uv: uv sync
```

### 4. Chạy Hệ thống (4 Terminal)

> **Lưu ý:** Tất cả các lệnh thực thi từ thư mục gốc của repository, trừ lệnh frontend yêu cầu di chuyển vào thư mục `frontend/`.

1. **Backend API**:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8001
   # Hoặc dùng Makefile: make dev (mặc định PORT=8001)
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
4. **Ingest & Dữ liệu Tri thức (Knowledge Base)**:
   - Dữ liệu tri thức RIASEC, hồ sơ sinh viên 10 năm và tài liệu tham khảo đã được lập chỉ mục sẵn trong thư mục `data/` (`qdrant_storage`, `bm25_index.pkl`, `semantic_cache.db`).
   - Tệp [`scripts/ingest_riasec_data.py`](scripts/ingest_riasec_data.py) là script mẫu tham khảo quy trình hành văn hóa (textualization ETL) từ bảng dữ liệu gốc sang vector embedding. Để nạp thêm tài liệu PDF/DOCX mới, sử dụng API `/ingest/pdf` hoặc [`scripts/direct_ingest.py`](scripts/direct_ingest.py).

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

| Pipeline Kiến Trúc | ROUGE-L | Semantic Similarity (BERTScore vi) | Citation Compliance Rate\* | Routing Accuracy | Response Time (Avg / p95)\*\* | Phân Tích Đánh Đổi Kiến Trúc (Trade-offs) |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Pipeline 1: Standalone LLM** | **0.1324** | **0.6852** | 0.0% * | N/A *(Không có Router)* | 4.18s / 6.92s | Tự do ngôn ngữ cao nhất (ROUGE & BERTScore dẫn đầu), nhưng **0% Citation** do không có retriever đối soát |
| **Pipeline 2: Naive RAG** | 0.0226 | 0.6171 | 0.0% | N/A *(Không có Router)* | **0.41s** / **0.51s** | Tối ưu độ trễ nhất (nhanh gấp ~10 lần), nhưng dễ nhiễu ngữ cảnh; ROUGE và điểm ngữ nghĩa thấp nhất |
| **Pipeline 3: Hybrid RAG** | 0.1185 | 0.6768 | **100.0%** | N/A *(Không có Router)* | 9.46s / 12.94s | Dẫn đầu về tuân thủ trích dẫn nguồn (**100% Citation**), nhưng thiếu router chuyên môn theo kịch bản |
| **Pipeline 4: Adaptive Agentic RAG** (Đề xuất) | 0.1273 | 0.6723 | 76.0% | **80.0%** | 12.39s / 23.12s | Trang bị **80% Routing** đa tác tử và **76% Citation**, cải thiện ROUGE so với Naive RAG, nhưng độ trễ đơn luồng cao hơn |

> 📌 **Phân tích Đánh đổi Khách quan theo từng Chỉ số (Metric-by-Metric Trade-off Analysis):**
> Nghiên cứu thực nghiệm cho thấy **không có pipeline nào chiến thắng trên tất cả các chỉ số (No single winner across all metrics)**. Mỗi kiến trúc đại diện cho một phương án đánh đổi kỹ thuật cụ thể:
>
> 1. **Khả năng Định tuyến (Routing Accuracy):** Chỉ *Adaptive Agentic RAG* sở hữu mô-đun Query Router và đạt **80.0%** độ chính xác phân loại intent. Ba baseline còn lại không có thành phần định tuyến nên được ghi nhận chính xác là **N/A** (không thể đánh giá).
> 2. **Trùng khớp từ vựng (ROUGE-L):** *Standalone LLM* đạt điểm cao nhất (**0.1324**) do mô hình tự do sinh từ xuôi chiều theo mẫu tham chiếu. *Adaptive Agentic RAG* đạt **0.1273**, cao hơn so với *Hybrid RAG* (**0.1185**) và *Naive RAG* (**0.0226** — prompt tổng quát của Naive RAG dễ sinh câu trả lời ngắn hoặc lệch định dạng). Tiền tố nguồn tham chiếu và ký hiệu trích dẫn đã được bóc tách bằng biểu thức chính quy chuẩn hóa trước khi so khớp LCS.
> 3. **Tương đồng Ngữ nghĩa (Semantic Similarity — đo qua BERTScore vi):** *Standalone LLM* dẫn đầu (**0.6852**), bám sát phía sau là *Hybrid RAG* (**0.6768**) và *Adaptive Agentic RAG* (**0.6723**). *Naive RAG* thấp nhất (**0.6171**). Độ chênh lệch giữa Standalone LLM và hai kiến trúc RAG nâng cao là rất nhỏ (~0.01), cho thấy thông tin trích xuất vẫn bảo toàn ngữ nghĩa tốt trong khi bổ sung được dữ liệu nội bộ có kiểm chứng. *(Lưu ý phương pháp: Điểm số này đo bằng BERTScore F1 tiếng Việt, hoàn toàn tách biệt về mặt thang đo với LLM-as-a-Judge ở Phần A).*
> 4. **Tuân thủ Nguồn trích dẫn (Citation Compliance Rate):** *Hybrid RAG* đạt mức tối đa (**100.0%**) nhờ việc bắt buộc gắn nguồn trên toàn bộ ngữ cảnh tổng hợp. *Adaptive Agentic RAG* đạt **76.0%** (ở offline eval) và **87.0%** (ở live E2E), do một số agent (như giao tiếp chung S7 hoặc trả lời ngắn) ưu tiên giải thích trực tiếp. *Standalone LLM* đạt **0.0%** do giới hạn cấu trúc (không có retriever); *Naive RAG* đạt **0.0%** do prompt cơ bản không yêu cầu ký hiệu `[n]`.
> 5. **Thời gian phản hồi & Quy ước Phân vị Độ trễ (Response Time / Latency):\*\***
>    - **Quy ước tính toán:** Thời gian trung bình và phân vị 95 (p95) được tính toán theo phương pháp nội suy tuyến tính Type 7 chuẩn (NIST / SciPy default).
>    - **Điều kiện đo lường Phần B (Offline Controlled Benchmark):** Cả 4 pipeline được đo đạc trong điều kiện kiểm soát đơn luồng, xử lý tuần tự trực tiếp trên bộ nhớ không thông qua bộ đệm (cold execution), nhằm phản ánh chi phí tính toán thuật toán thuần túy. Dưới điều kiện này, Naive RAG nhanh nhất (**0.41s** trung bình, p95: 0.51s); trong khi Adaptive Agentic RAG mất **12.39s** (p95: 23.12s) do phải thực thi 2 chặng suy luận LLM (Query Router + Specialized Agent) kết hợp Cross-Encoder Reranker.
>    - **Phân tách với kết quả Hệ thống Live (Phần A):** Phép đo Live E2E (5.98s) thuộc một giao thức vận hành khác (máy chủ FastAPI, truyền tải HTTP/SSE, và có hỗ trợ Semantic Cache phục vụ các truy vấn tương đồng). Do hai môi trường có điều kiện chạy và kiến trúc phục vụ khác nhau, các kết quả này không thể gộp chung vào một phép so sánh trực tiếp, mà phản ánh hai góc nhìn: chi phí tính toán thuật toán ngoại tuyến vs năng lực phục vụ thực tế của hệ thống.
>
> **Kết luận:** Adaptive Agentic RAG được thiết kế nhằm giải quyết bài toán tư vấn học thuật chuyên sâu: bổ sung năng lực phân định nghiệp vụ đa tác tử và cung cấp căn cứ nguồn trích dẫn rõ ràng, chấp nhận chi phí tính toán cao hơn ở tầng đơn luồng nhưng bù đắp bằng tầng bộ đệm thông minh khi triển khai thực tế.

---

### 📂 Phân Định Kết Quả Thực Nghiệm & Tính Minh Bạch Nghiên Cứu

Để đảm bảo liêm chính học thuật (academic integrity) và minh bạch tối đa khi thẩm định nghiên cứu, toàn bộ kết quả được phân định theo 3 cấp độ kiểm chứng:

1. **Observed Results (Kết quả Lưu trữ Lịch sử):** Các số liệu đo lường trong [`eval/results_improved_final.json`](eval/results_improved_final.json) và [`eval/comparative_results.json`](eval/comparative_results.json) ghi nhận từ lần chạy thực nghiệm hoàn chỉnh trên máy chủ thử nghiệm cục bộ (Apple Silicon M-series, runtime Ollama `qwen2.5:7b-instruct-q4_K_M`, mô hình nhúng `multilingual-e5-large`, không bật cache ở phần so sánh).
2. **Verified Results (Kết quả Đối soát Tái lập Toán học):** Toàn bộ phép tổng hợp (Micro/Macro Average, thống kê Type 7 Percentiles, phép bóc tách regex nguồn) được kiểm tra tự động bởi [`eval/verify_reproducibility.py --ci`](eval/verify_reproducibility.py) trong mỗi commit với sai số kiểm tra tuyệt đối $\le 10^{-4}$ ($0.000000$ discrepancy).
3. **Reproduced Results (Tái lập Toàn bộ từ Đầu):** Đòi hỏi môi trường phần cứng có GPU/NPU và các dịch vụ nền (Ollama server với model 7B, Qdrant vector database). Khi có đủ môi trường, thực thi `python eval/comparative_eval.py` hoặc `python eval/thesis_eval.py --live`.

#### ⚠️ Các Giới Hạn Nghiên Cứu Quan Trọng (Academic Caveats & Limitations)
- **Cấu trúc Bộ Ground Truth:** Tập [`eval/ground_truth_final.json`](eval/ground_truth_final.json) hiện gồm 100 câu hỏi độc lập được chia thành 7 nhóm kịch bản (S1–S7). Ở phiên bản hiện tại, các câu hỏi trong cùng một kịch bản đang đối chiếu với cùng một văn bản tham chiếu chung đại diện cho nhóm (1 reference template/scenario). Nghiên cứu đang trong lộ trình audit và may đo bộ 100 câu trả lời tham chiếu chuyên biệt cho từng câu hỏi riêng biệt.
- **Bản chất Chỉ số Citation Compliance:** Metric này kiểm tra tính hợp lệ của cú pháp trích dẫn `[n]` và sự tồn tại của chỉ mục $1 \le idx \le \text{len}(sources)$ từ kết quả truy xuất. Metric này **chưa phải là kiểm chứng tính xác thực ở mức nhận định (claim-level NLI entailment)**.
- **Tách biệt Không gian Điểm Ngữ nghĩa:** Điểm $0.8558$ ở Hệ thống Live là **LLM-as-a-Judge** (thang điểm rubric chuẩn hóa $[0, 1]$), trong khi điểm $0.6723 - 0.6852$ ở Bảng so sánh là **BERTScore vi F1**. Hai thang đo thuộc hai không gian toán học khác nhau và không được so sánh trực tiếp như cùng một đại lượng.

---

### 📂 Ma trận Nguồn gốc Tệp Dữ liệu Thực nghiệm (Provenance Matrix)

| Tệp Dữ Liệu | Mục Đích Sử Dụng | Phương Pháp Đánh Giá | Trạng Thái Học Thuật |
|:---|:---|:---|:---|
| [`eval/results_improved_final.json`](eval/results_improved_final.json) | Đánh giá E2E hệ thống Live qua API | LLM-as-a-Judge Semantic Rubric, Citation Presence, ROUGE-L | **Chính thức (Canonical)** — 100 câu |
| [`eval/thesis_metrics.json`](eval/thesis_metrics.json) | Bảng phân rã 7 kịch bản S1–S7 | Tổng hợp Micro-Average (100 câu) & Macro-Average (7 nhóm) | **Chính thức (Canonical)** — Báo cáo Luận văn |
| [`eval/comparative_results.json`](eval/comparative_results.json) | So sánh 4 Pipeline đối chứng | BERTScore vi (dự phòng embedding cosine), Citation Presence, ROUGE-L, Latency (Avg/p50/p95) | **Chính thức (Canonical)** — Phân tích Kiến trúc |
| [`eval/archive/standard_metrics_legacy.json`](eval/archive/standard_metrics_legacy.json) | Kết quả sơ khai từ commit `261a8f1` | Đo độ phủ nhị phân và token overlap ban đầu | **Lưu trữ lịch sử (Deprecated Archive)** |

---

### 🧪 Tự Động Hóa Kiểm Thử & CI/CD (Continuous Integration)

Dự án thiết lập quy trình tích hợp liên tục tự động hóa trên GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)), phân tách rõ ràng giữa kiểm thử môi trường CI chuẩn và kiểm thử dịch vụ ngoài:
- **Kiểm thử Đơn vị & Tích hợp (CI Isolated Test Suite):** Chạy `pytest tests/ -v -m "not external"` bao gồm **36 bài kiểm thử** (hợp đồng Pydantic schemas, API integration, và toàn bộ các trường hợp biên của metrics: citation index out-of-bounds, negative index, empty inputs, regex stripping, Type 7 interpolation), độc lập 100% với các daemon bên ngoài như Ollama hoặc Docker Qdrant.
- **Xác minh Tính Tái lập Benchmark (Reproducibility Verification - CI Mode):** Chạy `python eval/verify_reproducibility.py --ci` xác minh tính toàn vẹn và schema dữ liệu canonical, không chứa giá trị NaN/Inf, tái lập Micro/Macro Average 7 kịch bản S1–S7 và bảng đối sánh 4 pipeline với dung sai toán học chặt $\le 10^{-4}$ trên tất cả chỉ số (bao gồm cả `response_time`).
- **Đóng gói Docker Production:** Kiểm tra cú pháp và build sạch Docker container production (`Dockerfile`) sau khi toàn bộ bước kiểm thử và xác minh toán học đều vượt qua.
- **Kiểm thử Thực thi Toàn diện (Adaptive Agentic RAG Smoke Eval):** Khi có môi trường local/runtime đầy đủ, lệnh `python eval/verify_reproducibility.py --smoke-eval` cho phép kiểm thử trực tiếp chu trình Adaptive Agentic RAG (Router → Search → Rerank → LLM → Live Metrics).


