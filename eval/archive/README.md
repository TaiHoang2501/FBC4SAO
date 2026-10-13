# Thư Mục Lưu Trữ Kết Quả Lịch Sử (Evaluation Archive)

Thư mục này chứa các tệp kết quả thử nghiệm và artifact từ các phiên bản trước nhằm đảm bảo tính truy vết (provenance) và tính toàn vẹn lịch sử nghiên cứu.

---

### Danh mục tệp lưu trữ

#### `standard_metrics_legacy.json`
* **Nguồn gốc (Origin):** Được tạo ra trong giai đoạn thử nghiệm sơ khai (commit `261a8f1`).
* **Mục đích ban đầu:** Đo lường độ phủ truy xuất nhị phân (`accuracy = 1.0` thể hiện có ít nhất 1 tài liệu liên quan được bốc tách) cùng các chỉ số trùng khớp token truyền thống (`precision: 0.69`, `recall: 0.21`, `f1: 0.31`) trong điều kiện không bật Semantic Cache (độ trễ trung bình ~17.0s).
* **Trạng thái:** **Deprecated / Superseded**. 
* **Bộ dữ liệu thay thế chính thức (Canonical Thesis Evaluation Artifacts):**
  1. [`eval/results_improved_final.json`](../results_improved_final.json): Chi tiết 100 câu hỏi đánh giá hệ thống Live API hoàn chỉnh (kèm nhãn phương pháp chấm từng câu `semantic_metric_method`).
  2. [`eval/thesis_metrics.json`](../thesis_metrics.json): Bảng tổng hợp theo 7 kịch bản (Live Evaluation) với đầy đủ chỉ số Micro-Average và Macro-Average.
  3. [`eval/comparative_results.json`](../comparative_results.json): Thực nghiệm so sánh 4 pipeline (Comparative Pipeline Evaluation) có đối chiếu độ trễ chi tiết.
