# Data Flow Diagram (Sơ đồ Luồng Dữ Liệu) — FBC4SAO

> Tài liệu mô tả chi tiết đường đi của dòng dữ liệu (Data Flows) qua các tầng kiến trúc của hệ thống **FBC4SAO: Adaptive Agentic RAG**.
> Sơ đồ thể hiện rõ: **Tác nhân ngoài (External Entities)**, **Các tiến trình xử lý (Processes)**, **Các kho dữ liệu (Data Stores)** và **Dữ liệu truyền tải giữa các thành phần**.

---

## 1. Sơ đồ Luồng Dữ liệu Cấp 0 (Context Diagram - Level 0)

```mermaid
flowchart LR
    %% Tác nhân ngoài
    USER(["🎓 Học sinh / Người dùng<br/>(Student)"])
    ADMIN(["👨‍💼 Quản trị viên<br/>(Admin / Ingest)"])

    %% Hệ thống trung tâm
    SYSTEM[["⚡ HỆ THỐNG FBC4SAO<br/>Adaptive Agentic RAG<br/>(Advisory & Orientation)"]]

    %% Dịch vụ ngoài
    EXT_WEB[["🌐 Tavily Web Search API<br/>(Dynamic Web Fallback)"]]
    EXT_LLM[["🧠 LLM Provider<br/>(Ollama / OpenAI API)"]]

    %% Dòng dữ liệu Level 0
    USER -- "1. Câu hỏi tư vấn, mã phiên (session_id)" --> SYSTEM
    SYSTEM -- "2. Câu trả lời streaming kèm trích dẫn [n], nguồn tài liệu" --> USER

    ADMIN -- "3. Tài liệu ngoại khóa, CV, dữ liệu RIASEC mới" --> SYSTEM
    SYSTEM -- "4. Trạng thái ingest, thống kê cache & hệ thống" --> ADMIN

    SYSTEM -- "5. Từ khóa tìm kiếm bổ sung" --> EXT_WEB
    EXT_WEB -- "6. Đoạn trích web (web snippets & URLs)" --> SYSTEM

    SYSTEM -- "7. Prompt chuyên biệt của Agent + Chunks ngữ cảnh" --> EXT_LLM
    EXT_LLM -- "8. Luồng Tokens phản hồi (SSE Stream)" --> SYSTEM
```

---

## 2. Sơ đồ Luồng Dữ liệu Chi tiết Cấp 1 (DFD Level 1)

```mermaid
flowchart TD
    %% Tác nhân ngoài
    USER(["🎓 Học sinh / Người dùng"])
    
    %% Tầng Giao diện & Gateway
    subgraph UI_GATEWAY ["Tầng Giao Diện & Gateway API"]
        P0["0. Desktop GUI & API Gateway<br/>(FastAPI / HollandRAGGUI)"]
    end

    %% Các Tiến trình xử lý (Processes)
    subgraph PROCESSES ["Các Tiến Trình Xử Lý Nghiệp Vụ (Processes)"]
        P1["1.0 Tra Cứu Bộ Đệm Ngữ Nghĩa<br/>(Semantic Cache Lookup)"]
        P2["2.0 Phân Loại Ý Định<br/>(Multi-Agent Intent Router)"]
        P3["3.0 Truy Xuất Lai<br/>(Hybrid Search: BM25 + Dense Vector)"]
        P4["4.0 Mở Rộng Web Dự Phòng<br/>(Tavily Fallback Crawler)"]
        P5["5.0 Tái Xếp Hạng Ngữ Cảnh<br/>(Cross-Encoder Reranker)"]
        P6["6.0 Xây Dựng Prompt & Sinh Lời Giải<br/>(Prompt Builder & LLM Stream)"]
        P7["7.0 Lưu Trữ Phiên & Lịch Sử<br/>(Conversation Store Logger)"]
    end

    %% Các Kho Dữ Liệu (Data Stores)
    subgraph DATA_STORES ["Các Kho Dữ Liệu (Data Stores)"]
        D1[("D1: Semantic Cache DB<br/>(data/semantic_cache.db)")]
        D2[("D2: BM25 Lexical Index<br/>(data/bm25_index.pkl)")]
        D3[("D3: Qdrant Vector DB<br/>(data/qdrant_storage)")]
        D4[("D4: Conversation DB<br/>(data/conversation.db)")]
        D5[("D5: Tài Liệu Tham Khảo & CV<br/>(data/ tham khảo, CV)")]
    end

    %% Dòng dữ liệu chi tiết
    USER -- "Câu hỏi tư vấn" --> P0
    P0 -- "Query, Session ID" --> P1

    %% Luồng Cache
    P1 -- "Vector embedding câu hỏi" --> D1
    D1 -- "Cache Hit (Sim >= 0.92): Câu trả lời sẵn có" --> P0
    P0 -- "Phản hồi tức thì (<5ms)" --> USER

    %% Luồng Cache Miss -> Router
    P1 -- "Cache Miss: Chuyển câu hỏi" --> P2
    P2 -- "Phân loại: Agent ID chuyên môn (S1..S7)" --> P3

    %% Luồng Truy xuất
    P3 -- "Truy vấn từ khóa" --> D2
    D2 -- "Top Lexical Chunks (BM25)" --> P3

    P3 -- "Truy vấn Vector Embedding" --> D3
    D3 -- "Top Semantic Chunks (Cosine)" --> P3

    P3 -- "Hợp nhất kết quả (RRF Score)" --> P5

    %% Luồng Web Fallback (nếu thiếu thông tin)
    P3 -. "Độ tin cậy thấp / Thiếu thông tin" .-> P4
    P4 -- "Dữ liệu cào web thời gian thực" --> P5

    %% Luồng Rerank -> LLM
    P5 -- "Top-K Chunks liên quan cao nhất + Metadata nguồn" --> P6
    P6 -- "Luồng Tokens câu trả lời (SSE Stream)" --> P0
    P0 -- "Hiển thị câu trả lời + Trích dẫn [n]" --> USER

    %% Luồng Lưu vết
    P6 -- "Cặp câu hỏi + câu trả lời chuẩn" --> D1
    P6 -- "Lịch sử hội thoại (Role, Message, Timestamp)" --> P7
    P7 -- "Ghi log phiên" --> D4
```

