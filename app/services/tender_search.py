# -*- coding: utf-8 -*-
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://e-nabavki.gov.mk/PublicAccess/home.aspx#/notices"
ROW_SELECTORS = [
    "a.show-documents[data-rel]",
    "a[data-rel][class*='show-documents']",
    "table a[data-rel]",
    "table tbody tr",
    "table tr",
]


@dataclass
class TenderRow:
    index: int
    title: str
    institution: str
    deadline: str
    dossier_id: str
    source_page: int = 1
    row_text: str = ""


def setup_driver(headless: bool, download_dir: str) -> Chrome:
    os.makedirs(download_dir, exist_ok=True)
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--log-level=3")
    opts.add_argument("--disable-logging")
    opts.add_argument("--disable-background-networking")
    opts.add_argument("--disable-component-update")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    opts.add_experimental_option("prefs", prefs)
    service = Service(ChromeDriverManager().install(), log_output=subprocess.DEVNULL)
    return webdriver.Chrome(service=service, options=opts)


def js_click(driver: Chrome, element) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    driver.execute_script("arguments[0].click();", element)


def wait_dom_ready(driver: Chrome, sec: int = 20) -> None:
    WebDriverWait(driver, sec).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def ensure_on_notices(driver: Chrome, wait: WebDriverWait) -> None:
    driver.get(BASE_URL)
    try:
        wait.until(lambda d: "/#/notices" in (d.current_url or ""))
    except TimeoutException:
        pass


def open_search_panel(driver: Chrome, wait: WebDriverWait, log: Callable[[str], None]) -> None:
    try:
        panel = wait.until(
            EC.presence_of_element_located((By.XPATH, "//span[@label-for='SEARCH']"))
        )
        js_click(driver, panel)
        time.sleep(0.3)
    except TimeoutException:
        log("WARNING: Search panel button not found, continuing.")


def search_keyword(driver: Chrome, wait: WebDriverWait, keyword: str) -> None:
    field_xpaths = [
        "//input[@ng-model='searchModel.Subject']",
        "//input[@place-holder-for='SUBJECT SEARCH']",
        "//input[contains(@placeholder,'Subject')]",
        "//input[contains(@placeholder,'Предмет')]",
    ]
    button_xpaths = [
        "//input[@ng-click='filter()']",
        "//input[@label-for-submit='SEARCH']",
        "//input[@type='button' and (contains(@value,'Search') or contains(@value,'SEARCH'))]",
        "//input[@type='button' and contains(@value,'Пребарувај')]",
    ]

    field = None
    for xp in field_xpaths:
        try:
            field = WebDriverWait(driver, 4).until(
                EC.visibility_of_element_located((By.XPATH, xp))
            )
            break
        except TimeoutException:
            continue

    if field is None:
        raise TimeoutException("Search input field not found.")

    field.clear()
    field.send_keys(keyword)

    for xp in button_xpaths:
        try:
            button = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            js_click(driver, button)
            return
        except TimeoutException:
            continue

    # Last fallback: submit with Enter if explicit button is not found.
    field.send_keys("\n")


def fetch_tenders_via_js(driver: Chrome) -> list[dict]:
    js = r"""
    const out = [];
    const links = document.querySelectorAll(
      "a.show-documents[data-rel], a[data-rel][class*='show-documents'], table a[data-rel]"
    );
    links.forEach((a, idx) => {
      const tr = a.closest("tr");
      const tds = tr ? Array.from(tr.querySelectorAll("td")) : [];
      const cell = i => (tds[i] ? tds[i].innerText.trim() : "");
      out.push({
        index: idx + 1,
        dossier: a.getAttribute("data-rel") || "",
        title: cell(1),
        institution: cell(2),
        deadline: cell(3),
        row_text: tds.map(td => (td.innerText || "").trim()).join(" | "),
      });
    });
    if (out.length === 0) {
      const rows = document.querySelectorAll("table tbody tr, table tr");
      let idx = 1;
      rows.forEach((tr) => {
        const tds = Array.from(tr.querySelectorAll("td"));
        if (tds.length < 3) {
          return;
        }
        const cell = i => (tds[i] ? tds[i].innerText.trim() : "");
        const title = cell(1) || cell(0);
        const institution = cell(2) || "";
        const deadline = cell(3) || "";
        const dossier = (tr.getAttribute("data-rel") || "").trim();
        if (!(title || institution || deadline)) {
          return;
        }
        out.push({
          index: idx++,
          dossier: dossier || "",
          title,
          institution,
          deadline,
          row_text: tds.map(td => (td.innerText || "").trim()).join(" | "),
        });
      });
    }
    return out;
    """
    return driver.execute_script(js)


