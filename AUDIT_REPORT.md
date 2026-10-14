# BÁO CÁO TOÀN DIỆN AUDIT HỆ THỐNG VÀ THỰC NGHIỆM KHOA HỌC: REPOSITORY FBC4SAO

> **Mục đích:** Báo cáo kiểm định độc lập mã nguồn, cơ sở dữ liệu thực nghiệm, tính toàn vẹn tái lập (reproducibility) và tính bảo mật của repository [FBC4SAO](https://github.com/TaiHoang2501/FBC4SAO) trước khi nộp hồ sơ ứng tuyển vị trí **Research Assistant (Trợ lý Nghiên cứu AI/NLP)** tại **VinUniversity**.  
> **Thời điểm thẩm định:** 14/10/2026.  
> **Nguyên tắc thẩm định:** Liêm chính học thuật (Academic Integrity), khách quan thực chứng, không che giấu giới hạn, bảo tồn dữ liệu gốc, minh bạch giữa kết quả lưu trữ (Observed) và kết quả tái lập (Verified/Reproduced).

---

## A. EXECUTIVE SUMMARY (TỔNG QUAN ĐIỀU HÀNH)

### 1. Trạng Thái Tổng Thể
Repository **FBC4SAO** là một công trình nghiên cứu ứng dụng có nền tảng kiến trúc kỹ thuật rất tốt: kết hợp mô hình Đa tác tử (Adaptive Multi-Agent Router 7 nhóm), Tìm kiếm lai (Hybrid Search BM25 + Qdrant Dense Vector), Xếp hạng lại (Cross-Encoder Reranker) và Bộ đệm ngữ nghĩa (Semantic Cache SQLite). 

Tuy nhiên, qua audit tĩnh và đối soát dữ liệu thực nghiệm, hệ thống bộc lộ **3 vấn đề cốt lõi về mặt phương pháp luận đánh giá (evaluation methodology)** cần được minh định rạch ròi trước hội đồng học thuật VinUniversity:
1. **Bộ Ground Truth 100 câu hỏi nhưng chỉ có 7 văn bản tham chiếu chung:** Mỗi kịch bản (S1–S7) dùng chung 1 đoạn văn mẫu, làm méo mó các chỉ số so khớp n-gram (ROUGE-L) và điểm ngữ nghĩa (BERTScore).
2. **Bản chất của chỉ số Citation:** Hiện chỉ đo *Citation Compliance Rate* (tính hợp lệ của ký hiệu `[n]` và chỉ mục trong mảng nguồn), chưa phải kiểm chứng tính xác thực ở mức nhận định (*claim-level factual attribution / NLI entailment*).
3. **Phân tách không gian đo lường Ngữ nghĩa:** Điểm Live E2E ($0.8558$) dùng *LLM-as-a-Judge*, còn Bảng so sánh ($0.6723 - 0.6852$) dùng *BERTScore vi F1*. Đây là hai không gian thang đo khác nhau, không được so sánh đồng cấp.

### 2. Những Vấn Đề Nghiêm Trọng Nhất Đã Phát Hiện
| Cấp độ | Vấn đề | Vị trí | Tác động học thuật |
|:---:|:---|:---|:---|
| **P0** | **Ground Truth Templates**: 100 câu hỏi nhưng chỉ có 7 reference duy nhất | `eval/ground_truth_final.json` | Khi câu hỏi hỏi cụ thể nhóm Holland R (S1.1), mô hình trả lời trúng đích vẫn bị trừ điểm vì reference mẫu liệt kê cả 6 nhóm R-I-A-S-E-C. |
| **P0** | **Citation Semantics**: Nhầm lẫn giữa tuân thủ định dạng và độ trung thực | `eval/comparative_eval.py` | Bảng điểm báo 100% (Hybrid) và 76% (Adaptive) là tỷ lệ tuân thủ cú pháp trích dẫn, chưa chứng minh câu trả lời được nguồn bảo chứng. |
| **P0** | **Lệch Model trong Thực nghiệm vs README**: Thực nghiệm dùng 7B, tài liệu ghi 0.8B | `README.md`, `.env.example` | Benchmark chạy trên `qwen2.5:7b-instruct-q4_K_M`, nhưng tài liệu hướng dẫn kéo `qwen3.5:0.8b` (mô hình 0.8B không đủ năng lực suy luận tiếng Việt tương đương). |
| **P1** | **Routing Accuracy Rigid Labeling**: Nhãn kỳ vọng bị gán cứng theo scenario | `eval/ground_truth_final.json` | Câu hỏi so sánh khái niệm ở S2 bị router phân vào `hoidapchung` là hợp lý về nghiệp vụ nhưng bị chấm sai vì ground truth ép buộc nhãn `hdnk_nentang`. |
| **P1** | **Đường dẫn cục bộ tuyệt đối trong Scripts Ingestion**: Lỗi tính khả chuyển | `scripts/*.py`, `HollandRAGGUI.java` | Nhiều script chứa đường dẫn cứng `/Users/macos/Downloads/...` và gọi `.venv312/bin/python` tương đối gây lỗi khi chạy từ thư mục con. |

### 3. Những Việc Đã Sửa Trực Tiếp Trong Đợt Audit
- ✅ **Bảo mật & Ổn định API (`src/main.py`)**: Sửa cấu hình CORS (`allow_credentials=False` khi `allow_origins=["*"]`), tự động tạo thư mục `uploads/` tránh lỗi `FileNotFoundError` khi upload PDF.
- ✅ **Khả năng chạy của Java Bridge (`src/java_bridge.py`, `frontend/HollandRAGGUI.java`)**: Hỗ trợ tìm kiếm tự động `data/production_model.pkl` và tự động phát hiện đường dẫn Python/Bridge script bất kể chạy từ root hay từ `frontend/`.
- ✅ **Khả chuyển hóa toàn bộ Scripts (`scripts/*.py`)**: Thay thế đường dẫn tuyệt đối bằng `Path(__file__).resolve().parent.parent / "data"` cho `direct_ingest.py`, `ingest_references.py`, `ingest_cvs_batch.py`.
- ✅ **Nâng cấp Bộ Xác Minh Tái Lập (`eval/verify_reproducibility.py`)**: Bổ sung hàm kiểm tra Schema, kiểm tra tính duy nhất của 100 câu hỏi, kiểm tra số hữu hạn (`math.isfinite()`) không chứa NaN/Inf, và ghi nhận thông báo học thuật về cấu trúc reference.
- ✅ **Đồng bộ Tài liệu & Điều kiện Thực nghiệm (`README.md`, `Makefile`, `.env.example`)**: 
  - Khuyến nghị model `qwen2.5:7b-instruct-q4_K_M` đồng nhất với metadata thực nghiệm.
  - Đồng bộ cổng mặc định `8001` trên toàn bộ tài liệu và `Makefile`.
  - Phân định rõ 3 cấp độ: *Observed Results*, *Verified Results*, và *Reproduced Results*.
  - Công khai minh bạch 3 giới hạn học thuật quan trọng ngay trên `README.md`.

### 4. Những Việc Chưa Sửa Hoặc Chưa Thể Xác Minh Độc Lập
- ⏳ **Chưa biên soạn lại toàn bộ 100 câu trả lời tham chiếu (Ground Truth References):** Giữ nguyên tệp gốc `eval/ground_truth_final.json` theo đúng nguyên tắc không can thiệp dữ liệu thực nghiệm lịch sử khi chưa có hội đồng chuyên môn may đo và duyệt từng câu.
- ⏳ **Chưa tái lập đầy đủ 400 lượt gọi LLM ngoại tuyến (Reproduced Results):** Chưa chạy lại toàn bộ benchmark sinh văn bản mới vì đòi hỏi hạ tầng GPU chuyên dụng chạy Ollama 7B và đối soát thời gian thực trong nhiều giờ.

---

## B. REPOSITORY & README AUDIT

### 1. Danh Mục Các Tệp Đã Kiểm Tra Tĩnh & Kiểm Tra Động
- **Mã nguồn lõi (`src/`)**: `main.py`, `agents.py`, `vector_db.py`, `reranker.py`, `semantic_cache.py`, `llm_service.py`, `conversation_store.py`, `java_bridge.py`, `crawler.py`, `data_loader.py`.
- **Dữ liệu & Benchmark (`eval/`)**: `ground_truth_final.json`, `results_improved_final.json`, `thesis_metrics.json`, `comparative_results.json`, `comparative_eval.py`, `thesis_eval.py`, `verify_reproducibility.py`.
- **Hạ tầng kiểm thử (`tests/`)**: `test_evaluation_metrics.py`, `contract/test_models.py`, `integration/test_api.py`.
- **Scripts hỗ trợ (`scripts/`)**: `direct_ingest.py`, `ingest_references.py`, `ingest_cvs_batch.py`, `ingest_riasec_data.py`.
- **Cấu hình & CI**: `pyproject.toml`, `requirements.txt`, `Makefile`, `Dockerfile`, `.github/workflows/ci.yml`, `.env.example`.

### 2. Các Lệnh Đã Thực Thi & Kết Quả Thực Tế
| Lệnh kiểm tra | Mục đích | Kết quả thực tế | Trạng thái |
|:---|:---|:---|:---:|
| `pytest tests/ -v -m "not external"` | Chạy toàn bộ 36 unit tests độc lập | 36 passed trong 25.67s | ✅ PASS |
| `python eval/verify_reproducibility.py --ci` | Xác minh schema, dữ liệu canonical, đối soát tái lập Micro/Macro & Bảng so sánh 4 pipeline | 5/5 bài kiểm tra đạt, diff = 0.000000 | ✅ PASS |
| `git check-ignore -v .env` | Xác minh file môi trường nhạy cảm không bị track | `.gitignore:2:.env .env` | ✅ PASS |
| `javac frontend/HollandRAGGUI.java` | Biên dịch giao diện đồ họa Java Swing | Biên dịch sạch, exit code 0 | ✅ PASS |
| `python -c "from src.java_bridge import load_system; ..."` | Kiểm tra nạp mô hình sản xuất từ `data/production_model.pkl` | System loaded: True, Version: 1.0.0 | ✅ PASS |

### 3. Đối Chiếu README vs Code Thực Tế & Cách Xử Lý
1. **Lệch Model suy luận:**
   - *README cũ:* `ollama pull qwen3.5:0.8b`.
   - *Thực tế:* File `comparative_results.json` và `thesis_metrics.json` lưu provenance rõ ràng: `model: qwen2.5:7b-instruct-q4_K_M`.
   - *Xử lý:* Cập nhật README chỉ rõ model 7B là model chuẩn thực nghiệm; model 0.8B chỉ dùng smoke test.
2. **Lệch Port kết nối:**
   - *README cũ:* Ghi lẫn lộn giữa port `8001` (hướng dẫn chạy) và port `8000` (trong Makefile).
   - *Xử lý:* Đặt biến `PORT ?= 8001` trong `Makefile` đồng nhất với README và `thesis_eval.py`.
3. **Mục đích của script Ingestion:**
   - *README cũ:* Yêu cầu chạy `python scripts/ingest_riasec_data.py` (vốn là script mẫu đọc file CSV 145k mẫu không kèm trong repo).
   - *Xử lý:* Làm rõ thư mục `data/` đã có sẵn dữ liệu index và chỉ mục BM25/Qdrant; script trên đóng vai trò mã nguồn tham khảo ETL.

---

## C. SECURITY AUDIT (BẢO MẬT & BẢO VỆ DỮ LIỆU)

### 1. Phạm Vi Kiểm Tra
- Quét biểu thức chính quy (Regex Scan) tìm kiếm các chuỗi định dạng secret: `ghp_`, `gho_`, `sk-`, `AIza`, AWS keys, Private Keys trên toàn bộ cây thư mục đang theo dõi (`git ls-files`).
- Quét lịch sử commit Git (`git log -p`) tìm các secret từng bị commit trong quá khứ.
- Kiểm tra cấu hình bảo vệ tệp môi trường (`.gitignore`).
- Kiểm tra mã nguồn API về CORS, phân quyền, SQL Injection, và xử lý upload file.

### 2. Phát Hiện Theo Mức Độ Nghiêm Trọng

#### 🟢 Low / Info — Dữ liệu Email trong Nhật ký AI (`.ai-log/archive/`)
- **Vị trí:** `.ai-log/archive/2026-10-12.jsonl`, `2026-10-09.jsonl`
- **Mô tả:** Các tệp ghi nhận prompt của sinh viên có chứa địa chỉ email (`hoanganhtaia1@gmail.com`) và tên repo dự án học phần.
- **Đánh giá rủi ro:** Đây là email sinh viên phục vụ truy vết bài nộp học phần, không chứa mật khẩu hay API key. Tuy nhiên, khi công khai mở rộng nên cân nhắc ẩn danh hóa nếu cần bảo vệ quyền riêng tư cá nhân.

#### 🟡 Medium (Đã sửa) — CORS Wildcard kết hợp Credentials
- **Vị trí:** `src/main.py:68`
- **Mô tả:** Cấu hình `allow_origins=["*"]` đi kèm `allow_credentials=True` vi phạm đặc tả CORS W3C và bị trình duyệt cảnh báo.
- **Xử lý:** Đã chuyển thành `allow_credentials=False` cho cấu hình wildcard public API.

#### 🟡 Medium (Đã sửa) — Upload File Path Traversal & Missing Dir
- **Vị trí:** `src/main.py:328`
- **Mô tả:** `tempfile.NamedTemporaryFile(dir="uploads")` giả định thư mục `uploads` luôn tồn tại. Nếu chưa tạo thư mục, endpoint trả về mã lỗi 500.
- **Xử lý:** Bổ sung `Path("uploads").mkdir(parents=True, exist_ok=True)`.

#### 🟢 An toàn — SQL Injection
- **Vị trí:** `src/conversation_store.py`
- **Đánh giá:** Toàn bộ các câu lệnh SQLite đều sử dụng tham số hóa (`?`), tuyệt đối không ghép chuỗi SQL trực tiếp. An toàn trước SQL Injection.

### 3. Các Khu Vực Chưa Thể Thẩm Định Toàn Diện
- Chưa chạy công cụ phân tích phụ thuộc chuyên sâu (ví dụ `pip-audit` / Snyk) do môi trường mạng hạn chế tải cơ sở dữ liệu CVE thời gian thực. Các dependency được ghim phiên bản cụ thể trong `pyproject.toml`.

---

## D. BENCHMARK & GROUND TRUTH AUDIT

### 1. Thực Trạng Cấu Trúc Bộ Dữ Liệu `eval/ground_truth_final.json`
- **Tổng số mẫu:** 100 mẫu.
- **Số câu hỏi duy nhất:** 100 câu hỏi (100% unique, bao quát 7 kịch bản từ S1 đến S7).
- **Số câu trả lời tham chiếu duy nhất:** **Đúng 7 câu trả lời tham chiếu**.
- **Cơ chế phân bổ hiện tại:** 
  $$\forall q_i \in \text{Scenario } S_k \implies \text{Reference}(q_i) = \text{Template}_k$$

### 2. Các Trường Hợp Không Phù Hợp Điển Hình Được Xác Nhận
1. **Kịch bản S1 (Chẩn đoán RIASEC - 14 câu):**
   - Câu hỏi S1.01: *"Em hay thích tháo lắp máy móc và làm thủ công. Em thuộc nhóm Holland nào?"* $\rightarrow$ Đáp án chuẩn phải là **Nhóm Kỹ thuật (Realistic - R)**.
   - Reference thực tế: Liệt kê dàn trải cả 6 nhóm R, I, A, S, E, C.
   - *Hệ quả:* Mô hình trả lời chuẩn xác và tập trung vào nhóm R sẽ bị trừ điểm ROUGE-L và BERTScore vì không nhắc đến 5 nhóm còn lại!
2. **Kịch bản S7 (Hỏi đáp chung - 16 câu):**
   - Câu hỏi S7.04: *"Hệ thống Holland RIASEC ra đời từ năm nào và độ tin cậy ra sao?"* $\rightarrow$ Đáp án chuẩn cần mốc năm 1959 (John Holland) và độ tin cậy trắc nghiệm.
   - Reference thực tế: Đoạn giới thiệu chung *"Hệ thống RAG Tư vấn Hướng nghiệp cung cấp các thông tin tổng quát... Xin lưu ý hệ thống chỉ trả lời các vấn đề liên quan..."*.
   - *Hệ quả:* Hoàn toàn lệch thông tin sự thật (fact mismatch).
3. **Kịch bản S4 (Hoạt động cá nhân - 14 câu):**
   - Các câu hỏi từ cờ vua, bóng rổ, taekwondo đến viết blog đều đối chiếu với cùng một đoạn văn chung về âm nhạc/thể thao/nghệ thuật.

### 3. Tác Động Đến Các Metric Đã Báo Cáo
- **ROUGE-L (Bị nén thấp nhân tạo):** Điểm ROUGE-L của toàn hệ thống chỉ đạt $0.11 - 0.13$. Nguyên nhân lớn không phải do mô hình sinh từ ngữ kém, mà do câu trả lời đúng trọng tâm của mô hình không thể trùng khớp từ vựng với một đoạn văn mẫu dài liệt kê nhiều chủ đề không liên quan.
- **BERTScore F1 & LLM-as-a-Judge (Dễ bị nhiễu):** Điểm ngữ nghĩa phản ánh độ tương đồng với văn bản mẫu đóng khung chứ chưa đo lường độ đúng đắn của thông tin trả lời cho câu hỏi cụ thể.
- **Routing Accuracy (Bị phạt bởi nhãn cứng):** Trong 100 câu, 15 câu router phân loại khác nhãn kỳ vọng phần lớn là các câu hỏi ranh giới (ví dụ hỏi khái niệm ngoại khóa nền tảng thì router xếp vào `hoidapchung`, nhưng nhãn cứng ép vào `hdnk_nentang`). Độ chính xác 80–85% thực tế phản ánh sự bất đồng định nghĩa hơn là lỗi kỹ thuật của Router.

### 4. Đề Xuất Chuẩn Hóa Schema Mới (Kế hoạch V2)
Đề xuất chuẩn hóa schema cho tập ground truth trong tương lai (không ghi đè file hiện tại):
```json
{
  "id": "GT-S1-01",
  "scenario": "S1",
  "scenario_type": "standard",
  "question": "Em hay thích tháo lắp máy móc và làm thủ công. Em thuộc nhóm Holland nào?",
  "expected_agent": "test_riasec",
  "acceptable_agents": ["test_riasec"],
  "key_facts": [
    "Nhóm Kỹ thuật (Realistic - R)",
    "Đặc điểm: thích công cụ, máy móc, vận động thực hành",
    "Gợi ý làm bài test hoàn chỉnh để có mã đầy đủ"
  ],
  "reference": "Dựa trên sở thích tháo lắp máy móc và làm thủ công, bạn có thiên hướng thuộc nhóm Kỹ thuật (Realistic - R) trong mô hình Holland RIASEC. Nhóm này đại diện cho những người thực tế, thích làm việc với các đồ vật, công cụ và máy móc cụ thể. Bạn nên thực hiện bài trắc nghiệm RIASEC đầy đủ để tìm ra tổ hợp mã chính xác [1].",
  "citation_required": true
}
```

---

## E. REPRODUCIBILITY AUDIT (TÍNH TÁI LẬP THỰC NGHIỆM)

### 1. Phân Cấp Các Cấp Độ Kiểm Thử Hiện Tại
| Cấp độ | Lệnh thực thi | Nội dung thực hiện | Bằng chứng kiểm chứng |
|:---|:---|:---|:---|
| **Cấp 1: Kiểm thử Đơn vị (Unit Tests)** | `pytest tests/ -v -m "not external"` | 36 bài test kiểm tra logic hàm, schema Pydantic, edge cases của metrics | 36/36 tests PASSED trong 25.67s |
| **Cấp 2: Xác thực Schema & Toàn vẹn Dữ liệu** | `python eval/verify_reproducibility.py --ci` (Mục 1 & 2) | Kiểm tra 100 câu hỏi duy nhất, schema trường bắt buộc, không chứa NaN/Inf | 100% trường hợp hữu hạn, không lỗi cú pháp |
| **Cấp 3: Đối soát Tái lập Toán học (Mathematical Re-aggregation)** | `python eval/verify_reproducibility.py --ci` (Mục 3 & 4) | Tính lại Micro/Macro 7 kịch bản và bảng so sánh 4 pipeline từ mảng `details` | Dung sai đối soát tuyệt đối $\le 10^{-4}$ ($0.000000$) |
| **Cấp 4: Smoke Test Chu trình Lõi** | `python eval/verify_reproducibility.py --smoke-eval` | Chạy 1 câu hỏi mẫu qua toàn bộ Router $\rightarrow$ Search $\rightarrow$ Rerank $\rightarrow$ LLM $\rightarrow$ Live Metrics | Khả thi khi có Ollama runtime |
| **Cấp 5: Tái lập Thực nghiệm Toàn bộ (Full Rerun)** | `python eval/comparative_eval.py` | Chạy lại 400 lượt sinh văn bản ngoại tuyến và đánh giá tự động | Chưa thực hiện độc lập trong đợt audit này |

### 2. Minh Định Về Kết Quả Tái Lập
> ⚠️ **Tuyên bố quan trọng:** Việc `verify_reproducibility.py` báo **PASS** chứng minh rằng: **Các số liệu tổng hợp trong báo cáo luận văn và bảng so sánh hoàn toàn nhất quán về mặt toán học với các kết quả đo lường chi tiết từng mẫu đã lưu trữ**. Điều này ngăn chặn việc làm giả số liệu summary, nhưng **chưa phải là bằng chứng thay thế cho một lần chạy lại toàn bộ mô hình (end-to-end model inference) trên phần cứng mới**.

---

## F. CHANGE LOG (NHẬT KÝ THAY ĐỔI)

| Tệp thay đổi | Vấn đề phát hiện | Thay đổi đã thực hiện | Lý do | Cách kiểm tra lại |
|:---|:---|:---|:---|:---|
| [`src/main.py`](src/main.py) | CORS wildcard có credentials; thiếu tự động tạo thư mục upload | Đổi `allow_credentials=False`; thêm `Path("uploads").mkdir(parents=True, exist_ok=True)` | Tuân thủ W3C CORS; tránh lỗi 500 khi upload tài liệu mới | `pytest tests/integration/test_api.py` |
| [`src/java_bridge.py`](src/java_bridge.py) | Không tìm thấy `production_model.pkl` ở thư mục gốc | Bổ sung đường dẫn tìm kiếm `data/production_model.pkl` và chuẩn hóa `sys.path` | Đảm bảo nạp đúng mô hình cấu hình đa tác tử đã xuất xưởng | `python -c "from src.java_bridge import load_system; assert load_system()"` |
| [`frontend/HollandRAGGUI.java`](frontend/HollandRAGGUI.java) | Lỗi đường dẫn khi chạy từ thư mục con `frontend/` | Thêm hàm `resolvePath()` tìm kiếm `.venv312` và script từ cả cấp cha và cấp hiện tại | Khả chuyển mã nguồn khi chạy bằng cả `make frontend` lẫn chạy thủ công | `cd frontend && javac HollandRAGGUI.java` |
| [`scripts/*.py`](scripts/) | Hardcode đường dẫn tuyệt đối macOS của máy cá nhân | Đổi sang `Path(__file__).resolve().parent.parent / "data"` | Chạy được trên mọi máy tính và hệ điều hành | Chạy thử cú pháp Python các script trong `scripts/` |
| [`eval/verify_reproducibility.py`](eval/verify_reproducibility.py) | Thiếu kiểm tra schema và số hữu hạn | Thêm mục kiểm tra schema dữ liệu, check NaN/Inf, và thông báo học thuật về reference | Siết chặt quy chuẩn kiểm toán dữ liệu benchmark | `python eval/verify_reproducibility.py --ci` |
| [`Makefile`](Makefile) | Lệch port mặc định (8000 vs 8001); thiếu lệnh audit | Định nghĩa `PORT ?= 8001`, thêm target `audit` | Đồng bộ toàn bộ tài liệu hướng dẫn | `make -n audit` |
| [`README.md`](README.md) | Ghi sai model thực nghiệm (0.8B vs 7B); thiếu phân định Observed/Verified | Cập nhật model 7B chuẩn; thêm ma trận 3 cấp độ kết quả và 3 lưu ý học thuật | Đảm bảo tính trung thực và minh bạch học thuật | Đọc duyệt trực quan tài liệu |
| [`.env.example`](.env.example) | Ghi mặc định model 0.8B gây hiểu lầm | Ghi chú rõ model 7B cho thực nghiệm chuẩn, 0.8B cho smoke test | Tránh cấu hình sai khi tái lập | Kiểm tra nội dung tệp |

---

## G. REMAINING ISSUES & LỘ TRÌNH KHẮC PHỤC (ROADMAP)

### Ưu tiên P0 (Cần hoàn thiện trước khi xuất bản bài báo / nộp luận văn chính thức)
1. **Biên soạn lại Bộ Ground Truth May đo (Item-level References):**
   - *Hành động:* Xây dựng 100 câu trả lời tham chiếu độc lập cho từng câu hỏi, có cấu trúc `key_facts` làm rubric chấm điểm.
   - *Tác động:* Giúp chỉ số ROUGE-L và BERTScore phản ánh chính xác chất lượng sinh văn bản của từng pipeline.
2. **Nâng cấp Metric Citation sang Đánh giá Ngữ nghĩa (NLI / Claim Attribution):**
   - *Hành động:* Bổ sung mô hình Natural Language Inference (ví dụ `cross-encoder/nli-deberta-v3-base`) để kiểm tra xem từng nhận định trong câu trả lời có được tài liệu trích dẫn suy diễn logic (entailment) hay không.

### Ưu tiên P1 (Hoàn thiện mã nguồn & Giao thức thực nghiệm)
1. **Thẩm định lại nhãn Router cho các câu hỏi đa ý:**
   - *Hành động:* Cho phép trường `acceptable_agents` trong ground truth (ví dụ câu hỏi so sánh ngoại khóa chấp nhận cả `hdnk_nentang` hoặc `hoidapchung`).
2. **Lưu trữ Raw Log của lần chạy Benchmark:**
   - *Hành động:* Xuất file log chi tiết chứa toàn bộ prompt, raw LLM completion, danh sách contexts retrieval và thời gian từng chặng cho mỗi truy vấn.

---

## H. KẾT LUẬN NỘP HỒ SƠ VINUNIVERSITY RESEARCH ASSISTANT

### Đánh giá: **ĐỦ TIÊU CHUẨN ĐƯA VÀO HỒ SƠ ỨNG TUYỂN (READY WITH ACADEMIC MATURITY)**

### Lý do:
1. **Kỹ thuật nền tảng vững chắc:** Kiến trúc Multi-Agent Router, Hybrid Search BM25 + Qdrant, Cross-Encoder Reranking, và Semantic Cache là những kỹ thuật RAG tiên tiến, được triển khai hoàn chỉnh bằng code thực tế, có kiểm thử hợp đồng và kiểm thử tích hợp (36 unit tests pass).
2. **Tính trung thực và Minh bạch học thuật:** Việc repository công khai rõ ràng các kết quả thực nghiệm (*Observed Results*), chứng minh được tính nhất quán toán học (*Verified Results*), và **chủ động thừa nhận giới hạn của bộ Ground Truth cũng như bản chất của Citation Compliance** là một điểm cộng cực kỳ lớn trong mắt các giáo sư nghiên cứu tại VinUniversity. Nó thể hiện tư duy nghiên cứu chín chắn (research maturity), không làm đẹp số liệu hay tuyên bố quá đà.

### Các Điểm Cần Chủ Động Trình Bày Khi Phỏng Vấn:
Khi giảng viên hoặc hội đồng phỏng vấn đặt câu hỏi về dự án, bạn nên chủ động làm rõ 3 luận điểm sau để ghi điểm chuyên môn:
1. *"Chỉ số Citation trong bảng so sánh của em là **Citation Compliance Rate** (kiểm tra tính hợp lệ của việc gắn thẻ nguồn và chỉ mục trích dẫn), bước tiếp theo em dự định mở rộng thêm mô hình NLI để đánh giá Factual Groundedness ở cấp độ từng mệnh đề (claim-level attribution)."*
2. *"Em chủ động tách biệt thang đo ngữ nghĩa giữa Hệ thống Live (**LLM-as-a-Judge**) và Bảng so sánh pipeline (**BERTScore vi F1**) vì chúng thuộc hai không gian toán học khác nhau."*
3. *"Ở phiên bản benchmark ban đầu, bộ dữ liệu 100 câu hỏi được thiết kế theo 7 kịch bản nghiệp vụ. Em đã phát hiện vấn đề mỗi kịch bản dùng chung một reference template làm nén điểm ROUGE-L, và hiện em đã lên kế hoạch xây dựng bộ ground truth V2 có rubric và reference may đo riêng cho từng câu hỏi."*
