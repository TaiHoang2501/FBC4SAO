import json

data = []

def add_samples(scenario, agent, q_type, questions, ref_text):
    for q in questions:
        data.append({
            "scenario": scenario,
            "scenario_type": q_type,
            "question": q,
            "expected_agent": agent,
            "reference": ref_text
        })

# S1: Chẩn đoán Holland/RIASEC (14 samples)
s1_ref = "Dựa trên sở thích và tính cách của bạn, hệ thống chẩn đoán bạn có thể thuộc các nhóm trong Holland RIASEC. Realistic (R) thích máy móc, thực hành. Investigative (I) thích nghiên cứu, logic. Artistic (A) thích sáng tạo. Social (S) thích giúp đỡ, giảng dạy. Enterprising (E) thích kinh doanh, lãnh đạo. Conventional (C) thích tính toán, có tổ chức. Hãy hoàn thành bài kiểm tra để có mã chính xác [1]."
add_samples("S1", "test_riasec", "standard", [
    "Em hay thích tháo lắp máy móc và làm thủ công. Em thuộc nhóm Holland nào?",
    "Mình rất thích vẽ tranh và thiết kế đồ họa. Nhóm Holland của mình là gì?",
    "Cho em hỏi nếu em thích giao tiếp và giúp đỡ người khác thì em thuộc nhóm nào?",
    "Tôi là người ngăn nắp, thích làm việc với các con số và sổ sách. Tôi nhóm nào trong RIASEC?",
    "Em có sở thích làm trưởng nhóm và thuyết phục người khác. Xin tư vấn nhóm Holland.",
    "Tôi luôn tò mò, thích giải các bài toán khó và nghiên cứu khoa học. Tính cách này là gì?",
    "Đam mê sửa chữa xe cộ và máy tính thì thuộc nhóm tính cách nào ạ?",
    "Em thích sáng tác nhạc và viết lách, em hợp với chữ cái nào trong RIASEC?"
], s1_ref)
add_samples("S1", "test_riasec", "variant", [
    "Tính cách tôi: thích giải quyết vấn đề thực tế, không thích nói nhiều, làm tốt hơn nói. RIASEC là gì?",
    "Em không biết mình thích gì, nhưng không ghét môn nào cả. Làm sao xác định Holland?",
    "Bạn bè bảo tôi vừa thích kinh doanh (E) vừa thích vẽ (A). Có mã EA không?",
    "Mình rất hướng nội, chỉ thích ôm máy tính gõ code từ sáng đến tối. Mình thuộc Holland nào?",
    "Em ghét các con số, chỉ thích tự do bay nhảy và làm MC sự kiện. Tư vấn giúp em.",
    "Bố mẹ bảo em làm kế toán nhưng em thích đi làm tình nguyện vùng sâu vùng xa hơn."
], s1_ref)

# S2: Tư vấn Ngoại khóa Nền tảng (14 samples)
s2_ref = "Dựa trên nhóm tính cách của bạn, bạn có thể tham gia các hoạt động ngoại khóa nền tảng như: gia nhập các câu lạc bộ (CLB) sở thích tại trường, tham gia tình nguyện viên ngắn hạn, hoặc hỗ trợ sự kiện. Những hoạt động này không yêu cầu chuyên môn cao nhưng giúp xây dựng kỹ năng mềm, giao tiếp và làm việc nhóm [1][2]."
add_samples("S2", "hdnk_nentang", "standard", [
    "Em mã Holland là Social (S). Nên tham gia ngoại khóa nền tảng nào để phát triển kỹ năng mềm?",
    "Mình thuộc nhóm R. Có hoạt động nền tảng nào phù hợp cho người thích thực hành không?",
    "Nhóm Conventional thì nên tham gia các CLB nào ở trường cấp 3?",
    "Cho em hỏi làm sao để tìm các hoạt động tình nguyện cơ bản cho học sinh lớp 10?",
    "Em mới lên cấp 3, muốn cải thiện kỹ năng giao tiếp thì nên làm gì?",
    "Nhóm Artistic có nên tham gia CLB truyền thông của trường không?",
    "Ngoại khóa nền tảng là gì? Nó khác gì với ngoại khóa chuyên sâu?",
    "Em có thời gian rảnh cuối tuần, có dự án nền tảng nào phù hợp cho nhóm Enterprising?"
], s2_ref)
add_samples("S2", "hdnk_nentang", "variant", [
    "Tôi hướng nội, thuộc nhóm Investigative. Hoạt động ngoại khóa nào giúp tôi xây nền tảng mà không phải nói trước đám đông?",
    "Em bận học, không có thời gian. Hoạt động ngoại khóa nền tảng nào ngắn nhất?",
    "Trường em ở quê không có CLB nào cả, em làm sao để có ngoại khóa nền tảng?",
    "Làm lớp trưởng có được coi là một hoạt động ngoại khóa nền tảng tốt không?",
    "Tham gia đội tuyển học sinh giỏi có tính là ngoại khóa nền tảng không ạ?",
    "Em chỉ thích tham gia mấy buổi workshop 1 ngày, như vậy có đủ ghi vào CV chưa?"
], s2_ref)

