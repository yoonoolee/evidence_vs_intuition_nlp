import os
import re
import time
import json
import argparse
from urllib.parse import quote
from typing import List, Optional

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


CLICK_WAIT_TIME = 0.5


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def sanitize_filename(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return sanitized.strip("._-") or "hearing"


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def load_house_committees(mapping_path: str) -> List[str]:
    if not os.path.exists(mapping_path):
        return []
    with open(mapping_path, "r") as f:
        data = json.load(f)
    # Use the canonical names (top-level keys)
    return list(data.keys())


def build_committee_url(congress_no: str, committee_name: str) -> str:
    encoded_committee = quote(committee_name, safe="")
    return f"https://www.govinfo.gov/app/collection/chrg/{congress_no}/house/{encoded_committee}"


def _case_insensitive_text_xpath(text_literal: str) -> str:
    # Helper to match case-insensitively using translate
    lower = text_literal.lower()
    upper = text_literal.upper()
    return f"translate(normalize-space(text()), '{lower}', '{upper}')='{text_literal.upper()}'"


def collect_text_links_on_committee_page(driver: webdriver.Chrome) -> List[dict]:
    # Each hearing block has buttons PDF | TEXT | DETAILS. We collect the TEXT anchors
    links = []
    # Wait a moment for content to render
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//a[{_case_insensitive_text_xpath('TEXT')}]"))
        )
    except Exception:
        time.sleep(CLICK_WAIT_TIME)

    # Attempt to load dynamically by scrolling through the page to trigger lazy content (if any)
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(CLICK_WAIT_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Strategy: gather all TEXT anchors first to avoid stale references; then try to find a nearby title
    anchors = driver.find_elements(By.XPATH, f'//a[{_case_insensitive_text_xpath("TEXT")}]')
    for a in anchors:
        try:
            href = a.get_attribute('href')
            # Try to locate a nearby title within the same row or container
            container = a.find_element(By.XPATH, './ancestor::tr | ./ancestor::div[contains(@class, "row")]')
            title_elem = container.find_elements(By.XPATH, './/td[1]//span | .//span[contains(@class, "title")] | .//a[contains(@href, "details")]/preceding::span[1]')
            title = title_elem[0].text if title_elem else ""
            links.append({"title": title, "url": href})
        except Exception:
            # If any structure assumption fails, still keep the URL
            if href:
                links.append({"title": "", "url": href})
    return links


def download_text(url: str, out_path: str, timeout: int = 30, delay: float = 0.2) -> bool:
    try:
        with requests.get(url, timeout=timeout) as r:
            r.raise_for_status()
            # Some TEXT endpoints are HTML; save as .html if content-type indicates text/html
            content_type = r.headers.get("Content-Type", "").lower()
            ext = ".txt"
            if "html" in content_type:
                ext = ".html"
            if not out_path.endswith(ext):
                out_path = out_path + ext
            with open(out_path, "wb") as f:
                f.write(r.content)
        if delay:
            time.sleep(delay)
        return True
    except Exception:
        return False


def scrape_committee(
    congress_no: str,
    committee_name: str,
    out_dir: str,
) -> List[str]:
    url = build_committee_url(congress_no, committee_name)
    driver = setup_driver()
    try:
        driver.get(url)
        time.sleep(1)
        text_links = collect_text_links_on_committee_page(driver)

        saved_files: List[str] = []
        base_dir = os.path.join(out_dir, "house", congress_no, sanitize_filename(committee_name))
        ensure_dir(base_dir)

        for idx, item in enumerate(text_links, start=1):
            title_slug = sanitize_filename(item.get("title") or f"hearing_{idx}")
            filename = os.path.join(base_dir, f"{title_slug}")
            if os.path.exists(filename + ".txt") or os.path.exists(filename + ".html"):
                continue
            ok = download_text(item["url"], filename)
            if ok:
                saved_files.append(filename)
        return saved_files
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Scrape and download all 'TEXT' files for House committee hearings")
    parser.add_argument("--congress", required=True, help="Congress number, e.g., 119")
    parser.add_argument(
        "--committee",
        action="append",
        help="Committee name (can be repeated). If omitted with --all, all known committees are scraped.",
    )
    parser.add_argument("--all", action="store_true", help="Scrape all House committees from the mapping file")
    parser.add_argument(
        "--mapping",
        default=os.path.join(os.path.dirname(__file__), "../data/mappings/house_committee_names.json"),
        help="Path to house committee mapping JSON (default: data/mappings/house_committee_names.json)",
    )
    parser.add_argument(
        "--outdir",
        default=os.path.join(os.path.dirname(__file__), "../data/hearing_data/transcripts"),
        help="Base output directory",
    )
    args = parser.parse_args()

    congress_no: str = str(args.congress)
    committees: List[str] = []

    if args.all:
        committees = load_house_committees(os.path.abspath(args.mapping))
    if args.committee:
        committees.extend(args.committee)

    if not committees:
        raise SystemExit("No committees specified. Use --committee multiple times or --all.")

    out_dir = os.path.abspath(args.outdir)
    ensure_dir(out_dir)

    for name in committees:
        print(f"Scraping {name} (Congress {congress_no})...")
        saved = scrape_committee(congress_no, name, out_dir)
        print(f"Saved {len(saved)} files for {name}")


if __name__ == "__main__":
    main()


