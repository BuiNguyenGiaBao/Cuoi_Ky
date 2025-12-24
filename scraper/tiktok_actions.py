import undetected_chromedriver as uc
import time
import random
import csv
import os
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= CẤU HÌNH (SỬA Ở ĐÂY) =================
# Hãy đổi sang một Profile cụ thể, đừng dùng trang chủ
TARGET_PROFILE = "https://www.tiktok.com"
LIMIT_VIDEOS = 200           # Số lượng video muốn lấy
MAX_COMMENTS_PER_VIDEO = 100    # Số comment tối đa mỗi video


# ================= CONFIG =================
TARGET_PROFILE = "https://www.tiktok.com/"
LIMIT_VIDEOS = 200
MAX_COMMENTS_PER_VIDEO = 50

VIDEO_FILE = "tiktok_videos.csv"
COMMENT_FILE = "tiktok_comments.csv"
VIDEO_FILE = "tiktok_videos_fixed.csv"
COMMENT_FILE = "tiktok_comments_fixed.csv"

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# ================= 1. KHỞI TẠO TRÌNH DUYỆT =================
def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    driver = uc.Chrome(options=options)
    return driver

def solve_captcha(driver):
    """Đợi bạn giải Captcha nếu nó hiện ra"""
    try:
        if driver.find_elements(By.CLASS_NAME, "captcha_verify_container"):
            logger.warning("⚠️ PHÁT HIỆN CAPTCHA! Bạn có 60s để giải bằng tay...")
            WebDriverWait(driver, 60).until_not(
                EC.presence_of_element_located((By.CLASS_NAME, "captcha_verify_container"))
            )
            logger.info("✅ Captcha đã xong.")
            time.sleep(2)
    except:
        pass

# ================= 2. LẤY LINK VIDEO TỪ PROFILE =================
def get_video_links(driver, url, limit):
    logger.info(f"🌍 Đang truy cập: {url}")
    driver.get(url)
    time.sleep(5) # Chờ web load
    solve_captcha(driver)
    
    links = set()
    
    # Cuộn trang để lấy đủ link
    while len(links) < limit:
        # Tìm thẻ a chứa link video (Selector chuẩn cho Profile)
        elems = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/video/"]')
        
        for e in elems:
            href = e.get_attribute("href")
            if href:
                links.add(href)
                if len(links) >= limit: break
        
        if len(links) >= limit: break

        logger.info(f"📜 Đang cuộn... Đã tìm thấy {len(links)} video")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 4))
        
    return list(links)[:limit]

# ================= 3. LẤY THÔNG TIN VIDEO =================
def get_video_data(driver, video_url):
    driver.get(video_url)
    time.sleep(3)
    solve_captcha(driver)
    
    video_id = video_url.split("/video/")[-1].split("?")[0]
    
    data = {
        "video_id": video_id,
        "url": video_url,
        "caption": "N/A",
        "likes": "0",
        "comments_count": "0"
    }
    
    try:
        # Dùng data-e2e là ổn định nhất
        data["caption"] = driver.find_element(By.CSS_SELECTOR, '[data-e2e="video-desc"]').text
    except: pass
    
    try:
        data["likes"] = driver.find_element(By.CSS_SELECTOR, '[data-e2e="like-count"]').text
    except: pass
    
    try:
        data["comments_count"] = driver.find_element(By.CSS_SELECTOR, '[data-e2e="comment-count"]').text
    except: pass
    
    logger.info(f"🎬 Video: {video_id} | ❤️ {data['likes']} | 💬 {data['comments_count']}")
    return data