def has_any_result_rows(driver: Chrome) -> bool:
    js = r"""
    const links = document.querySelectorAll(
      "a.show-documents[data-rel], a[data-rel][class*='show-documents'], table a[data-rel]"
    );
    if (links.length > 0) return true;
    const rows = document.querySelectorAll("table tbody tr, table tr");
    for (const tr of rows) {
      const tds = tr.querySelectorAll("td");
      if (tds.length >= 3) return true;
    }
    return false;
    """
    try:
        return bool(driver.execute_script(js))
    except Exception:
        return False


def save_debug_snapshot(
    driver: Chrome, snapshot_dir: str, prefix: str = "search-timeout"
) -> tuple[str, str]:
    out = Path(snapshot_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = out / f"{prefix}_{stamp}.html"
    png_path = out / f"{prefix}_{stamp}.png"
    html_path.write_text(driver.page_source, encoding="utf-8")
    try:
        driver.save_screenshot(str(png_path))
    except Exception:
        png_path = Path("")
    return str(html_path), str(png_path)


def wait_for_result_rows(
    driver: Chrome,
    wait: WebDriverWait,
    log: Callable[[str], None],
    attempts: int = 3,
    base_delay_sec: float = 1.0,
    snapshot_dir: str | None = None,
) -> bool:
    for attempt in range(1, attempts + 1):
        if has_any_result_rows(driver):
            return True
        for selector in ROW_SELECTORS:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return True
            except TimeoutException:
                continue
        delay = base_delay_sec * attempt
        log(f"INFO: No rows detected (attempt {attempt}/{attempts}), retrying in {delay:.1f}s.")
        time.sleep(delay)

    if snapshot_dir:
        html_path, png_path = save_debug_snapshot(driver, snapshot_dir)
        if png_path:
            log(f"WARN: Search timeout snapshot saved: {html_path} and {png_path}")
        else:
            log(f"WARN: Search timeout snapshot saved: {html_path}")
    return False


def collect_tenders(driver: Chrome, wait: WebDriverWait, log: Callable[[str], None]) -> list[TenderRow]:
    data = fetch_tenders_via_js(driver)
    if not data:
        log("WARNING: No tender rows found on current page.")
        return []
    rows = [
        TenderRow(
            index=item["index"],
            title=item["title"],
            institution=item["institution"],
            deadline=item["deadline"],
            dossier_id=item["dossier"],
            source_page=1,
            row_text=item.get("row_text", ""),
        )
        for item in data
    ]
    log(f"Found {len(rows)} results.")
    return rows


def click_next_page(driver: Chrome, wait: WebDriverWait, log: Callable[[str], None]) -> bool:
    xpaths = [
        "//li[contains(@class,'next') and not(contains(@class,'disabled'))]/a",
        "//a[contains(@aria-label,'Next') and not(contains(@class,'disabled'))]",
        "//a[contains(.,'Next') and not(contains(@class,'disabled'))]",
        "//a[contains(.,'Следна') and not(contains(@class,'disabled'))]",
        "//button[contains(.,'Next') and not(@disabled)]",
        "//button[contains(.,'Следна') and not(@disabled)]",
    ]
    for xp in xpaths:
        try:
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xp)))
            js_click(driver, btn)
            time.sleep(1.0)
            return True
        except Exception:
            continue
    log("INFO: No next-page control found or no more pages.")
    return False


