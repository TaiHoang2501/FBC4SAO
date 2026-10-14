# 📋 Hướng Dẫn Tái Lập Thực Nghiệm & Đánh Giá Độc Lập (Evaluation & Replication Guide)

Tài liệu này cung cấp hướng dẫn đầy đủ, minh bạch và có thể kiểm chứng độc lập cho toàn bộ các thực nghiệm đánh giá trong dự án FBC4SAO, phục vụ công tác thẩm định học thuật và đối chiếu khoa học.

---

## 1. Cấu Trúc Dữ Liệu & Ma Trận Nguồn Gốc (Data Provenance Matrix)

| Tệp Dữ Liệu | Vai Trò & Trạng Thái | Phương Pháp Đo Ngữ Nghĩa | Quy Ước Thời Gian | Giao Thức Đánh Giá |
|:---|:---|:---|:---|:---|
| [`ground_truth_final.json`](ground_truth_final.json) | **Tập kiểm thử chuẩn hóa** (100 câu, 7 kịch bản S1–S7) | N/A (Bộ câu hỏi & tham chiếu chuẩn) | N/A | Dataset đối sánh chuẩn mực |
| [`results_improved_final.json`](results_improved_final.json) | **Kết quả Live API E2E** (100 câu) | **LLM-as-a-Judge** (thang 0.0 - 1.0, model `qwen2.5:7b-instruct-q4_K_M`) | E2E HTTP/SSE streaming, có Semantic Cache (<5ms) | Thực nghiệm Phần A (Hệ thống thời gian thực) |
| [`thesis_metrics.json`](thesis_metrics.json) | **Báo cáo tổng hợp Luận văn** (Micro & Macro) | Sinh tự động từ `results_improved_final.json` | Micro-average: **5.98s** | Báo cáo chính thức theo từng kịch bản |
| [`comparative_results.json`](comparative_results.json) | **So sánh 4 Pipeline đối chứng** (400 lượt chạy) | **BERTScore vi F1** (thư viện `bert_score`, dự phòng `embedding_cosine`) | Cold-run đơn luồng không cache (Avg, p50, p95 qua Type 7) | Thực nghiệm Phần B (Kiến trúc đối chứng) |
| [`archive/standard_metrics_legacy.json`](archive/standard_metrics_legacy.json) | **Dữ liệu lưu trữ lịch sử** (commit `261a8f1`) | Token overlap sơ khai | Đo lường cũ | Đã lưu trữ (Deprecated Archive) |

> ⚠️ **Nguyên tắc phương pháp luận quan trọng:**
> - **Không gộp hai thang đo Semantic Similarity:** Điểm số ngữ nghĩa ở Phần A (**0.8558 ~ 0.86**) được chấm bằng **LLM-as-a-Judge rubric**, trong khi Phần B (**0.6723**) được đo bằng **BERTScore vi F1**. Hai thước đo này khác nhau về bản chất toán học và không gian giá trị, do đó được báo cáo độc lập tại hai bảng riêng biệt.
> - **Không đối chiếu trực tiếp độ trễ khác điều kiện:** Thời gian phản hồi trong bài thử nghiệm 4 Pipeline (**12.39s**, p95: 23.12s) được đo trong môi trường ngoại tuyến đơn luồng, không sử dụng bộ đệm (cold queries) để đo chi phí thuật toán thuần túy. Trong khi đó, hệ thống Live API (**5.98s**) hoạt động qua máy chủ FastAPI có hỗ trợ Semantic Cache. Hai số liệu này phản ánh hai góc nhìn kỹ thuật khác nhau, không phải cùng một điều kiện thử nghiệm.

---

## 2. Quy Ước Tính Toán Chỉ Số (Metric Computation Conventions)

1. **Routing Accuracy (Độ chính xác định tuyến):**
   - Đánh giá khả năng phân loại đúng tác tử chuyên môn theo kịch bản ($1.0$ nếu `predicted_agent == expected_agent`, ngược lại $0.0$).
   - **Tiêu chuẩn giữa các pipeline:** Chỉ *Adaptive Agentic RAG* sở hữu module Query Router nên được chấm điểm số thực tế. Ba baseline (Standalone LLM, Naive RAG, Hybrid RAG) là kiến trúc đơn pipeline, không trang bị Router, do đó được ghi nhận chính xác là **N/A** (kèm cờ `routing_supported: False`).
