# script2_gallery_fullsize.py
import os
import time
import requests
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

DOWNLOAD_DIR = "downloads_media"

def init_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")  # uncomment to run headless
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def download_with_name(url, media_id, default_ext=".jpg"):
    out_path = os.path.join(DOWNLOAD_DIR, f"{media_id}{default_ext}")
    if os.path.exists(out_path):
        print(f"Already downloaded {os.path.basename(out_path)}")
        return
    try:
        print(f"Downloading -> {os.path.basename(out_path)}")
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def extract_full_img_links(driver):
    """Extract all <img src> links and replace 'thumbnail' with 'full'."""
    script = """
      return Array.from(document.querySelectorAll("img[src*='/v1/media/']"))
                  .map(img => img.src);
    """
    thumbs = driver.execute_script(script) or []
    fulls = []
    for t in thumbs:
        fulls.append(t.replace("/thumbnail", "/full"))
    print(f"Found {len(fulls)} media images on the gallery page.")
    return fulls

def main():
    ensure_dir(DOWNLOAD_DIR)
    driver = init_driver()

    # 1) Manual login
    driver.get("https://www.parentzone.me/login")
    input("Log in in the opened browser. When you see your dashboard, press Enter here...")

    # 2) Navigate to gallery
    driver.get("https://www.parentzone.me/gallery")
    time.sleep(3)
    print("Scroll the gallery page if necessary so all items load.")
    input("When ready, press Enter here to continue...")

    # 3) Extract fullsize image links
    img_links = extract_full_img_links(driver)

    # 4) Download each
    seen = set()
    for link in img_links:
        # get media id (the number after /media/)
        try:
            media_id = link.split("/v1/media/")[1].split("/")[0]
        except Exception:
            media_id = str(abs(hash(link)))
        if link in seen:
            continue
        seen.add(link)
        download_with_name(link, media_id, ".jpg")

    print("Done.")
    driver.quit()

if __name__ == "__main__":
    main()
