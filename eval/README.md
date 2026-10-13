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

1. **Routing Accuracy:** Tỷ lệ phân loại đúng agent chuyên môn ($1.0$ nếu đúng, $0.0$ nếu sai). Đối với 3 baseline không có Router (Standalone LLM, Naive RAG, Hybrid RAG), chỉ số này ghi nhận là **N/A**.
2. **ROUGE-L & Chuẩn hóa tiền tố nguồn:**
   - Sử dụng thuật toán Longest Common Subsequence (LCS) trên tập token từ vựng tiếng Việt.
   - Trước khi so khớp, tiền tố nguồn (`Nguồn:`, `Nguồn tham khảo:`, `Sources:`, `**Nguồn:**`, v.v.) và các ký hiệu trích dẫn (`[n]`, `[1, 2]`) được bóc tách triệt để bằng biểu thức chính quy chuẩn hóa (`clean_for_rouge`) để đảm bảo không làm sai lệch điểm số nội dung chính.
3. **Citation Compliance Rate:** Kiểm tra sự tuân thủ hình thức trích dẫn `[n]` trong văn bản và sự hiện diện của danh sách tài liệu nguồn tham khảo hợp lệ từ retriever.
4. **Quy ước Phân vị Độ trễ (Percentiles):**
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
Dự án cung cấp bộ công cụ tự động kiểm tra tính nhất quán dữ liệu, tính tái lập toán học, regex bóc tách nguồn và sự sẵn sàng của thư viện BERTScore:
```bash
python eval/verify_reproducibility.py
```
*Kết quả kỳ vọng: 5/5 bài kiểm tra đều hiển thị `✅ PASS`.*

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

## 4. Kiểm Thử Đơn Vị & Hợp Đồng Dữ Liệu (Unit & Contract Tests)

Để xác nhận hệ thống backend và các hợp đồng Pydantic hoạt động chính xác trước khi chạy benchmark:
```bash
pytest tests/ -v
```
*Kết quả kỳ vọng: 11/11 tests PASS (bao gồm 6 contract tests, 4 integration tests, 1 snapshot test).*