# ================= TIKTOK API COMMENT =================
def fetch_comments_api(video_id, cookies, user_agent, max_comments=50):
    url = "https://www.tiktok.com/api/comment/list/"
    headers = {
        "User-Agent": user_agent,
        "Referer": f"https://www.tiktok.com/video/{video_id}",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty"
    }

    params = {
        "aid": 1988,
        "aweme_id": video_id,
        "count": 10,
        "cursor": 0,
    }

    comments = []

    while len(comments) < max_comments:
        for attempt in range(3):
            try:
                r = requests.get(
                    url,
                    headers=headers,
                    cookies=cookies,
                    params=params,
                    timeout=10
                )
                break
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Retry {attempt+1}/3: {e}")
                time.sleep(random.uniform(2, 4))
        else:
            break

        if r.status_code != 200:
            logger.warning(f"❌ Status code {r.status_code}")
            break

        try:
            data = r.json()
        except ValueError:
            logger.warning("❌ TikTok trả response không phải JSON")
            break

        if "comments" not in data:
            break

        for c in data["comments"]:
            comments.append({
                "video_id": video_id,
                "user": c["user"]["nickname"],
                "comment_text": c["text"]
            })

        if not data.get("has_more"):
            break

        params["cursor"] = data["cursor"]
        time.sleep(random.uniform(2.5, 4))

    logger.info(f"💬 Lấy được {len(comments)} comment")
    return comments



# ================= CSV =================
def save_csv(file, rows, headers):
    exists = os.path.isfile(file)
    with open(file, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not exists:
            writer.writeheader()
        if isinstance(rows, list):
            writer.writerows(rows)
        else:
            writer.writerow(rows)


# ================= 4. LẤY COMMENT (BẰNG SELENIUM) =================
def get_comments(driver, video_id, max_cmt):
    comments = []
    logger.info("⬇️ Đang tải comment...")
    
    last_count = 0
    retries = 0
    
    while len(comments) < max_cmt:
        # Tìm tất cả các ô comment cấp 1
        cmt_elems = driver.find_elements(By.CSS_SELECTOR, '[data-e2e="comment-level-1"]')
        
        if len(cmt_elems) > last_count:
            # Xử lý các comment mới load được
            new_items = cmt_elems[last_count:]
            for item in new_items:
                try:
                    user = item.find_element(By.CSS_SELECTOR, '[data-e2e="comment-username"]').text
                    text = item.find_element(By.CSS_SELECTOR, '[data-e2e="comment-level-1-content"]').text
                    
                    comments.append({
                        "video_id": video_id,
                        "user": user,
                        "text": text.replace("\n", " ")
                    })
                    if len(comments) >= max_cmt: break
                except: continue
            
            last_count = len(cmt_elems)
            retries = 0
            logger.info(f"   -> Đã lấy {len(comments)} comment...")
            
            # Cuộn xuống một chút để load tiếp
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(2)
        else:
            retries += 1
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
            if retries > 3: break # Hết comment hoặc mạng lag
            
    return comments

# ================= 5. LƯU FILE =================
def save_to_csv(filename, data_list):
    if not data_list: return
    
    exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=data_list[0].keys())
        if not exists: writer.writeheader()
        writer.writerows(data_list)


# ================= MAIN =================
if __name__ == "__main__":
    driver = setup_driver()
    
    try:
        # 1. Lấy danh sách video
        links = get_video_links(driver, TARGET_PROFILE, LIMIT_VIDEOS)
        
        if not links:
            logger.error("❌ Không lấy được link nào. Kiểm tra lại Profile URL.")
        else:
            # 2. Duyệt từng video
            for i, link in enumerate(links, 1):
                logger.info(f"\n[{i}/{len(links)}] Đang xử lý: {link}")
                
                # Lấy Info
                v_data = get_video_data(driver, link)
                save_to_csv(VIDEO_FILE, [v_data])
                
                # Lấy Comment (nếu video có comment)
                if v_data['comments_count'] != '0':
                    c_data = get_comments(driver, v_data['video_id'], MAX_COMMENTS_PER_VIDEO)
                    save_to_csv(COMMENT_FILE, c_data)
                
                time.sleep(random.uniform(3, 5))
                
        logger.info("\n✅ HOÀN THÀNH! File đã được lưu.")
        
    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")
        
    finally:
        logger.info("👋 Đóng trình duyệt sau 5 giây...")
        time.sleep(5)
        driver.quit()

