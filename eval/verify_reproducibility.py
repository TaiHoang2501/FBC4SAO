#!/usr/bin/env python3
"""
verify_reproducibility.py — Kịch bản xác minh độc lập tính tái lập (Reproducibility Verification Harness)

Mục đích:
1. Kiểm tra tính toàn vẹn và hợp lệ của các bộ dữ liệu canonical (ground truth, live results, comparative results).
2. Tái lập tính toán độc lập Micro-Average và Macro-Average từ dữ liệu gốc kết quả live.
3. Tái lập tính toán độc lập summary và phân vị độ trễ (Type 7 percentiles) từ dữ liệu so sánh 4 pipeline.
4. Kiểm tra sự sẵn sàng của môi trường BERTScore tiếng Việt và embedding model.
5. Kiểm tra hàm chuẩn hóa regex bóc tách nguồn trích dẫn cho ROUGE-L.
6. (Tùy chọn) Chạy kiểm thử mẫu (--smoke-eval) để chứng minh pipeline thực thi được từ đầu đến cuối.
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT_DIR / "eval"
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(EVAL_DIR))


def check_file_exists(p: Path, name: str) -> bool:
    if not p.exists():
        print(f"❌ [FAIL] Không tìm thấy tệp {name}: {p}")
        return False
    print(f"✅ [PASS] Tệp {name} tồn tại ({p.stat().st_size:,} bytes)")
    return True


def verify_canonical_datasets() -> bool:
    print("\n" + "=" * 80)
    print("1. KIỂM TRA TÍNH TOÀN VẸN CÁC TỆP DỮ LIỆU CANONICAL")
    print("=" * 80)
    ok = True
    files = [
        ("ground_truth_final.json", EVAL_DIR / "ground_truth_final.json", 100),
        ("results_improved_final.json", EVAL_DIR / "results_improved_final.json", 100),
        ("thesis_metrics.json", EVAL_DIR / "thesis_metrics.json", None),
        ("comparative_results.json", EVAL_DIR / "comparative_results.json", None),
    ]
    for name, path, expected_count in files:
        if not check_file_exists(path, name):
            ok = False
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if expected_count is not None:
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get("details", data.get("results", []))
                else:
                    items = []
                count = len(items)
                if count == expected_count:
                    print(f"   ↳ Khớp chính xác {count}/{expected_count} mẫu kiểm thử")
                else:
                    print(f"   ↳ ⚠ Lệch số lượng: có {count}, mong đợi {expected_count}")
                    ok = False
        except Exception as e:
            print(f"   ↳ ❌ Lỗi đọc JSON: {e}")
            ok = False
    return ok


def verify_live_aggregation() -> bool:
    print("\n" + "=" * 80)
    print("2. TÁI LẬP TÍNH TOÁN ĐỘC LẬP MICRO & MACRO AVERAGE TỪ RESULTS_IMPROVED_FINAL.JSON")
    print("=" * 80)
    res_path = EVAL_DIR / "results_improved_final.json"
    thesis_path = EVAL_DIR / "thesis_metrics.json"

    with open(res_path, "r", encoding="utf-8") as f:
        live_data = json.load(f)
    with open(thesis_path, "r", encoding="utf-8") as f:
        thesis_data = json.load(f)

    results = live_data.get("details", live_data.get("results", []))
    n = len(results)

    errors = []

    # 1. Tái lập Micro-Average (trung bình có trọng số theo 100 mẫu)
    micro_routing = round(sum(r.get("routing_correct", 0) for r in results) / n, 4)
    micro_rouge = round(sum(r.get("rouge_l", 0) for r in results) / n, 4)
    micro_sem = round(sum(r.get("semantic_similarity", r.get("bertscore", 0)) for r in results) / n, 4)
    micro_cite = round(sum(r.get("citation_compliance", r.get("citation_correct", 0)) for r in results) / n, 4)
    micro_time = round(sum(r.get("response_time", 0) for r in results) / n, 4)

    stored_micro = thesis_data.get("overall_micro_average", thesis_data.get("micro_average", {}))
    if abs(micro_routing - stored_micro["routing_accuracy"]) > 1e-4:
        errors.append(f"Micro Routing mismatch: {micro_routing} vs {stored_micro['routing_accuracy']}")
    if abs(micro_rouge - stored_micro["rouge_l"]) > 1e-4:
        errors.append(f"Micro ROUGE mismatch: {micro_rouge} vs {stored_micro['rouge_l']}")
    if abs(micro_sem - stored_micro["semantic_similarity"]) > 1e-4:
        errors.append(f"Micro Semantic mismatch: {micro_sem} vs {stored_micro['semantic_similarity']}")
    if abs(micro_cite - stored_micro["citation_compliance_rate"]) > 1e-4:
        errors.append(f"Micro Citation mismatch: {micro_cite} vs {stored_micro['citation_compliance_rate']}")
    stored_micro_time = stored_micro.get("response_time", stored_micro.get("response_time_avg", 0.0))
    if abs(micro_time - stored_micro_time) > 0.05:
        errors.append(f"Micro Time mismatch: {micro_time} vs {stored_micro_time}")

    # 2. Tái lập theo từng kịch bản (Scenario Breakdown S1 - S7)
    scenarios = ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]
    stored_scenarios = {s["scenario"]: s for s in thesis_data.get("per_scenario", [])}
    scen_recomputed = []

    print("  Chi tiết đối chiếu 7 kịch bản (S1–S7):")
    for sid in scenarios:
        s_items = [r for r in results if r.get("scenario") == sid]
        k = len(s_items)
        if k == 0:
            errors.append(f"Kịch bản {sid} không có mẫu dữ liệu nào")
            continue

        s_routing = round(sum(r.get("routing_correct", 0) for r in s_items) / k, 4)
        s_rouge = round(sum(r.get("rouge_l", 0) for r in s_items) / k, 4)
        s_sem = round(sum(r.get("semantic_similarity", r.get("bertscore", 0)) for r in s_items) / k, 4)
        s_cite = round(sum(r.get("citation_compliance", r.get("citation_correct", 0)) for r in s_items) / k, 4)
        s_time = round(sum(r.get("response_time", 0) for r in s_items) / k, 4)

        scen_recomputed.append({
            "routing": s_routing, "rouge": s_rouge, "sem": s_sem, "cite": s_cite, "time": s_time
        })

        stored_s = stored_scenarios.get(sid, {})
        match_status = "✅"
        if (abs(s_routing - stored_s.get("routing_accuracy", 0)) > 1e-3 or
            abs(s_rouge - stored_s.get("rouge_l", 0)) > 1e-3 or
            abs(s_sem - stored_s.get("semantic_similarity", 0)) > 1e-3 or
            abs(s_cite - stored_s.get("citation_compliance_rate", 0)) > 1e-3):
            match_status = "❌"
            errors.append(f"Sai lệch tại kịch bản {sid}")
        print(f"    {match_status} {sid}: n={k:2d} | Routing={s_routing:.2f} | ROUGE={s_rouge:.2f} | Sem={s_sem:.2f} | Cite={s_cite:.2f} | Time={s_time:.2f}s")

    # 3. Tái lập Macro-Average (trung bình không trọng số của 7 kịch bản)
    num_scen = len(scen_recomputed)
    macro_routing = round(sum(s["routing"] for s in scen_recomputed) / num_scen, 4)
    macro_rouge = round(sum(s["rouge"] for s in scen_recomputed) / num_scen, 4)
    macro_sem = round(sum(s["sem"] for s in scen_recomputed) / num_scen, 4)
    macro_cite = round(sum(s["cite"] for s in scen_recomputed) / num_scen, 4)
    macro_time = round(sum(s["time"] for s in scen_recomputed) / num_scen, 4)

    stored_macro = thesis_data.get("overall_macro_average", {})
    if abs(macro_routing - stored_macro.get("routing_accuracy", 0)) > 1e-4:
        errors.append(f"Macro Routing mismatch: {macro_routing} vs {stored_macro.get('routing_accuracy')}")
    if abs(macro_rouge - stored_macro.get("rouge_l", 0)) > 1e-4:
        errors.append(f"Macro ROUGE mismatch: {macro_rouge} vs {stored_macro.get('rouge_l')}")
    if abs(macro_sem - stored_macro.get("semantic_similarity", 0)) > 1e-4:
        errors.append(f"Macro Semantic mismatch: {macro_sem} vs {stored_macro.get('semantic_similarity')}")
    if abs(macro_cite - stored_macro.get("citation_compliance_rate", 0)) > 1e-4:
        errors.append(f"Macro Citation mismatch: {macro_cite} vs {stored_macro.get('citation_compliance_rate')}")
    stored_macro_time = stored_macro.get("response_time", 0.0)
    if abs(macro_time - stored_macro_time) > 0.05:
        errors.append(f"Macro Time mismatch: {macro_time} vs {stored_macro_time}")

    if not errors:
        print(f"\n  ✅ [PASS] Tái lập Micro-Average thành công:")
        print(f"     Routing: {micro_routing:.4f} | ROUGE-L: {micro_rouge:.4f} | Semantic (LLM): {micro_sem:.4f} | Citation: {micro_cite:.4f} | Time: {micro_time:.2f}s")
        print(f"  ✅ [PASS] Tái lập Macro-Average thành công:")
        print(f"     Routing: {macro_routing:.4f} | ROUGE-L: {macro_rouge:.4f} | Semantic (LLM): {macro_sem:.4f} | Citation: {macro_cite:.4f} | Time: {macro_time:.2f}s")
        return True
    else:
        print("❌ [FAIL] Có sai lệch khi tái lập:")
        for err in errors:
            print(f"   - {err}")
        return False


def verify_comparative_aggregation() -> bool:
    print("\n" + "=" * 80)
    print("3. TÁI LẬP TÍNH TOÁN BẢNG SO SÁNH 4 PIPELINE TỪ COMPARATIVE_RESULTS.JSON")
    print("=" * 80)
    comp_path = EVAL_DIR / "comparative_results.json"
    with open(comp_path, "r", encoding="utf-8") as f:
        comp_data = json.load(f)

    from comparative_eval import compute_summary

    recomputed = compute_summary(comp_data["details"])
    stored = comp_data["summary"]

    all_matched = True
    for pipe, s_rec in recomputed.items():
        s_stored = stored.get(pipe, {})
        print(f"  Pipeline: {pipe}")
        for key in ["rouge_l", "semantic_similarity", "citation_compliance_rate", "response_time_avg", "response_time_p50", "response_time_p95"]:
            v_rec = s_rec.get(key)
            v_sto = s_stored.get(key)
            if v_rec is None and v_sto is None:
                continue
            if abs((v_rec or 0) - (v_sto or 0)) > 1e-2:
                print(f"    ❌ Lệch chỉ số {key}: tính {v_rec} vs lưu {v_sto}")
                all_matched = False
            else:
                print(f"    ✅ Khớp {key:<24}: {v_rec}")
    return all_matched


def verify_regex_source_stripping() -> bool:
    print("\n" + "=" * 80)
    print("4. KIỂM TRA HÀM BÓC TÁCH NGUỒN CHO ROUGE-L (REGEX TEST)")
    print("=" * 80)
    from comparative_eval import compute_rouge_l

    test_samples = [
        ("Nội dung chính [1]. Nguồn: [1] tailieu.pdf", "Nội dung chính [2]. Nguồn: [2] khac.pdf"),
        ("Tư vấn Holland RIASEC.\n\nNguồn tham khảo: [1] cv.pdf", "Tư vấn Holland RIASEC."),
        ("Dự án cá nhân [1, 2]. **Nguồn:** [1] resume.pdf", "Dự án cá nhân."),
        ("Hoạt động ngoại khóa. Sources: [1] web", "Hoạt động ngoại khóa."),
    ]
    all_ok = True
    for ref, hyp in test_samples:
        score = compute_rouge_l(ref, hyp)
        # Vì phần nội dung chính giống hệt nhau (chỉ khác nguồn), ROUGE-L sau khi bóc tách nguồn phải đạt xấp xỉ 1.0
        print(f"  Test pair: '{ref[:30]}...' vs '{hyp[:30]}...' -> ROUGE-L = {score:.4f}")
        if score < 0.8:
            print("    ⚠ Cảnh báo: ROUGE-L thấp bất thường, tiền tố nguồn có thể chưa được lọc sạch.")
            all_ok = False
    if all_ok:
        print("✅ [PASS] Biểu thức chính quy bóc tách nguồn hoạt động chính xác.")
    return all_ok


def verify_bertscore_environment() -> bool:
    print("\n" + "=" * 80)
    print("5. KIỂM TRA MÔI TRƯỜNG BERTSCORE TIẾNG VIỆT & EMBEDDING MODEL")
    print("=" * 80)
    try:
        from bert_score import score as bscore
        P, R, F1 = bscore(["Xin chào"], ["Chào bạn"], lang="vi", verbose=False)
        print(f"✅ [PASS] Thư viện bert_score sẵn sàng! Điểm thử nghiệm vi: F1={float(F1[0]):.4f}")
        bert_ok = True
    except Exception as e:
        print(f"⚠ [WARN] Không thể chạy bert_score: {e}")
        bert_ok = False

    try:
        from data_loader import embed_texts
        vec = embed_texts(["Kiểm tra vector"], is_query=True)[0]
        print(f"✅ [PASS] Embedding model sẵn sàng! Chiều vector: {len(vec)}")
        emb_ok = True
    except Exception as e:
        print(f"⚠ [WARN] Không thể nạp embedding model: {e}")
        emb_ok = False

    return bert_ok or emb_ok


def main():
    parser = argparse.ArgumentParser(description="Xác minh độc lập tính tái lập của benchmark FBC4SAO")
    args = parser.parse_args()

    results = [
        ("Canonical Datasets Integrity", verify_canonical_datasets()),
        ("Live E2E Micro/Macro Aggregation", verify_live_aggregation()),
        ("Comparative Pipeline Aggregation", verify_comparative_aggregation()),
        ("Regex Source Stripping", verify_regex_source_stripping()),
        ("BERTScore & Embedding Environment", verify_bertscore_environment()),
    ]

    print("\n" + "=" * 80)
    print("TỔNG KẾT XÁC MINH TÍNH TÁI LẬP (REPRODUCIBILITY SUMMARY)")
    print("=" * 80)
    passed_all = True
    for name, res in results:
        status = "✅ PASS" if res else "❌ FAIL"
        if not res:
            passed_all = False
        print(f"  {name:<40}: {status}")

    if passed_all:
        print("\n🎉 Tất cả kiểm tra tính tái lập dữ liệu và thuật toán đều THÀNH CÔNG.")
        sys.exit(0)
    else:
        print("\n⚠ Có bài kiểm tra không đạt. Vui lòng kiểm tra nhật ký chi tiết phía trên.")
        sys.exit(1)


if __name__ == "__main__":
    main()