# S3: Tư vấn Ngoại khóa Chuyên sâu (14 samples)
s3_ref = "Với nhu cầu làm đẹp hồ sơ học thuật và chuyên môn, bạn nên tham gia các hoạt động ngoại khóa chuyên sâu. Điều này bao gồm: thực tập tại các công ty, tham gia nghiên cứu khoa học với giảng viên, tham gia các kỳ thi hackathon hoặc giải quyết tình huống kinh doanh, và công bố báo cáo khoa học. Các hoạt động này minh chứng rõ ràng năng lực nghề nghiệp của bạn [1][2]."
add_samples("S3", "hdnk_chuyenmon", "standard", [
    "Em muốn làm hồ sơ chuyên môn về AI. Ngoại khóa chuyên sâu nào phù hợp?",
    "Ngành Tài chính Kế toán thì nên có ngoại khóa chuyên môn gì?",
    "Làm sao để xin tham gia nghiên cứu khoa học cùng thầy cô đại học?",
    "Em nhóm Artistic, muốn làm Portfolio thiết kế chuyên nghiệp thì bắt đầu từ đâu?",
    "Nhóm Enterprising nên thi các giải Case Study kinh doanh nào để đẹp hồ sơ?",
    "Tư vấn cho em các hoạt động chuyên sâu dành cho ngành Tâm lý học.",
    "Cần chuẩn bị những gì để xin thực tập ở công ty công nghệ khi mới năm nhất?",
    "Em muốn có chứng chỉ chuyên môn về phân tích dữ liệu, hệ thống gợi ý cho em khóa học được không?"
], s3_ref)
add_samples("S3", "hdnk_chuyenmon", "variant", [
    "Nhóm Enterprising (E) có thể làm startup hoặc dự án kinh doanh nào để đẹp hồ sơ chuyên môn?",
    "Em ở tỉnh, không có cơ hội thực tập ở công ty lớn. Có cách nào làm ngoại khóa chuyên môn không?",
    "Viết báo khoa học mà chỉ đăng tạp chí trong nước thì có được đánh giá cao khi du học không?",
    "Em mới lớp 11 thì làm sao để các công ty đồng ý cho thực tập chuyên sâu?",
    "Tự học code ở nhà và up lên Github có tính là ngoại khóa chuyên sâu không?",
    "Làm Freelance thiết kế logo cho khách hàng có đưa vào CV xin việc được không?"
], s3_ref)

# S4: Hoạt động Cá nhân (14 samples)
s4_ref = "Hoạt động cá nhân là những sở thích đặc biệt giúp hồ sơ của bạn trở nên độc đáo và đậm chất con người. Bạn có thể phát triển các sở thích như nghệ thuật, âm nhạc, thể thao, hoặc viết blog cá nhân. Dù không trực tiếp liên quan đến học thuật, chúng thể hiện sự kiên trì, tính kỷ luật và khả năng tự cân bằng cuộc sống của bạn [1][2]."
add_samples("S4", "hdnk_canhan", "standard", [
    "Em thích âm nhạc và nghệ thuật. Làm sao biến sở thích cá nhân thành điểm nhấn hồ sơ?",
    "Chơi thể thao (bóng rổ) có giúp ích gì cho hồ sơ xin học bổng không?",
    "Em thích viết blog truyện ngắn, hoạt động này có ý nghĩa gì không?",
    "Đam mê chụp ảnh phong cảnh thì nên thể hiện vào hồ sơ như thế nào?",
    "Làm kênh Youtube chia sẻ cách học bài có phải là hoạt động cá nhân tốt không?",
    "Em có đai đen Taekwondo, có nên đưa vào CV xin việc ngành IT không?",
    "Sở thích làm bánh và nấu ăn có giúp gì cho nhóm Holland Social không?",
    "Cho em hỏi làm sao để chứng minh sở thích tự học ngoại ngữ của mình trên hồ sơ?"
], s4_ref)
add_samples("S4", "hdnk_canhan", "variant", [
    "Em chơi cờ vua từ nhỏ. Cờ vua có được tính là ngoại khóa cá nhân giá trị không?",
    "Em không có sở thích đặc biệt gì. Mọi người bảo cần có hoạt động cá nhân thì phải làm sao?",
    "Ghi sở thích 'chơi game online' vào hồ sơ có bị giám khảo đánh giá là thiếu nghiêm túc không?",
    "Em chỉ thích đọc truyện tranh Manga và Anime, có cách nào biến nó thành thế mạnh hồ sơ?",
    "Em bị cận nặng không chơi thể thao được, em có thể làm hoạt động cá nhân gì thay thế?",
    "Việc em tự học trang điểm (makeup) có phải là hoạt động cá nhân của nhóm Artistic?"
], s4_ref)

