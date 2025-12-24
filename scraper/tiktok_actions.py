import undetected_chromedriver as uc
import time
import random
import csv
import os
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ================= CẤU HÌNH =================
TARGET_PROFILE = "https://www.tiktok.com/explore"
LIMIT_VIDEOS = 200
MAX_COMMENTS_PER_VIDEO = 500

VIDEO_FILE = "tiktok_videos_data.csv"
COMMENT_FILE = "tiktok_comments_data.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# ================= KHỞI TẠO BẢO MẬT =================
def setup_driver():
    options = uc.ChromeOptions()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(script_dir, "tiktok_session")
    
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
        
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--mute-audio")

    driver = uc.Chrome(options=options)
    return driver

def solve_captcha(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "captcha_verify_container"))
        )
        logger.warning("⚠️ CAPTCHA phát hiện – vui lòng giải tay")
        WebDriverWait(driver, 300).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "captcha_verify_container"))
        )
        logger.info("✅ CAPTCHA đã giải")
    except:
        pass

def save_to_csv(filename, data_list):
    if not data_list: return
    exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=data_list[0].keys())
        if not exists: writer.writeheader()
        writer.writerows(data_list)
    logger.info(f"💾 Đã lưu vào {filename}")

# ================= LẤY DANH SÁCH VIDEO =================
def get_video_links(driver, url, limit):
    logger.info(f"🌍 Truy cập: {url}")
    driver.get(url)
    time.sleep(5)

    links = set()
    while len(links) < limit:
        elems = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/video/"]')
        for e in elems:
            href = e.get_attribute("href")
            if href: links.add(href)
        
        if len(links) >= limit: break
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Kiểm tra nếu hết video
        if driver.find_elements(By.CSS_SELECTOR, '[data-e2e="user-post-item-no-content"]'):
            break
            
    return list(links)[:limit]

# ================= LẤY THÔNG TIN VIDEO =================
def get_video_info(driver, url):
    driver.get(url)
    time.sleep(4)
    solve_captcha(driver)

    video_id = url.split("/video/")[-1].split("?")[0]

    data = {
        "video_url": url,
        "video_id": video_id,
        "caption": "",
        "like_count": "",
        "comment_count": "",
        "share_count": "",
    }

    try:
        caption = driver.find_element(By.CSS_SELECTOR, '[data-e2e="video-desc"]')
        data["caption"] = caption.text
    except:
        pass

    buttons = driver.find_elements(By.TAG_NAME, "button")
    for b in buttons:
        aria = (b.get_attribute("aria-label") or "").lower()
        num = "".join(filter(str.isdigit, aria))

        if "like" in aria or "thích" in aria:
            data["like_count"] = num
        if "comment" in aria or "bình luận" in aria:
            data["comment_count"] = num
        if "share" in aria or "chia sẻ" in aria:
            data["share_count"] = num

    logger.info(
        f"🎬 {video_id} | ❤️ {data['like_count']} | 💬 {data['comment_count']}"
    )
    return data

def get_cookie_dict(driver):
    cookies = driver.get_cookies()
    return {c["name"]: c["value"] for c in cookies}

def scroll_get_video_links(driver, limit):
    driver.get(TARGET_PROFILE)
    time.sleep(5)
    solve_captcha(driver)

    links = set()

    while len(links) < limit:
        driver.execute_script("window.scrollBy(0, 800)")
        time.sleep(random.uniform(2, 3))

        elems = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/video/"]')
        for e in elems:
            href = e.get_attribute("href")
            if href and "/video/" in href:
                links.add(href)

        logger.info(f"📹 Đã lấy {len(links)}/{limit} video")

        if len(links) >= limit:
            break

    return list(links)[:limit]