2. **ROUGE-L & Chuẩn hóa tiền tố nguồn:**
   - Sử dụng thuật toán Longest Common Subsequence (LCS) trên tập token từ vựng tiếng Việt.
   - Trước khi so khớp, tiền tố nguồn (`Nguồn:`, `Nguồn tham khảo:`, `Sources:`, `**Nguồn:**`, v.v.) và các ký hiệu trích dẫn (`[n]`, `[1, 2]`) được bóc tách triệt để bằng biểu thức chính quy chuẩn hóa (`clean_for_rouge`) để đảm bảo không làm sai lệch điểm số nội dung chính.
3. **Citation Compliance & Source Index Validity (Tuân thủ trích dẫn & Hợp lệ nguồn tồn tại):**
   - Đánh giá tính hợp lệ về hình thức trích dẫn và tính toàn vẹn của chỉ mục tài liệu tham chiếu:
     * Câu trả lời không rỗng và hệ thống có tài liệu nguồn được truy xuất (`sources` không rỗng).
     * Phải có ít nhất một ký hiệu trích dẫn `[n]` trong văn bản.
     * **Kiểm tra nguồn tồn tại (Source Existence Check):** TẤT CẢ các chỉ số trích dẫn trong văn bản phải nằm trong phạm vi chỉ mục tài liệu thực tế: $1 \le n \le \text{len}(sources)$.
     * **Xử lý trích dẫn ảo:** Nếu câu trả lời trích dẫn chỉ mục không tồn tại (ví dụ: trích dẫn `[5]` trong khi chỉ có 2 tài liệu trong context, hoặc chỉ số $\le 0$), điểm số lập tức bị đánh tụt về **0.0**.
   - *Lưu ý học thuật:* Chỉ số này đo lường tính tuân thủ hình thức và tính toàn vẹn chỉ mục nguồn, chưa phải là claim-level NLI entailment.
4. **Semantic Similarity & Phân tách phương pháp (Pure Metrics Separation):**
   - Sử dụng thư viện `bert_score` chuẩn cho tiếng Việt (`lang="vi"`).
   - **Nguyên tắc phân tách minh bạch:** Trong trường hợp có dự phòng (fallback) sang `embedding_cosine`, hệ thống lưu rõ `semantic_metric_method` cho từng câu và báo cáo độc lập:
     * `bertscore_f1_pure`: Điểm trung bình CHỈ trên các mẫu đo bằng BERTScore thuần.
     * `embedding_cosine_pure`: Điểm trung bình CHỈ trên các mẫu đo bằng Cosine Embedding.
     * Không gộp mập mờ hai không gian điểm khác nhau vào cùng một cột mà không có bảng phân rã `semantic_metric_breakdown`.
5. **Quy ước Phân vị Độ trễ (Percentiles):**
   - Độ trễ trung vị (p50) và phân vị 95 (p95) được tính toán theo chuẩn **Type 7 Linear Interpolation** (mặc định của NumPy và NIST/SciPy).

---

## 3. Hướng Dẫn Tái Lập Độc Lập Từng Bước (Step-by-Step Replication)

### Bước 1: Chuẩn bị môi trường sạch
```bash
# Tạo và kích hoạt môi trường ảo Python 3.12
python3.12 -m venv .venv
source .venv/bin/activate

# Cài đặt toàn bộ dependencies
pip install -r requirements.txt
pip install bert-score torch
```

### Bước 2: Tải mô hình và cấu hình Ollama
```bash
# Khởi động Ollama local runtime
ollama serve

# Tải mô hình ngôn ngữ chỉ định
ollama pull qwen2.5:7b-instruct-q4_K_M
```

### Bước 3: Chạy kịch bản kiểm tra tính tái lập tự động
Dự án cung cấp bộ công cụ tự động kiểm tra tính toàn vẹn dữ liệu, tính tái lập toán học với dung sai chặt (≤ 1e-4) cho tất cả các chỉ số (bao gồm cả độ trễ `response_time_avg`, `p50`, `p95` ở cả 4 pipeline và 7 kịch bản S1–S7), regex bóc tách nguồn, và kiểm tra độc lập từng môi trường:
```bash
# 1. Chạy xác minh trong CI (không tải mô hình nặng HuggingFace, không phụ thuộc dịch vụ ngoài):
python eval/verify_reproducibility.py --ci

# 2. Kiểm tra toán học, dữ liệu và môi trường đầy đủ (6 bài kiểm tra độc lập):
python eval/verify_reproducibility.py

# 3. Chạy kèm kiểm thử thực thi End-to-End trực tiếp trên Adaptive Agentic RAG:
python eval/verify_reproducibility.py --smoke-eval
```
*Kết quả kỳ vọng:*
- *Chế độ `--ci`: 4/4 bài kiểm tra đạt `✅ PASS` trong ~5 giây (hoàn hảo cho GitHub Actions runner).*
- *Chế độ mặc định: 6/6 bài kiểm tra đạt `✅ PASS`.*
- *Chế độ `--smoke-eval`: Kiểm tra toàn diện chu trình Adaptive Agentic RAG (Router → Search → Rerank → LLM → Live Metrics), đạt `✅ PASS`.*

