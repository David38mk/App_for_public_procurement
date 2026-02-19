# -*- coding: utf-8 -*-
import os
import time
import threading
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd  # pip install pandas openpyxl

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://e-nabavki.gov.mk/PublicAccess/home.aspx#/notices"

# =========================
# Selenium helpers
# =========================
def setup_driver(headless: bool, download_dir: str) -> Chrome:
    os.makedirs(download_dir, exist_ok=True)
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    # директно симнување без prompt
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    opts.add_experimental_option("prefs", prefs)
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

def js_click(driver: Chrome, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    driver.execute_script("arguments[0].click();", el)

def wait_dom_ready(driver: Chrome, sec: int = 20):
    WebDriverWait(driver, sec).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def ensure_on_notices(driver: Chrome, wait) -> None:
    """Оди на страницата Огласи и почекај Angular рутата."""
    driver.get(BASE_URL)
    try:
        wait.until(lambda d: "/#/notices" in (d.current_url or ""))
    except TimeoutException:
        pass

def open_search_panel(driver: Chrome, wait, log) -> None:
    """Клик на „Пребарувај“ панелот (ако постои)."""
    try:
        spn = wait.until(EC.presence_of_element_located((By.XPATH, "//span[@label-for='SEARCH']")))
        js_click(driver, spn)
        time.sleep(0.3)
    except TimeoutException:
        log("⚠ Не најдов копче „Пребарувај“ – продолжувам директно со полето.")

def search_keyword(driver: Chrome, wait, keyword: str) -> None:
    """Внес клучен збор во „Предмет на договорот“ и клик на Пребарувај."""
    fld = wait.until(
        EC.visibility_of_element_located((
            By.XPATH,
            "//input[@ng-model='searchModel.Subject' "
            "or @place-holder-for='SUBJECT SEARCH' "
            "or @placeholder='Предмет на договорот']"
        ))
    )
    fld.clear()
    fld.send_keys(keyword)

    btn = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//input[@ng-click='filter()' or @label-for-submit='SEARCH' or (@type='button' and contains(@value,'Пребарувај'))]"
        ))
    )
    js_click(driver, btn)

def fetch_tenders_via_js(driver: Chrome) -> list[dict]:
    """Еден атомски snapshot на табелата за да избегнеме stale елементи."""
    js = r"""
    const out = [];
    const links = document.querySelectorAll("a.show-documents[data-rel]");
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
      });
    });
    return out;
    """
    return driver.execute_script(js)

@dataclass
class TenderRow:
    index: int
    title: str
    institution: str
    deadline: str
    dossier_id: str

def collect_tenders(driver: Chrome, wait, log) -> list[TenderRow]:
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.show-documents[data-rel]")))
    time.sleep(0.3)  # кратко за Angular да заврши прецртување
    data = fetch_tenders_via_js(driver)
    rows: list[TenderRow] = [
        TenderRow(d["index"], d["title"], d["institution"], d["deadline"], d["dossier"])
        for d in data
    ]
    log(f"Найдени {len(rows)} резултати.")
    return rows

def click_show_for_dossier(driver: Chrome, wait, dossier_id: str) -> None:
    show = wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//a[contains(@class,'show-documents') and @data-rel='{dossier_id}']"))
    )
    js_click(driver, show)

def click_download_all_in_modal(driver: Chrome, wait) -> None:
    btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@label-for='DOWNLOAD_ALL_TD_DOCS']")))
    js_click(driver, btn)