# ================= LẤY COMMENT (CÓ CLICK MỞ) =================
def get_comments(driver, video_id, max_cmt):
    comments_data = []
    logger.info("⬇️ Đang quét comment...")

    # --- BƯỚC 1: CLICK MỞ BẢNG COMMENT NẾU ĐANG ĐÓNG ---
    try:
        wait = WebDriverWait(driver, 5)
        comment_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-e2e="comment-icon"]')))
        driver.execute_script("arguments[0].click();", comment_btn)
        logger.info("✅ Đã click mở bảng comment.")
        time.sleep(2)
    except:
        logger.info("ℹ️ Bảng comment có vẻ đã mở sẵn.")

    collected_texts = set()
    retries = 0
    
    while len(comments_data) < max_cmt and retries < 10:
        # Tìm item comment level 1
        items = driver.find_elements(By.CSS_SELECTOR, '[data-e2e="comment-level-1"]')
        
        if not items:
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(3)
            retries += 1
            continue

        new_found = False
        for item in items:
            try:
                text = item.text.strip()
                if not text or text in collected_texts: continue
                
                # Tìm User bằng XPath tương đối
                try:
                    user_elem = item.find_element(By.XPATH, "./ancestor::div[contains(@class,'DivContentContainer')]//a[contains(@href, '/@')]")
                    user = user_elem.get_attribute("href").split("/@")[-1].split("?")[0]
                except:
                    user = "unknown"

                collected_texts.add(text)
                comments_data.append({
                    "video_id": video_id,
                    "user": user,
                    "text": text.replace("\n", " ")
                })
                new_found = True
                print(f"   + {user}: {text[:40]}...")

                if len(comments_data) >= max_cmt: break
            except:
                continue

        if new_found:
            retries = 0
            # Cuộn đến comment cuối để load thêm
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", items[-1])
        else:
            retries += 1
            driver.execute_script("window.scrollBy(0, 600);")

        time.sleep(random.uniform(2, 4))
        
    return comments_data

# ================= MAIN =================
def main():
    # 1. Khởi tạo trình duyệt với Session đã lưu
    driver = setup_driver()

    try:
        logger.info("🚀 BẮT ĐẦU CHƯƠNG TRÌNH")
        
        # 2. Lấy danh sách link video từ mục khám phá hoặc profile
        # Với LIMIT_VIDEOS = 200, hàm này sẽ cuộn trang để thu thập đủ link
        video_links = scroll_get_video_links(driver, LIMIT_VIDEOS)
        
        if not video_links:
            logger.error("❌ Không tìm thấy link video nào. Vui lòng kiểm tra lại trạng thái đăng nhập hoặc kết nối.")
            return

        logger.info(f"✅ Đã thu thập được {len(video_links)} video. Bắt đầu lấy chi tiết...")

        # 3. Duyệt qua từng link video để lấy thông tin và comment
        for idx, url in enumerate(video_links, 1):
            try:
                logger.info(f"\n--- Xử lý video [{idx}/{len(video_links)}] ---")
                logger.info(f"🔗 Link: {url}")
                
                # Lấy thông tin video (Like, Comment count, Caption)
                video_data = get_video_info(driver, url)
                
                # Lưu thông tin video vào CSV ngay lập tức
                save_to_csv(VIDEO_FILE, video_data, video_data.keys())

                # Kiểm tra số lượng comment trước khi quét để tiết kiệm thời gian
                # Chuyển đổi sang số nguyên nếu có thể để so sánh
                try:
                    cmt_count_str = video_data.get("comment_count", "0")
                    # Xử lý các trường hợp count dạng "1.2K" hoặc rỗng
                    if not cmt_count_str or cmt_count_str == "0":
                        logger.info("⏩ Video không có bình luận hoặc bình luận bị tắt. Bỏ qua.")
                        continue
                except:
                    pass

                # Gọi hàm get_comments (Dùng Selenium để quét comment)
                comments = get_comments(
                    driver, 
                    video_data["video_id"], 
                    MAX_COMMENTS_PER_VIDEO
                )
                
                if comments:
                    save_to_csv(COMMENT_FILE, comments, comments[0].keys())
                    logger.info(f"✅ Đã lưu {len(comments)} bình luận từ video {video_data['video_id']}")
                else:
                    logger.warning(f"⚠️ Không tìm thấy bình luận nào cho video này.")

                # Nghỉ ngơi ngẫu nhiên để tránh bị TikTok phát hiện bot
                sleep_time = random.uniform(5, 10)
                logger.info(f"😴 Nghỉ {sleep_time:.2f}s...")
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"❌ Lỗi khi xử lý video tại {url}: {e}")
                # Tiếp tục với video tiếp theo thay vì dừng toàn bộ
                continue

        logger.info("\n🎉 TẤT CẢ TIẾN TRÌNH ĐÃ HOÀN THÀNH!")

    except KeyboardInterrupt:
        logger.info("\n🛑 Người dùng đã chủ động dừng chương trình.")
    except Exception as e:
        logger.error(f"💥 Lỗi nghiêm trọng: {e}")
    finally:
        # Luôn đảm bảo trình duyệt được đóng sạch sẽ
        logger.info("👋 Đang đóng trình duyệt...")
        driver.quit()

if __name__ == "__main__":
    main()