def dedupe_tenders(rows: list[TenderRow]) -> list[TenderRow]:
    seen: set[str] = set()
    out: list[TenderRow] = []
    for row in rows:
        key = (row.dossier_id or "").strip()
        if not key:
            key = f"{row.title}|{row.institution}|{row.deadline}"
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def collect_all_pages(
    driver: Chrome,
    wait: WebDriverWait,
    log: Callable[[str], None],
    max_pages: int = 10,
    snapshot_dir: str | None = None,
) -> list[TenderRow]:
    all_rows: list[TenderRow] = []
    page = 1
    prev_signature: tuple[str, ...] | None = None
    while page <= max_pages:
        wait_for_result_rows(
            driver,
            wait,
            log,
            attempts=2,
            base_delay_sec=1.0,
            snapshot_dir=snapshot_dir,
        )
        page_rows = collect_tenders(driver, wait, log)
        for r in page_rows:
            r.source_page = page
        log(f"INFO: Page {page} rows: {len(page_rows)}")
        all_rows.extend(page_rows)

        current_signature = tuple((r.dossier_id or "") for r in page_rows[:5])
        if prev_signature is not None and current_signature and current_signature == prev_signature:
            log("INFO: Pagination appears stuck on the same page data. Stopping.")
            break
        prev_signature = current_signature

        # If page 1 has rows but later page is empty, stop immediately.
        if page > 1 and len(page_rows) == 0:
            log("INFO: Empty page reached after first page. Stopping pagination.")
            break

        if page >= max_pages:
            log(f"INFO: Reached max_pages={max_pages}.")
            break
        if not click_next_page(driver, wait, log):
            break
        page += 1

    unique_rows = dedupe_tenders(all_rows)
    log(
        f"INFO: Pagination complete. pages={page}, total_rows={len(all_rows)}, unique_rows={len(unique_rows)}"
    )
    return unique_rows


def find_dossier_on_pages(
    driver: Chrome,
    wait: WebDriverWait,
    dossier_id: str,
    log: Callable[[str], None],
    max_pages: int = 10,
) -> bool:
    page = 1
    while page <= max_pages:
        try:
            show = WebDriverWait(driver, 4).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//a[contains(@class,'show-documents') and @data-rel='{dossier_id}']")
                )
            )
            js_click(driver, show)
            return True
        except Exception:
            pass

        if page >= max_pages:
            break
        if not click_next_page(driver, wait, log):
            break
        page += 1
    return False


def click_show_for_dossier(driver: Chrome, wait: WebDriverWait, dossier_id: str) -> None:
    show = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//a[contains(@class,'show-documents') and @data-rel='{dossier_id}']")
        )
    )
    js_click(driver, show)


def click_download_all_in_modal(driver: Chrome, wait: WebDriverWait) -> None:
    button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//span[@label-for='DOWNLOAD_ALL_TD_DOCS']"))
    )
    js_click(driver, button)


def handle_download_doc_without_login(driver: Chrome, log: Callable[[str], None]) -> int:
    try:
        try:
            wait_dom_ready(driver, 10)
        except Exception:
            pass

        try:
            urls = driver.execute_script("return (window.fileUrls || []).slice();")
            if not isinstance(urls, list):
                urls = []
        except Exception:
            urls = []

        if not urls:
            anchors = driver.find_elements(
                By.XPATH, "//a[contains(@href,'/File/DownloadPublicFile?fileId=')]"
            )
            urls = [a.get_attribute("href") for a in anchors if a.get_attribute("href")]

        if not urls:
            log("WARNING: No direct download links found.")
            return 0

        started = 0
        for i, url in enumerate(urls, 1):
            current_url = url
            if not current_url.startswith("http"):
                current_url = "https://www.e-nabavki.gov.mk" + current_url
            log(f"DOWNLOAD [{i}/{len(urls)}] {current_url}")
            driver.get(current_url)
            started += 1
            time.sleep(0.8)
        return started
    except Exception as exc:
        log(f"ERROR: Download failed: {exc}")
        return 0


def login_on_download_doc(
    driver: Chrome, username: str, password: str, log: Callable[[str], None], timeout: int = 15
) -> bool:
    try:
        user = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.ID, "ctl00_publicAccess_txtUsername"))
        )
        pwd = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.ID, "ctl00_publicAccess_txtPassword"))
        )
        login_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.ID, "ctl00_publicAccess_btnLogin"))
        )

        try:
            user.clear()
        except Exception:
            pass
        user.click()
        user.send_keys(username.strip())

        try:
            pwd.clear()
        except Exception:
            pass
        pwd.click()
        pwd.send_keys(password)

        js_click(driver, login_btn)

        WebDriverWait(driver, timeout).until(
            lambda d: d.find_elements(By.ID, "ctl00_publicAccess_btnDownloadAll")
            or d.find_elements(By.XPATH, "//a[contains(@href,'/File/DownloadPublicFile?fileId=')]")
            or d.execute_script("return !!window.fileUrls && window.fileUrls.length > 0;")
        )
        log("INFO: Login on download page succeeded.")
        return True
    except Exception as exc:
        log(f"WARNING: Login on download page failed: {exc}")
        return False
