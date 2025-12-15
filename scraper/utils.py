import time
import random

def human_sleep(min_t=1.5, max_t=3.8):
    t = random.uniform(min_t, max_t)
    time.sleep(t)

def random_scroll(driver):
    scroll = random.randint(300, 1200)
    driver.execute_script(f"window.scrollBy(0, {scroll});")
    human_sleep(1.5, 3)

def random_mouse_move(driver):
    x = random.randint(200, 500)
    y = random.randint(150, 400)
    driver.execute_script(f"window.scrollTo({x}, {y});")
    human_sleep(0.3, 0.8)

def extract_caption(desc):
    parts = desc.split("#")
    return parts[0].strip()

def extract_hashtags(desc):
    tags = []
    for part in desc.split("#")[1:]:
        tag = part.split()[0].strip()
        tags.append("#" + tag)
    return tags