---

## 3. Sơ đồ Luồng Dữ Liệu Tuần Tự (Sequence Trace)

```mermaid
sequenceDiagram
    autonumber
    actor User as Học sinh (Student)
    participant UI as Desktop GUI (Java)
    participant API as FastAPI Backend (src/main.py)
    participant Cache as D1: Semantic Cache (SQLite)
    participant Router as Multi-Agent Router (src/agents.py)
    participant Retriever as Hybrid Retriever (BM25 + Qdrant)
    participant Reranker as Reranker (src/reranker.py)
    participant LLM as LLM Engine (Ollama / OpenAI)
    participant Store as D4: Conversation Store (SQLite)

    User->>UI: Nhập câu hỏi tư vấn hướng nghiệp
    UI->>API: GET /query/stream?question=...&session_id=...
    API->>Cache: Kiểm tra câu hỏi tương đồng (Cosine Sim >= 0.92)
    alt Cache Hit (Có sẵn lời giải tương tự)
        Cache-->>API: Trả về câu trả lời đã lưu + nguồn tài liệu
        API-->>UI: Phản hồi tức thì (< 5ms)
    else Cache Miss (Câu hỏi mới)
        API->>Router: route_question(query)
        Router-->>API: Agent chuyên trách (S1..S7: Holland, Ngoại khóa, Hồ sơ...)
        API->>Retriever: agent_search(query, agent)
        Retriever->>Retriever: BM25 (data/bm25_index.pkl) + Vector (data/qdrant_storage)
        Retriever->>Retriever: Xếp hạng hợp nhất Reciprocal Rank Fusion (RRF)
        Retriever->>Reranker: rerank(candidate_chunks, query)
        Reranker-->>API: Danh sách Top Chunks tối ưu nhất
        API->>LLM: build_agent_prompt(query, contexts, sources)
        LLM-->>API: Dòng Tokens phản hồi theo thời gian thực (SSE)
        API-->>UI: Render từng Token trực tiếp lên màn hình
        API->>Cache: Lưu (query_vector, answer, sources) vào Semantic Cache
        API->>Store: Lưu tin nhắn hội thoại vào conversation.db
    end
    UI-->>User: Hoàn tất câu trả lời với đầy đủ trích dẫn nguồn [n]
```

---

## 4. Bảng Phân Tích Kho Dữ Liệu (Data Stores Matrix)

| Ký hiệu | Tên Kho Dữ Liệu | Đường dẫn vật lý | Tiến trình Ghi (Write) | Tiến trình Đọc (Read) | Mô tả & Định dạng |
|:---:|---|---|---|---|---|
| **D1** | **Semantic Cache** | `data/semantic_cache.db` | Tiến trình 6.0 (LLM Generator) | Tiến trình 1.0 (Cache Lookup) | SQLite lưu `(query_text, query_embedding, answer, sources, timestamp)` phục vụ tra cứu nhanh <5ms |
| **D2** | **BM25 Lexical Index** | `data/bm25_index.pkl` | Script Ingest dữ liệu ban đầu | Tiến trình 3.0 (Hybrid Search) | Pickle file chứa bộ chỉ mục từ khóa Okapi BM25 của toàn bộ kho tài liệu |
| **D3** | **Dense Vector DB** | `data/qdrant_storage` | Script Ingest dữ liệu ban đầu | Tiến trình 3.0 (Hybrid Search) | Qdrant Vector Storage lưu trữ vector embedding (dim=1536) và payload metadata của các chunks |
| **D4** | **Conversation Store** | `data/conversation.db` | Tiến trình 7.0 (Session Logger) | Tầng API Gateway | SQLite lưu bảng `messages (id, session_id, role, content, created_at)` quản lý lịch sử hội thoại |
| **D5** | **Reference Documents** | `data/` (`CV/`, `tham khảo/`) | Quản trị viên nạp thủ công | Script Ingest dữ liệu | Kho tài liệu nguồn: bài báo Holland, hồ sơ học sinh du học 10 năm, dữ liệu chuẩn RIASEC 145k |
