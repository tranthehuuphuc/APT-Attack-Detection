# Nghiên cứu Giải pháp Phát hiện Tấn công APT thông qua Phân tích Đồ thị Nguồn gốc và Tri thức TTP

**Tác giả:** Trần Thế Hữu Phúc - Hà Minh Quân  
**Giảng viên hướng dẫn:** TS. Phan Thế Duy  
**Trường:** Đại học Công nghệ Thông tin - ĐHQG TP.HCM  
**Khoa:** Mạng máy tính và Truyền thông

---

## 📌 Giới thiệu

Đồ án này tập trung vào việc xây dựng một hệ thống săn lùng và phát hiện các mối đe dọa dai dẳng (APT) bằng cách áp dụng các kỹ thuật học sâu tiên tiến trên Đồ thị Nguồn gốc (Provenance Graph). Cốt lõi của dự án là sự chuyển dịch từ mô hình phát hiện dựa trên các Chỉ số Tấn công (IOC) tĩnh sang mô hình phát hiện dựa trên **hành vi và cấu trúc của chuỗi tấn công**, được mô tả bởi các Kỹ thuật, Chiến thuật và Quy trình (TTP) theo framework MITRE ATT&CK.

Hệ thống được xây dựng dựa trên phương pháp luận của bài báo khoa học **MEGR-APT**, kết hợp với một module cải tiến sử dụng **Mô hình Ngôn ngữ Lớn (LLM)** để tự động hóa việc trích xuất tri thức từ các báo cáo tình báo về mối đe dọa (CTI).

## 🎯 Mục tiêu chính

- **Xây dựng Đồ thị Nguồn gốc:** Tự động hóa việc xử lý và tổng hợp một khối lượng lớn log hệ thống (định dạng CDM) thành một bộ dữ liệu đồ thị duy nhất và toàn vẹn.
- **Làm giàu Ngữ nghĩa:** Thiết kế và triển khai một hệ thống gán nhãn TTP tự động dựa trên luật cho các thực thể và sự kiện trong đồ thị.
- **Tự động hóa Xây dựng Tri thức:** Xây dựng một pipeline sử dụng LLM để tự động đọc các báo cáo CTI và trích xuất ra các Đồ thị Truy vấn Tấn công (Attack Query Graphs).
- **Huấn luyện Mô hình So khớp Đồ thị:** Huấn luyện một mô hình GNN (cụ thể là RGCN) có khả năng so sánh độ tương đồng về mặt cấu trúc giữa hai đồ thị bất kỳ, dựa trên khái niệm Khoảng cách Chỉnh sửa Đồ thị (GED).
- **Xây dựng Quy trình Săn lùng:** Triển khai một pipeline săn lùng hoàn chỉnh, sử dụng mô hình đã huấn luyện để so khớp các đồ thị con đáng ngờ với các đồ thị tấn công đã biết.

## 🏗️ Kiến trúc Hệ thống

Hệ thống được thiết kế theo một luồng xử lý gồm hai giai đoạn chính, hoạt động độc lập: **Giai đoạn Huấn luyện (Offline)** và **Giai đoạn Săn lùng (Online)**.

![Kiến trúc Hệ thống](images/System-Structure.png)

### Giai đoạn 1: Huấn luyện Mô hình
Đây là một quy trình offline, được thực hiện một lần để xây dựng "bộ não" cho hệ thống.
1.  **Xử lý Log:** Log CDM được xử lý để tạo ra các file `nodes.csv` và `edges.csv`.
2.  **Gán nhãn TTP:** Các node và edge được làm giàu bằng các nhãn TTP.
3.  **Trích xuất Subgraph Lành tính:** Hàng nghìn đồ thị con lành tính được tạo ra bằng phương pháp Đi bộ Ngẫu nhiên lưỡng hướng.
4.  **Chuẩn bị Dữ liệu Huấn luyện:** Các cặp đồ thị lành tính được tạo ra và Khoảng cách Chỉnh sửa Đồ thị (GED) giữa chúng được tính toán để làm nhãn "chân lý".
5.  **Huấn luyện:** Mô hình GNN được huấn luyện để học cách xấp xỉ giá trị GED này.

### Giai đoạn 2: Săn lùng Mối đe dọa
Đây là quy trình vận hành, sử dụng mô hình đã được huấn luyện.
1.  **Xây dựng Query Graph:** Một báo cáo CTI được đưa vào module LLM để tự động tạo ra một Đồ thị Truy vấn Tấn công.
2.  **Xác định Hạt giống (Seeds):** Hệ thống tìm kiếm các node/edge trong đồ thị nguồn gốc khớp với TTP khởi nguồn của Query Graph.
3.  **Trích xuất Ngữ cảnh:** Một đồ thị con ứng viên được trích xuất xung quanh mỗi "hạt giống" bằng phương pháp k-hop sampling.
4.  **So khớp & Chấm điểm:** Mô hình GNN tính toán điểm tương đồng giữa đồ thị con và đồ thị truy vấn.
5.  **Cảnh báo:** Nếu điểm tương đồng vượt ngưỡng, một cảnh báo sẽ được tạo ra.


## 📚 Tài liệu tham khảo chính
Aly, Ahmed, et al. "MEGR-APT: A Memory-Efficient APT Hunting System Based on Attack Representation Learning." *IEEE Transactions on Information Forensics and Security*, 2024.

---
*Đồ án Chuyên ngành, Khoa Mạng Máy tính và Truyền thông, Trường Đại học Công nghệ Thông tin - ĐHQG TP.HCM.*
