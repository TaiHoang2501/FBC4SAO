# CLAUDE.md — Hướng Dẫn Phát Triển Dự Án FBC4SAO

> Tài liệu hướng dẫn cho AI Coding Assistants và Developers khi làm việc trên codebase FBC4SAO.

---

## 1. Lệnh Phát Triển & Kiểm Thử Thường Dùng

### Khởi chạy Backend
```bash
# Chạy backend development (reload tự động)
make dev
# hoặc
uvicorn src.main:app --reload --port 8000
```

### Chạy Đánh Giá Thực Nghiệm
```bash
# Đánh giá 100 câu hỏi luận văn
make eval
# hoặc
python eval/thesis_eval.py --file eval/ground_truth_final.json

# Đánh giá so sánh 4 pipelines
make comparative-eval
# hoặc
python eval/comparative_eval.py
```

### Chạy Kiểm Thử Đơn Vị (Tests)
```bash
make test
# hoặc
pytest tests/ -v
```

### Kiểm Tra Chất Lượng Mã Nguồn (Lint & Format)
```bash
make lint
make format
```

---

## 2. Quy Chuẩn Kiến Trúc & Cấu Trúc Thư Mục

- **`src/`**: Chứa toàn bộ mã nguồn nghiệp vụ chính. Không lưu file tạm, dữ liệu hay kết quả test ở đây.
- **`eval/`**: Chứa toàn bộ kịch bản đánh giá, file ground truth (`ground_truth_final.json`), và file kết quả JSON.
- **`data/`**: Chứa các file cơ sở dữ liệu (`conversation.db`, `semantic_cache.db`), index lưu trữ (`bm25_index.pkl`, `qdrant_storage/`), và tài liệu tham khảo.
- **`frontend/`**: Chứa client ứng dụng (Java Swing GUI, logo, v.v.).
- **`docs/`**: Chứa tài liệu giải thích kiến trúc, tổng quan hệ thống.
- **`presentation/`**: Chứa bài báo khoa học, slide trình bày và hình vẽ biểu đồ.

---

## 3. Quy Tắc Viết Code (Coding Conventions)
- **Python Version**: >= 3.12
- **Linter & Formatter**: Tuân thủ cấu hình trong `ruff.toml`.
- **Đường dẫn**: Luôn xử lý linh hoạt fallback đường dẫn tương đối và đường dẫn từ `PROJECT_ROOT / "data"`.
- **Trích dẫn nguồn**: Mọi câu trả lời của Agent tư vấn bắt buộc phải kèm trích dẫn nguồn dạng `[n]` và danh mục liên kết tài liệu ở cuối câu.