def handle_download_doc_without_login(driver: Chrome, download_dir: str, log) -> int:
    """Без логирање: чита fileUrls или <a href='/File/DownloadPublicFile?fileId='> и симнува."""
    try:
        try:
            wait_dom_ready(driver, 10)
        except Exception:
            pass

        # пробај fileUrls од JS
        try:
            urls = driver.execute_script("return (window.fileUrls || []).slice();")
            if not isinstance(urls, list):
                urls = []
        except Exception:
            urls = []

        # ако нема, пробај anchors
        if not urls:
            anchors = driver.find_elements(By.XPATH, "//a[contains(@href,'/File/DownloadPublicFile?fileId=')]")
            urls = [a.get_attribute("href") for a in anchors if a.get_attribute("href")]

        if not urls:
            log("     ⚠ Нема директни линкови за преземање (fileUrls/anchors празно).")
            return 0

        log(f"     ⬇ Ќе симнам {len(urls)} документ(и).")
        started = 0
        for i, url in enumerate(urls, 1):
            if not url.startswith("http"):
                url = "https://www.e-nabavki.gov.mk" + url
            log(f"       [{i}/{len(urls)}] {url}")
            try:
                driver.get(url)
                started += 1
                time.sleep(0.8)
            except Exception as e:
                log(f"         ⚠ Грешка при отворање: {e}")

        time.sleep(1.0)
        return started

    except Exception as e:
        log(f"     ⚠ DownloadDoc: грешка при читање линкови/симнување: {e}")
        return 0

def login_on_downloaddoc(driver: Chrome, username: str, password: str, log) -> bool:
    """Логин на DownloadDoc.aspx (ASP.NET WebForms)."""
    try:
        user = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "ctl00_publicAccess_txtUsername"))
        )
        pwd = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "ctl00_publicAccess_txtPassword"))
        )
        btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "ctl00_publicAccess_btnLogin"))
        )

        try: user.clear()
        except Exception: pass
        user.click(); time.sleep(0.1)
        user.send_keys(username.strip())

        try: pwd.clear()
        except Exception: pass
        pwd.click(); time.sleep(0.1)
        for ch in password:
            pwd.send_keys(ch); time.sleep(0.02)

        js_click(driver, btn)

        # исход: download all / anchors / fileUrls
        WebDriverWait(driver, 15).until(
            lambda d: d.find_elements(By.ID, "ctl00_publicAccess_btnDownloadAll")
                      or d.find_elements(By.XPATH, "//a[contains(@href,'/File/DownloadPublicFile?fileId=')]")
                      or d.execute_script("return !!window.fileUrls && window.fileUrls.length>0;")
        )
        log("✓ Логирање на DownloadDoc успешно.")
        return True

    except TimeoutException:
        log("⚠ DownloadDoc: timeout при логирање.")
    except Exception as e:
        log(f"⚠ DownloadDoc: грешка при логирање: {e}")
    return False