# S5: Đối chiếu Hồ sơ (14 samples)
s5_ref = "Hệ thống đã đối chiếu yêu cầu của bạn với cơ sở dữ liệu hồ sơ sinh viên thành công. Những sinh viên có mã Holland tương tự thường có lộ trình học thuật vững vàng, tham gia nghiên cứu và thực tập từ sớm. Bạn có thể tham khảo lộ trình của họ làm tài liệu tham khảo để định hướng cho bản thân, tuy nhiên vẫn cần tùy chỉnh theo hoàn cảnh cá nhân [1][2][3]."
add_samples("S5", "match_hoso", "standard", [
    "Em mã Holland là IA, muốn học ngành Khoa học máy tính. Có anh chị nào tương tự không?",
    "Tìm giúp em hồ sơ của một bạn nhóm E trúng tuyển ngành Quản trị Kinh doanh.",
    "Hệ thống có mẫu CV nào của sinh viên nhóm S làm về Truyền thông không?",
    "Cho em xem lộ trình của một bạn có nhóm tính cách R thi đỗ kỹ sư cơ khí.",
    "Em muốn đối chiếu hồ sơ của em với các cựu học sinh đã đỗ Đại học Ngoại thương.",
    "Có anh chị nào thuộc nhóm Artistic mà thành công trong ngành Thiết kế đồ họa không?",
    "Cho tôi xem hồ sơ của một bạn học khối tự nhiên nhưng lại thành công ở ngành xã hội.",
    "So sánh giúp em hồ sơ của em với một sinh viên đã đạt học bổng toàn phần."
], s5_ref)
add_samples("S5", "match_hoso", "variant", [
    "Cho tôi xem hồ sơ của những bạn xuất phát điểm bình thường nhưng sau vẫn trúng tuyển đại học tốt.",
    "Em muốn tìm hồ sơ anh chị nhóm Conventional (C) học ngành Kế toán, có không?",
    "Hồ sơ của em giống hệt thủ khoa năm ngoái, liệu em có 100% trúng tuyển không?",
    "Có ai hướng nội tột cùng (nhóm I) mà lại làm Giám đốc Sales thành công không, cho em xem CV với.",
    "Em mới chỉ có mỗi giải Ba thành phố, hệ thống có ai điểm thấp như em mà đỗ du học không?",
    "Cho em xin danh sách các hoạt động ngoại khóa mà các anh chị đậu Havard đã làm."
], s5_ref)

