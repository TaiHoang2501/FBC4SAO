import json

new_samples = [
    {
        "scenario": "S1",
        "scenario_type": "tricky",
        "question": "Tôi thích vẽ tranh nhưng lại muốn học kinh tế để kiếm nhiều tiền. Thế tôi nên theo nhóm nào trong Holland để sau này làm marketing?",
        "expected_agent": "test_riasec",
        "reference": "Trường hợp của bạn cho thấy sự kết hợp giữa nhóm Artistic (thích vẽ, sáng tạo) và Enterprising (kinh doanh, kiếm tiền). Mã Holland của bạn có thể là AE hoặc EA. Để làm marketing, yếu tố Enterprising và Artistic đều rất quan trọng vì ngành này cần cả sự sáng tạo lẫn tư duy kinh doanh. Bạn nên làm bài test đầy đủ để xem nhóm nào chiếm tỷ trọng cao hơn [1]."
    },
    {
        "scenario": "S1",
        "scenario_type": "tricky",
        "question": "Mọi người nói em hợp làm giáo viên vì em hay giảng bài cho bạn, nhưng em lại rất thích ở một mình code. Vậy Holland của em có bị mâu thuẫn không?",
        "expected_agent": "test_riasec",
        "reference": "Không hề mâu thuẫn. Việc thích giảng bài cho thấy bạn có đặc điểm của nhóm Social (S), trong khi sở thích code một mình thuộc về nhóm Investigative (I) hoặc Realistic (R). Mã Holland của bạn có thể là SI hoặc IS. Nhiều kỹ sư phần mềm giỏi hoặc giảng viên CNTT đều có sự kết hợp này [1]."
    },
    {
        "scenario": "S2",
        "scenario_type": "tricky",
        "question": "Em muốn tham gia ngoại khóa nhưng trường em không có câu lạc bộ nào cả, đoàn trường cũng rất ít hoạt động. Em phải làm sao để có kỹ năng nền tảng?",
        "expected_agent": "hdnk_nentang",
        "reference": "Nếu trường không có sẵn CLB, bạn có thể tự tạo cơ hội bằng cách: tham gia các dự án tình nguyện online, tham gia các tổ chức phi chính phủ (NGO) tuyển tình nguyện viên từ xa, tự lập một nhóm học tập nhỏ, hoặc tham gia các khóa học kỹ năng mềm trực tuyến. Kỹ năng nền tảng không nhất thiết phải đến từ CLB của trường [1][2]."
    },
    {
        "scenario": "S2",
        "scenario_type": "tricky",
        "question": "Tham gia đội tuyển học sinh giỏi Toán có được tính là ngoại khóa nền tảng không ạ?",
        "expected_agent": "hdnk_nentang",
        "reference": "Đội tuyển học sinh giỏi thiên về thành tích học thuật hơn là ngoại khóa nền tảng (vốn tập trung vào kỹ năng mềm như giao tiếp, làm việc nhóm). Tuy nhiên, quá trình học nhóm trong đội tuyển vẫn giúp bạn rèn tư duy logic và sự kiên nhẫn. Để hồ sơ toàn diện hơn, bạn nên bổ sung thêm các hoạt động mang tính cộng đồng hoặc xã hội [1][2]."
    },
    {
        "scenario": "S3",
        "scenario_type": "tricky",
        "question": "Em định xin thực tập ở một công ty IT nhưng em mới học lớp 11, họ không nhận. Có cách nào khác để làm ngoại khóa chuyên sâu CNTT không?",
        "expected_agent": "hdnk_chuyenmon",
        "reference": "Nếu chưa xin được thực tập, bạn có thể làm ngoại khóa chuyên sâu bằng cách: đóng góp mã nguồn cho các dự án Open Source trên GitHub, tự xây dựng một ứng dụng/website nhỏ và publish lên mạng, hoặc tham gia các kỳ thi lập trình (hackathon) dành cho học sinh. Các dự án cá nhân này đôi khi còn được đánh giá cao hơn cả thực tập [1][2]."
    },
    {
        "scenario": "S3",
        "scenario_type": "tricky",
        "question": "Viết báo khoa học nhưng không được đăng báo quốc tế thì có tính là ngoại khóa chuyên môn xịn không?",
        "expected_agent": "hdnk_chuyenmon",
        "reference": "Vẫn được tính là ngoại khóa chuyên môn rất giá trị. Dù không được đăng quốc tế, quá trình nghiên cứu khoa học cho thấy bạn có tư duy phân tích, khả năng đọc hiểu tài liệu và tinh thần học hỏi sâu. Bạn có thể tóm tắt nghiên cứu đó vào portfolio hoặc đăng trên các nền tảng chia sẻ học thuật [1][2]."
    },
    {
        "scenario": "S4",
        "scenario_type": "tricky",
        "question": "Em rất thích chơi game online. Làm sao để ghi cái này vào hồ sơ ngoại khóa cá nhân mà không bị đánh giá xấu?",
        "expected_agent": "hdnk_canhan",
        "reference": "Bạn có thể biến sở thích chơi game thành điểm nhấn nếu thể hiện được kỹ năng: ví dụ bạn từng tổ chức hoặc quản lý một team/clan lớn (thể hiện kỹ năng lãnh đạo), tự build cấu hình máy tính (kỹ năng kỹ thuật), hoặc viết blog/review phân tích chiến thuật game (tư duy phân tích). Quan trọng là bạn học được gì từ quá trình đó [1][2]."
    },
    {
        "scenario": "S4",
        "scenario_type": "tricky",
        "question": "Sở thích cá nhân của em là nấu ăn cho gia đình. Điều này có ý nghĩa gì cho hồ sơ du học ngành kỹ thuật không?",
        "expected_agent": "hdnk_canhan",
        "reference": "Nấu ăn có vẻ không liên quan đến kỹ thuật, nhưng nó thể hiện bạn là một người cân bằng, biết chăm sóc bản thân và gia đình. Trong ngành kỹ thuật căng thẳng, những sở thích giúp giải tỏa áp lực và duy trì sức khỏe tinh thần rất được trân trọng. Nó cho thấy bạn có đời sống tinh thần phong phú [1][2]."
    },
    {
        "scenario": "S5",
        "scenario_type": "tricky",
        "question": "Hồ sơ của em y hệt một anh chị đã đậu thủ khoa, liệu em có chắc chắn đậu không?",
        "expected_agent": "match_hoso",
        "reference": "Không có gì là chắc chắn. Tuy hồ sơ của bạn tương đồng với một sinh viên thành công, hội đồng tuyển sinh còn đánh giá qua cách bạn viết bài luận cá nhân, vòng phỏng vấn và sự phù hợp với văn hóa trường ở thời điểm hiện tại. Hồ sơ tương đồng chỉ là một hệ quy chiếu giúp bạn tự tin hơn về định hướng, chứ không phải giấy báo trúng tuyển [1][2]."
    },
    {
        "scenario": "S5",
        "scenario_type": "tricky",
        "question": "Có hồ sơ nào của người hướng nội mà lại thành công trong ngành sale/marketing không?",
        "expected_agent": "match_hoso",
        "reference": "Có rất nhiều. Người hướng nội (như nhóm Investigative hoặc Artistic) trong ngành marketing thường thành công nhờ tư duy phân tích dữ liệu sâu sắc, khả năng sáng tạo nội dung xuất sắc và thấu hiểu tâm lý khách hàng thay vì giao tiếp ồn ào. Trong cơ sở dữ liệu có những sinh viên tương tự đã dùng thế mạnh lắng nghe để chốt sale hiệu quả [1][2][3]."
    },
    {
        "scenario": "S6",
        "scenario_type": "tricky",
        "question": "Mã Holland của em là Social, thích làm tình nguyện, nhưng gia đình ép học y. Em nên xây dựng lộ trình ngoại khóa thế nào để vừa ý bố mẹ vừa đúng đam mê?",
        "expected_agent": "danhgia_all",
        "reference": "Bạn có thể dung hòa cả hai bằng cách kết hợp nhóm Social và ngành Y: tham gia các dự án y tế cộng đồng, chiến dịch hiến máu, hoặc làm tình nguyện viên tại các trạm xá/bệnh viện. Lộ trình này vừa giúp bạn thỏa mãn đam mê đóng góp cho xã hội, vừa xây dựng được một hồ sơ y khoa giàu lòng nhân ái - điều kiện cực kỳ quan trọng cho ngành y [1][2]."
    },
    {
        "scenario": "S6",
        "scenario_type": "tricky",
        "question": "Đánh giá giúp hồ sơ của em: Điểm SAT 1550, GPA 9.8 nhưng ngoại khóa chỉ có 1 hoạt động duy nhất là đánh đàn piano ở nhà.",
        "expected_agent": "danhgia_all",
        "reference": "Hồ sơ của bạn có điểm nhấn học thuật rất mạnh (Investigative/Conventional) nhưng đang thiếu hụt trầm trọng kỹ năng mềm và khả năng làm việc cộng đồng (Social). Với chỉ một hoạt động piano ở nhà, bạn sẽ gặp khó khăn khi cạnh tranh vào các trường đại học hàng đầu đề cao sự toàn diện. Cần ngay lập tức bổ sung các hoạt động ngoại khóa nền tảng như dự án cộng đồng hoặc CLB [1][2]."
    },
    {
        "scenario": "S7",
        "scenario_type": "tricky",
        "question": "Trắc nghiệm Holland có bao giờ bị sai không? Cảm giác kết quả không giống em lắm.",
        "expected_agent": "hoidapchung",
        "reference": "Trắc nghiệm Holland là công cụ tâm lý học nên vẫn có thể có độ lệch, nhất là khi tâm trạng bạn không ổn định lúc làm bài hoặc bạn chưa hiểu rõ bản thân. Nếu thấy kết quả không đúng, bạn nên xem xét lại các hoạt động thực tế mình từng làm, kết hợp tham vấn chuyên gia hướng nghiệp để có góc nhìn khách quan hơn [1]."
    },
    {
        "scenario": "S7",
        "scenario_type": "tricky",
        "question": "Em có thể dùng bài kiểm tra MBTI thay cho Holland khi dùng hệ thống này được không?",
        "expected_agent": "hoidapchung",
        "reference": "Hệ thống này được thiết kế chuyên biệt dựa trên lý thuyết Holland RIASEC, vốn tập trung vào sở thích và môi trường nghề nghiệp. MBTI tập trung vào xu hướng tính cách. Bạn không thể thay thế trực tiếp, nhưng có thể dùng MBTI như một nguồn tham khảo bổ trợ để hiểu sâu hơn về bản thân. Tuy nhiên, hệ thống tư vấn ngoại khóa sẽ chỉ dùng mã Holland để gợi ý [1]."
    }
]

def run():
    with open('ground_truth.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data.extend(new_samples)
    
    with open('ground_truth.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Added {len(new_samples)} tricky questions. Total samples: {len(data)}.")

if __name__ == '__main__':
    run()