### Bước 4: Tái lập Bảng tổng hợp Luận văn (thesis_metrics.json)
```bash
python eval/compute_standard_metrics.py
```
*Kịch bản sẽ tự động đọc `results_improved_final.json` và tái lập chính xác bảng Micro-Average (Routing: 0.85, ROUGE-L: 0.11, Semantic: 0.86, Citation: 0.87, Latency: 5.98s) và Macro-Average.*

### Bước 5: Chạy lại Thử nghiệm So sánh 4 Pipeline (Comparative Pipeline Evaluation)
```bash
python eval/comparative_eval.py --output comparative_results_reproduced.json
```
*Kịch bản sẽ chạy lần lượt 100 câu qua 4 pipeline (Standalone LLM, Naive RAG, Hybrid RAG, Adaptive Agentic RAG), đo ROUGE-L, BERTScore vi F1, Citation Compliance và Latency (Avg, p50, p95), sau đó in bảng đối sánh chuẩn.*

### Bước 6: Chạy lại Thử nghiệm Hệ thống Live E2E (Tùy chọn)
Khởi động máy chủ backend tại terminal 1:
```bash
python -m src.main
```
Tại terminal 2, kích hoạt kịch bản kiểm thử API trực tiếp:
```bash
python eval/thesis_eval.py --live --api http://localhost:8000 --file eval/ground_truth_final.json --output results_live_reproduced.json
```

---

## 4. Kiểm Thử Đơn Vị & Kiểm Chứng Metric Độc Lập (Unit & Metric Tests)

Hệ thống cung cấp bộ kiểm thử độc lập toàn diện bao quát tất cả các trường hợp biên của từng chỉ số (`tests/test_evaluation_metrics.py`):
```bash
# 1. Chạy toàn bộ kiểm thử đơn vị, API và các trường hợp biên của metric (36 tests):
pytest tests/ -v -m "not external"

# 2. Chạy riêng bộ kiểm chứng toán học và hành vi metric (26 tests):
pytest tests/test_evaluation_metrics.py -v

# 3. Chạy toàn bộ test suite bao gồm cả test snapshot router trực tiếp:
pytest tests/ -v
```
*Kết quả kỳ vọng trong CI: **36/36 tests PASS** (bao gồm 6 contract tests, 4 API integration tests, 26 metric unit tests bao quát trích dẫn ảo, nguồn rỗng, bóc tách nguồn ROUGE, fallback semantic similarity, percentiles Type 7).*

---

## 5. Phạm Vi & Giới Hạn Kiểm Chứng Của CI (CI Verification Scope & Limitations)

Để duy trì tính trung thực và minh bạch học thuật:
- **Những gì CI đã kiểm chứng tự động (GitHub Actions):**
  1. Toàn bộ logic toán học của các hàm tính metric, bao gồm bóc tách nguồn, xử lý trích dẫn ảo, trỏ nguồn ngoài phạm vi, và phân rã fallback (`tests/test_evaluation_metrics.py`).
  2. Tính toàn vẹn cấu trúc và định dạng JSON của 4 tệp dữ liệu canonical (`ground_truth_final.json`, `results_improved_final.json`, `thesis_metrics.json`, `comparative_results.json`).
  3. Tính tái lập toán học độc lập giữa dữ liệu chi tiết từng câu và các bảng tổng hợp với dung sai nghiêm ngặt $\le 10^{-4}$ cho tất cả các chỉ số (kể cả thời gian phản hồi).
  4. Hợp đồng dữ liệu Pydantic, API endpoints và đóng gói Docker container production sạch sẽ.
- **Giới hạn của môi trường CI:**
  1. Do tài nguyên máy chủ ảo GitHub Actions (Ubuntu runner) không có GPU chuyên dụng và không duy trì thường trực dịch vụ LLM Ollama cục bộ, CI **chưa chạy lại toàn bộ 400 câu hỏi sinh văn bản thời gian thực (real-time generation)** của bài so sánh 4 pipeline.
  2. Việc tái lập bài chạy sinh văn bản đầy đủ cần được thực hiện trong môi trường cục bộ có phần cứng phù hợp (Apple Silicon M-series hoặc GPU NVIDIA) theo đúng hướng dẫn tại Mục 3 (Bước 5).

