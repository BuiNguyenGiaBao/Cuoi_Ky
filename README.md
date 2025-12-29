
# Cuoi_Ky — TikTok Data Collection & Analysis

Dự án cuối kỳ môn **Mã nguồn mở trong Khoa học Dữ liệu**.  
Mục tiêu là thu thập, lưu trữ và phân tích dữ liệu từ nền tảng TikTok phục vụ nghiên cứu hành vi người dùng.

---

## 1. Mục tiêu
- Thu thập dữ liệu video và bình luận từ TikTok bằng Selenium.
- Lưu trữ dữ liệu có cấu trúc bằng MongoDB.
- Phân tích dữ liệu nhằm rút ra đặc điểm và xu hướng hành vi người dùng.

---

## 2. Cấu trúc thư mục
```

Cuoi_Ky/
├── scraper/              # Mã thu thập dữ liệu bằng Selenium
├── Mongo/                # Script xử lý và phân tích dữ liệu
├── data/                 # Dữ liệu thu thập (CSV / JSON)
├── requirements.txt      # Danh sách thư viện
└── README.md

````

---

## 3. Yêu cầu hệ thống
- Python 3.9+
- Google Chrome
- ChromeDriver (phiên bản tương thích)
- MongoDB (local hoặc cloud)

---

## 4. Cài đặt môi trường
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
````

---

## 5. Thu thập dữ liệu

Chạy script thu thập dữ liệu trong thư mục `scraper`:

```bash
python scraper/main.py
```

Dữ liệu thu được sẽ được lưu dưới dạng CSV hoặc JSON trong thư mục `data/` hoặc đưa trực tiếp vào MongoDB.

---

## 6. Phân tích dữ liệu

Chạy các script trong thư mục `Mongo/` để:

* Thống kê số lượng video, bình luận
* Phân tích độ dài bình luận
* Phân tích mối quan hệ giữa lượt thích và bình luận

---

## 7. Tác giả

* Bùi Nguyễn Gia Bảo
* Tăng Phước Bảo