# S6: Đánh giá Toàn diện (14 samples)
s6_ref = "Đánh giá toàn diện: Dựa trên thông tin hồ sơ bạn cung cấp, hệ thống xác định bạn có thiên hướng rõ rệt về một số nhóm Holland nhất định. Tuy nhiên, hồ sơ của bạn có thể đang thiếu sự cân bằng giữa ngoại khóa nền tảng, chuyên môn và cá nhân. Lộ trình gợi ý: Bước 1 - Củng cố nền tảng qua các CLB xã hội. Bước 2 - Đẩy mạnh chuyên môn bằng dự án thực tế. Bước 3 - Duy trì sở thích cá nhân để tạo sự khác biệt [1][2]."
add_samples("S6", "danhgia_all", "standard", [
    "Em tên Minh, thích toán và lập trình, ghét giao tiếp đám đông. Phân tích hồ sơ và lộ trình ngoại khóa cho em.",
    "CV em: Trưởng CLB Thiện nguyện, MC sự kiện trường, điểm Văn cao. Mã Holland và lộ trình ngoại khóa phù hợp?",
    "Em là học sinh chuyên Lý, GPA 9.5, chưa có ngoại khóa. Hãy đánh giá toàn diện giúp em.",
    "Nhờ hệ thống đánh giá xem hồ sơ của em (đã có IELTS 7.5 và tham gia trại hè) đã đủ mạnh để nộp du học chưa.",
    "Phân tích điểm mạnh điểm yếu trong lộ trình của em: Em thuộc nhóm E, đã làm phó chủ tịch CLB kinh doanh.",
    "Hãy tổng hợp và đưa ra lời khuyên toàn diện cho một bạn nhóm IA đang muốn chuyển hướng sang kinh tế.",
    "Đánh giá tổng quan về năng lực của em nếu em chọn thi vào ngành Luật, em thuộc nhóm Social.",
    "Xây dựng lộ trình 3 năm cấp 3 cho một bạn mới vào lớp 10 có mã Holland là RC."
], s6_ref)
add_samples("S6", "danhgia_all", "variant", [
    "Em chưa làm gì cả, học lớp 10, chưa biết mình thích gì. Vẫn cần đánh giá toàn diện không?",
    "Đánh giá giúp hồ sơ của em: Điểm SAT 1550, GPA 9.8 nhưng ngoại khóa chỉ có 1 hoạt động duy nhất là đánh đàn piano ở nhà.",
    "Em học lệch Toán, dốt Văn, giao tiếp kém nhưng lại muốn mở công ty riêng. Hệ thống đánh giá sao về trường hợp này?",
    "Em bị mâu thuẫn giữa việc gia đình bắt học Y nhưng bản thân muốn làm nghệ thuật. Xin phân tích toàn diện.",
    "Có phải cứ có đủ 3 loại ngoại khóa (nền tảng, chuyên môn, cá nhân) là chắc chắn hồ sơ hoàn hảo không?",
    "Em viết luận rất giỏi nhưng CV trắng trơn. Hãy cho em một chiến lược toàn diện để vượt qua điểm yếu này."
], s6_ref)

# S7: Hỏi đáp Tổng quát & Out-of-scope (16 samples)
s7_ref = "Hệ thống RAG Tư vấn Hướng nghiệp cung cấp các thông tin tổng quát về lý thuyết Holland RIASEC, ý nghĩa của các bài trắc nghiệm tính cách, và cách sử dụng nền tảng để xây dựng lộ trình ngoại khóa. Xin lưu ý hệ thống chỉ trả lời các vấn đề liên quan đến hướng nghiệp, hồ sơ năng lực và ngoại khóa [1]."
add_samples("S7", "hoidapchung", "standard", [
    "Mã Holland là gì? Giải thích ngắn gọn.",
    "Hệ thống này tư vấn được những gì cho học sinh?",
    "Làm sao để sử dụng ứng dụng này một cách hiệu quả nhất?",
    "Hệ thống Holland RIASEC ra đời từ năm nào và độ tin cậy ra sao?",
    "Trắc nghiệm Holland có giống với trắc nghiệm MBTI không?",
    "Các kết quả tư vấn của bot có dựa trên tài liệu khoa học nào không?",
    "Làm thế nào để phân biệt giữa ngoại khóa chuyên sâu và ngoại khóa nền tảng?",
    "Tôi có thể lưu lại kết quả bài test trên hệ thống này được không?"
], s7_ref)
add_samples("S7", "hoidapchung", "variant", [ # Tricky/Out-of-scope
    "Bạn có thể nói chuyện bằng tiếng Anh không?",
    "Hôm nay thời tiết thế nào, có nên đi thi đại học không?",
    "Bạn có thể viết giúp tôi một đoạn code Python để tự động crawl dữ liệu được không?",
    "Trắc nghiệm Holland có bao giờ bị sai không? Cảm giác kết quả không giống em lắm.",
    "Hệ thống có giải được đề thi Toán đại học không?",
    "Cho mình xin công thức nấu món phở bò Nam Định.",
    "Bạn là ai? Ai là người tạo ra bạn?",
    "Tư vấn cho tôi cách kiếm 1 tỷ đầu tiên trước tuổi 20 mà không cần bằng đại học."
], s7_ref)

with open('ground_truth_final.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Generated ground_truth_final.json with {len(data)} questions.")