# =========================
# Tkinter GUI
# =========================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Е-набавки – Пребарување, селекција и симнување")
        self.geometry("1040x720")

        # Inputs
        self.var_keyword = tk.StringVar(value="Интернет")
        self.var_username = tk.StringVar(value="")
        self.var_download = tk.StringVar(value=str(Path.cwd() / "downloads"))
        self.var_headless = tk.BooleanVar(value=False)

        self.entry_password = None

        # Selenium state
        self.driver: Chrome | None = None
        self.wait: WebDriverWait | None = None
        self.results: list[TenderRow] = []

        self._make_ui()

    # ---------- UI ----------
    def _make_ui(self):
        pad = {'padx': 6, 'pady': 6}
        top = ttk.Frame(self)
        top.pack(fill="x", **pad)

        ttk.Label(top, text="Клучен збор:").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.var_keyword, width=24).grid(row=0, column=1, sticky="w")

        ttk.Label(top, text="Корисничко име (опц.):").grid(row=0, column=2, sticky="w")
        ttk.Entry(top, textvariable=self.var_username, width=18).grid(row=0, column=3, sticky="w", padx=(0, 10))

        ttk.Label(top, text="Лозинка (опц.):").grid(row=0, column=4, sticky="w")
        self.entry_password = ttk.Entry(top, width=18, show="*")
        self.entry_password.grid(row=0, column=5, sticky="w")

        ttk.Label(top, text="Download папка:").grid(row=1, column=0, sticky="w")
        ent_dir = ttk.Entry(top, textvariable=self.var_download, width=50)
        ent_dir.grid(row=1, column=1, columnspan=3, sticky="we")
        ttk.Button(top, text="Избери…", command=self.choose_dir).grid(row=1, column=4, sticky="w")

        ttk.Checkbutton(top, text="Headless", variable=self.var_headless).grid(row=1, column=5, sticky="w")

        ttk.Button(top, text="Пребарај", command=self.on_search).grid(row=2, column=1, sticky="w", pady=(4, 0))
        ttk.Button(top, text="Симни селектиран", command=self.on_download_selected).grid(row=2, column=2, sticky="w", pady=(4, 0))
        ttk.Button(top, text="Симни повеќе", command=self.on_download_multi).grid(row=2, column=3, sticky="w", pady=(4, 0))
        ttk.Button(top, text="Извези во Excel", command=self.on_export_excel).grid(row=2, column=4, sticky="w", pady=(4, 0))

        # Table (Treeview)
        cols = ("#","Наслов","Институција","Рок","DossierID")
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=6, pady=(2,6))

        self.tree = ttk.Treeview(
            tree_frame,
            columns=cols,
            show="headings",
            height=16,
            selectmode="extended"  # Ctrl/Shift селектирање
        )
        for c, w in zip(cols, (50, 480, 300, 150, 380)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=yscroll.set)
        yscroll.pack(side="right", fill="y")

        # Log panel
        self.txt = tk.Text(self, height=12, wrap="word")
        self.txt.pack(fill="both", expand=False, padx=6, pady=6)
        self.txt.config(state="disabled")

    # ---------- Helpers ----------
    def choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.var_download.get() or str(Path.cwd()))
        if d:
            self.var_download.set(d)

    def log(self, msg: str):
        self.txt.config(state="normal")
        self.txt.insert("end", time.strftime("%H:%M:%S  ") + msg + "\n")
        self.txt.see("end")
        self.txt.config(state="disabled")
        self.update_idletasks()

    def set_busy(self, busy: bool):
        try:
            self.config(cursor="watch" if busy else "")
        except Exception:
            pass

    def ensure_driver(self) -> tuple[Chrome, WebDriverWait]:
        if self.driver is None:
            self.driver = setup_driver(self.var_headless.get(), self.var_download.get().strip() or str(Path.cwd()/ "downloads"))
            self.wait = WebDriverWait(self.driver, 20)
        return self.driver, self.wait

    # ---------- Core download routine reused ----------
    def _download_one(self, dossier_id: str, title: str, institution: str, deadline: str,
                      username: str, password: str, download_dir: str) -> int:
        """Го извршува цел процес за едно досие. Враќа број на стартувани симнувања."""
        driver, wait = self.ensure_driver()
        ensure_on_notices(driver, wait)
        open_search_panel(driver, wait, self.log)

        click_show_for_dossier(driver, wait, dossier_id)
        click_download_all_in_modal(driver, wait)

        time.sleep(1.0)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        started = handle_download_doc_without_login(driver, download_dir, self.log)
        if started == 0 and username and password:
            ok = login_on_downloaddoc(driver, username, password, self.log)
            if ok:
                # официјалното копче (ако постои)
                try:
                    btn_all = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "ctl00_publicAccess_btnDownloadAll"))
                    )
                    js_click(driver, btn_all)
                    self.log("✓ Кликнато „Преземи ги сите документи“ по логирање.")
                    time.sleep(1.2)
                except Exception:
                    pass
                started = handle_download_doc_without_login(driver, download_dir, self.log)
        return started

    # ---------- Actions ----------
    def on_search(self):
        keyword = (self.var_keyword.get() or "").strip()
        if not keyword:
            messagebox.showwarning("Недостига клучен збор", "Внеси клучен збор (пример: Интернет).")
            return

        def work():
            self.set_busy(True)
            self.log(f"▶ Пребарувам: „{keyword}“")
            try:
                driver, wait = self.ensure_driver()
                ensure_on_notices(driver, wait)
                open_search_panel(driver, wait, self.log)
                search_keyword(driver, wait, keyword)

                # чекај да има резултати и да се стабилизира DOM-от
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.show-documents[data-rel]")))
                time.sleep(0.3)

                # snapshot преку JS (без stale)
                self.results = collect_tenders(driver, wait, self.log)

                # пополни табела
                self.tree.delete(*self.tree.get_children())
                for r in self.results:
                    self.tree.insert("", "end", values=(r.index, r.title, r.institution, r.deadline, r.dossier_id))
                self.log("✓ Резултатите се прикажани во листата.")

            except WebDriverException as e:
                self.log(f"⚠ WebDriver грешка: {e}")
            except Exception as e:
                self.log(f"⚠ Грешка: {e}")
            finally:
                self.set_busy(False)

        threading.Thread(target=work, daemon=True).start()

    def on_download_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Нема селекција", "Одбери еден тендер од листата.")
            return

        item = self.tree.item(sel[0])  # земи прв селектиран
        _, title, institution, deadline, dossier_id = item["values"]
        username = (self.var_username.get() or "").strip()
        password = self.entry_password.get()
        download_dir = (self.var_download.get() or "").strip() or str(Path.cwd() / "downloads")

        def work():
            self.set_busy(True)
            self.log(f"⏬ Ќе симнувам: {title}  ({institution})  [рок: {deadline}]")
            try:
                started = self._download_one(dossier_id, title, institution, deadline,
                                             username, password, download_dir)
                self.log(f"✓ Готово. Тригерирани симнувања: {started}. Папка: {download_dir}")
            except WebDriverException as e:
                self.log(f"⚠ WebDriver грешка: {e}")
            except Exception as e:
                self.log(f"⚠ Грешка: {e}")
            finally:
                self.set_busy(False)

        threading.Thread(target=work, daemon=True).start()

    def on_download_multi(self):
        sels = self.tree.selection()
        if not sels:
            messagebox.showinfo("Нема селекција", "Означи еден или повеќе тендери (Ctrl/Shift-клик).")
            return

        username = (self.var_username.get() or "").strip()
        password = self.entry_password.get()
        download_dir = (self.var_download.get() or "").strip() or str(Path.cwd() / "downloads")

        self.log(f"⏬ Ќе симнувам {len(sels)} избрани тендери во: {download_dir}")

        def work():
            self.set_busy(True)
            total_started = 0
            try:
                for idx, sel in enumerate(sels, 1):
                    vals = self.tree.item(sel)["values"]
                    # колони: ("#","Наслов","Институција","Рок","DossierID")
                    _, title, institution, deadline, dossier_id = vals
                    self.log(f"   [{idx}/{len(sels)}] {title}  ({institution})  [рок: {deadline}]")
                    try:
                        started = self._download_one(dossier_id, title, institution, deadline,
                                                     username, password, download_dir)
                        total_started += started
                    except Exception as e:
                        self.log(f"     ⚠ Грешка при симнување за {dossier_id}: {e}")
                self.log(f"✓ Готово. Вкупно стартувани симнувања: {total_started}.")
            finally:
                self.set_busy(False)

        threading.Thread(target=work, daemon=True).start()

    def on_export_excel(self):
        if not self.results:
            messagebox.showinfo("Нема податоци", "Прво направи пребарување.")
            return

        default_path = Path(self.var_download.get() or Path.cwd()).joinpath("results.xlsx")
        out_path = filedialog.asksaveasfilename(
            initialdir=str(default_path.parent),
            initialfile=default_path.name,
            title="Сними како Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if not out_path:
            return

        rows = [{
            "Ред": r.index,
            "Наслов": r.title,
            "Институција": r.institution,
            "Рок": r.deadline,
            "DossierID": r.dossier_id,
        } for r in self.results]

        try:
            df = pd.DataFrame(rows)
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            df.to_excel(out_path, index=False)  # потребен е openpyxl
            self.log(f"✓ Excel извезен: {out_path}")
            if messagebox.askyesno("Отвори фајл", "Успешно извезено. Да го отворам Excel фајлот?"):
                os.startfile(out_path)
        except Exception as e:
            messagebox.showerror("Грешка при извоз", str(e))

    def destroy(self):
        # затвори драjвер
        try:
            if self.driver:
                time.sleep(1.0)
                self.driver.quit()
        except Exception:
            pass
        super().destroy()


if __name__ == "__main__":
    # Инсталирај:
    #   pip install selenium==4.24.0 webdriver-manager==4.0.2 pandas openpyxl
    # Потоа старт:
    #   python app_gui_full.py
    App().mainloop()

