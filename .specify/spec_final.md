# System Specification: FBC4SAO

## 1. Mục Tiêu Dự Án
Xây dựng hệ thống Chatbot RAG đa tác nhân thích ứng (Adaptive Agentic RAG) nhằm hỗ trợ học sinh định hướng hoạt động ngoại khóa phục vụ mục tiêu du học dựa trên lý thuyết mật mã Holland (RIASEC).

## 2. Các Yêu Cầu Chức Năng (Functional Requirements)
1. **Chẩn đoán RIASEC:** Bóc tách tính cách, sở thích và đề xuất mã Holland phù hợp.
2. **Thiết kế Lộ trình Ngoại khóa 3 cấp độ:**
   - Cấp độ 1: Hoạt động nền tảng (Foundation)
   - Cấp độ 2: Hoạt động chuyên môn (Professional)
   - Cấp độ 3: Hoạt động mang màu sắc cá nhân (Personal Spike)
3. **Đối chiếu Hồ sơ 10 năm:** Tìm kiếm hồ sơ học sinh tương tự trong quá khứ đã trúng tuyển vào các trường quốc tế để làm căn cứ tư vấn.
4. **Trích dẫn Minh bạch:** Toàn bộ tư vấn phải có nguồn kiểm chứng `[n]`, dẫn link tài liệu xác thực.
5. **Đệm Ngữ Nghĩa (Semantic Cache):** Trả lời tức thì câu hỏi quen thuộc với Cosine similarity >= 0.92.

## 3. Chỉ Số Chất Lượng (Quality Attributes & Benchmarks)
- Routing Accuracy >= 0.85
- BERTScore F1 >= 0.75
- Citation Accuracy >= 0.80
- Response Time <= 10.0 giây
