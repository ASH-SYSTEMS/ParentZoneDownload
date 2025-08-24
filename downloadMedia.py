# ScriptC_stable_scroll.py
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

DOWNLOAD_DIR = "downloads_timeline"

def init_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")  # optional
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def download_with_name(url, media_id, ext):
    out_path = os.path.join(DOWNLOAD_DIR, f"{media_id}{ext}")
    if os.path.exists(out_path):
        return
    try:
        print(f"Downloading {os.path.basename(out_path)}")
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        print(f"Failed: {url} ({e})")

def scroll_and_collect(driver, pause_time=2, max_no_new=10):
    """
    Incrementally scroll and collect all media items from timeline.
    Stops after `max_no_new` consecutive scrolls with no new items.
    """
    seen_urls = set()
    no_new_count = 0
    last_scroll_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # 1) Collect currently visible media
        media_items = driver.execute_script("""
            let imgs = Array.from(document.querySelectorAll("img[src*='/v1/media/']"));
            return imgs.map(img => {
                let container = img.closest("div");
                let isVideo = false;
                if (container) {
                    let svg = container.querySelector("svg[data-testid='VideocamIcon']");
                    if (svg) isVideo = true;
                }
                return {src: img.src, isVideo: isVideo};
            });
        """)

        # 2) Download new items
        new_count = 0
        for item in media_items:
            src = item["src"]
            if src in seen_urls:
                continue
            seen_urls.add(src)
            new_count += 1

            full_url = src.replace("/thumbnail", "/full")
            try:
                media_id = full_url.split("/v1/media/")[1].split("/")[0]
            except Exception:
                media_id = str(abs(hash(full_url)))
            ext = ".mp4" if item["isVideo"] else ".jpg"
            download_with_name(full_url, media_id, ext)

        print(f"Found {len(seen_urls)} total items, {new_count} new this scroll.")

        # 3) Scroll incrementally
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(pause_time)

        # 4) Check if page height changed
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_count == 0 and new_height == last_scroll_height:
            no_new_count += 1
        else:
            no_new_count = 0
        last_scroll_height = new_height

        # 5) Stop if no new items for several consecutive scrolls
        if no_new_count >= max_no_new:
            print("Reached end of timeline.")
            break

    return seen_urls

def main():
    ensure_dir(DOWNLOAD_DIR)
    driver = init_driver()

    # 1) Login manually
    driver.get("https://www.parentzone.me/login")
    input("Log in in the opened browser. When you see your dashboard, press Enter here...")

    # 2) Navigate to timeline
    driver.get("https://www.parentzone.me/timeline")
    time.sleep(5)

    # 3) Progressive scroll & download
    seen = scroll_and_collect(driver)

    print(f"Done. Total unique media downloaded: {len(seen)}")
    driver.quit()

if __name__ == "__main__":
    main()
