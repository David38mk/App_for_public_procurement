# -*- coding: utf-8 -*-
import json
import os
import threading
import time
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from openpyxl import Workbook
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

try:
    from app.services.template_builder import extract_placeholders_from_docx, render_docx_template
    from app.services.tender_search import (
        TenderRow,
        click_download_all_in_modal,
        click_show_for_dossier,
        collect_tenders,
        ensure_on_notices,
        handle_download_doc_without_login,
        login_on_download_doc,
        open_search_panel,
        search_keyword,
        setup_driver,
        wait_for_result_rows,
    )
except ImportError:
    from services.template_builder import extract_placeholders_from_docx, render_docx_template
    from services.tender_search import (
        TenderRow,
        click_download_all_in_modal,
        click_show_for_dossier,
        collect_tenders,
        ensure_on_notices,
        handle_download_doc_without_login,
        login_on_download_doc,
        open_search_panel,
        search_keyword,
        setup_driver,
        wait_for_result_rows,
    )


class TenderSearchFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.var_keyword = tk.StringVar(value="Internet")
        self.var_download = tk.StringVar(value=str(Path.cwd() / "downloads"))
        self.var_headless = tk.BooleanVar(value=False)
        self.var_username = tk.StringVar(value="")
        self.var_password = tk.StringVar(value="")
        self.var_search_mode = tk.StringVar(value="Mode: idle")
        self.results: list[TenderRow] = []
        self.driver = None
        self.wait = None
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Keyword:").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.var_keyword, width=24).grid(row=0, column=1, sticky="w")
        ttk.Label(top, text="Username (optional):").grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Entry(top, textvariable=self.var_username, width=20).grid(row=0, column=3, sticky="w")
        ttk.Label(top, text="Password (optional):").grid(row=0, column=4, sticky="w", padx=(10, 0))
        ttk.Entry(top, textvariable=self.var_password, show="*", width=20).grid(row=0, column=5, sticky="w")

        ttk.Label(top, text="Download folder:").grid(row=1, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.var_download, width=60).grid(row=1, column=1, columnspan=4, sticky="we")
        ttk.Button(top, text="Browse...", command=self.choose_dir).grid(row=1, column=5, sticky="w")
        ttk.Checkbutton(top, text="Headless", variable=self.var_headless).grid(
            row=1, column=6, sticky="w", padx=(8, 0)
        )

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btns, text="Search", command=self.on_search).pack(side="left")
        ttk.Button(btns, text="Download selected", command=self.on_download_selected).pack(
            side="left", padx=6
        )
        ttk.Button(btns, text="Export Excel", command=self.on_export_excel).pack(side="left")
        ttk.Label(btns, textvariable=self.var_search_mode).pack(side="left", padx=(12, 0))

        cols = ("#", "Title", "Institution", "Deadline", "DossierID")
        wrap = ttk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="extended")
        widths = (50, 420, 260, 140, 260)
        for col, width in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        yscroll = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        yscroll.pack(side="right", fill="y")
        self.tree.configure(yscroll=yscroll.set)

        self.log_text = tk.Text(self, height=10, wrap="word")
        self.log_text.pack(fill="x", padx=8, pady=(0, 8))
        self.log_text.config(state="disabled")

    def log(self, msg: str):
        self.log_text.config(state="normal")
        self.log_text.insert("end", time.strftime("%H:%M:%S  ") + msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self.update_idletasks()

    def choose_dir(self):
        selected = filedialog.askdirectory(initialdir=self.var_download.get() or str(Path.cwd()))
        if selected:
            self.var_download.set(selected)

    def ensure_driver(self):
        if self.driver is None:
            self.driver = setup_driver(self.var_headless.get(), self.var_download.get().strip())
            self.wait = WebDriverWait(self.driver, 20)
        return self.driver, self.wait

    def on_search(self):
        keyword = (self.var_keyword.get() or "").strip()
        if not keyword:
            messagebox.showwarning("Missing keyword", "Enter a keyword.")
            return

        def work():
            self.log(f"SEARCH: {keyword}")
            try:
                used_fallback = False
                driver, wait = self.ensure_driver()
                snapshot_dir = str(Path(self.var_download.get().strip() or str(Path.cwd() / "downloads")) / "debug")
                ensure_on_notices(driver, wait)
                open_search_panel(driver, wait, self.log)
                search_keyword(driver, wait, keyword)
                wait_for_result_rows(
                    driver,
                    wait,
                    self.log,
                    attempts=3,
                    base_delay_sec=1.2,
                    snapshot_dir=snapshot_dir,
                )
                self.results = collect_tenders(driver, wait, self.log)

                if len(self.results) == 0:
                    self.log("INFO: No results after first keyword filter attempt. Retrying once.")
                    # Reset form/page state and retry once.
                    ensure_on_notices(driver, wait)
                    open_search_panel(driver, wait, self.log)
                    search_keyword(driver, wait, keyword)
                    wait_for_result_rows(
                        driver,
                        wait,
                        self.log,
                        attempts=3,
                        base_delay_sec=1.2,
                        snapshot_dir=snapshot_dir,
                    )
                    self.results = collect_tenders(driver, wait, self.log)

                if len(self.results) == 0:
                    # Final fallback: collect baseline rows without keyword filter.
                    self.log(
                        "WARN: search_filter_failed=true; collecting baseline results without filter."
                    )
                    ensure_on_notices(driver, wait)
                    self.results = collect_tenders(driver, wait, self.log)
                    used_fallback = True

                if used_fallback:
                    self.var_search_mode.set("Mode: fallback baseline (search_filter_failed=true)")
                else:
                    self.var_search_mode.set("Mode: filtered")

                self.tree.delete(*self.tree.get_children())
                for row in self.results:
                    self.tree.insert(
                        "",
                        "end",
                        values=(row.index, row.title, row.institution, row.deadline, row.dossier_id),
                    )
            except WebDriverException as exc:
                self.var_search_mode.set("Mode: error")
                self.log(f"ERROR: WebDriver: {exc}")
            except Exception as exc:
                self.var_search_mode.set("Mode: error")
                self.log(f"ERROR: {exc}")

        threading.Thread(target=work, daemon=True).start()

    def on_download_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select one or more tenders.")
            return

        username = (self.var_username.get() or "").strip()
        password = self.var_password.get() or ""

        def work():
            total_started = 0
            try:
                driver, wait = self.ensure_driver()
                for idx, item_id in enumerate(selected, 1):
                    _, title, institution, deadline, dossier_id = self.tree.item(item_id)["values"]
                    self.log(f"DOWNLOAD [{idx}/{len(selected)}] {title} ({institution}) [{deadline}]")
                    ensure_on_notices(driver, wait)
                    open_search_panel(driver, wait, self.log)
                    click_show_for_dossier(driver, wait, dossier_id)
                    click_download_all_in_modal(driver, wait)
                    time.sleep(1.0)

                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])

                    started = handle_download_doc_without_login(driver, self.log)
                    if started == 0 and username and password:
                        if login_on_download_doc(driver, username, password, self.log):
                            try:
                                all_btn = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.ID, "ctl00_publicAccess_btnDownloadAll"))
                                )
                                all_btn.click()
                                time.sleep(1.2)
                            except Exception:
                                pass
                            started = handle_download_doc_without_login(driver, self.log)

                    total_started += started
                self.log(f"DONE: Started downloads: {total_started}")
            except Exception as exc:
                self.log(f"ERROR: Download failed: {exc}")

        threading.Thread(target=work, daemon=True).start()

    def on_export_excel(self):
        if not self.results:
            messagebox.showinfo("No data", "Search first.")
            return
        output = filedialog.asksaveasfilename(
            title="Save results",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="tender-results.xlsx",
        )
        if not output:
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "Tender Results"
        ws.append(["Row", "Title", "Institution", "Deadline", "DossierID"])
        for row in self.results:
            ws.append([row.index, row.title, row.institution, row.deadline, row.dossier_id])
        wb.save(output)
        self.log(f"EXPORTED: {output}")
        if os.name == "nt":
            os.startfile(output)

    def get_profile_data(self) -> dict:
        return {
            "keyword": self.var_keyword.get(),
            "download_dir": self.var_download.get(),
            "headless": self.var_headless.get(),
            "username": self.var_username.get(),
            "password": self.var_password.get(),
        }

    def apply_profile_data(self, data: dict) -> None:
        self.var_keyword.set(data.get("keyword", self.var_keyword.get()))
        self.var_download.set(data.get("download_dir", self.var_download.get()))
        self.var_headless.set(bool(data.get("headless", self.var_headless.get())))
        self.var_username.set(data.get("username", self.var_username.get()))
        self.var_password.set(data.get("password", self.var_password.get()))

    def shutdown(self):
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                pass


class DocumentationFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.var_template = tk.StringVar(value="")
        self.var_output_dir = tk.StringVar(value=str(Path.cwd() / "generated_docs"))
        self.var_output_name = tk.StringVar(value="tender-document.docx")
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Template (.docx):").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.var_template, width=70).grid(row=0, column=1, sticky="we")
        ttk.Button(top, text="Browse...", command=self.choose_template).grid(row=0, column=2, sticky="w", padx=6)

        ttk.Label(top, text="Output folder:").grid(row=1, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.var_output_dir, width=70).grid(row=1, column=1, sticky="we")
        ttk.Button(top, text="Browse...", command=self.choose_output_dir).grid(row=1, column=2, sticky="w", padx=6)

        ttk.Label(top, text="Output file name:").grid(row=2, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.var_output_name, width=40).grid(row=2, column=1, sticky="w")

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(actions, text="Scan placeholders", command=self.scan_placeholders).pack(side="left")
        ttk.Button(actions, text="Generate document", command=self.generate_document).pack(side="left", padx=6)

        ttk.Label(self, text="Values (KEY=value, one per line):").pack(anchor="w", padx=8, pady=(0, 4))
        self.values_text = tk.Text(self, height=18, wrap="none")
        self.values_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.log_text = tk.Text(self, height=8, wrap="word")
        self.log_text.pack(fill="x", padx=8, pady=(0, 8))
        self.log_text.config(state="disabled")

    def log(self, msg: str):
        self.log_text.config(state="normal")
        self.log_text.insert("end", time.strftime("%H:%M:%S  ") + msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def choose_template(self):
        path = filedialog.askopenfilename(
            title="Choose template",
            filetypes=[("Word template", "*.docx")],
        )
        if path:
            self.var_template.set(path)

    def choose_output_dir(self):
        path = filedialog.askdirectory(initialdir=self.var_output_dir.get() or str(Path.cwd()))
        if path:
            self.var_output_dir.set(path)

    def scan_placeholders(self):
        template_path = self.var_template.get().strip()
        if not template_path:
            messagebox.showwarning("Template missing", "Select a .docx template.")
            return
        try:
            placeholders = extract_placeholders_from_docx(template_path)
            self.values_text.delete("1.0", "end")
            for key in placeholders:
                self.values_text.insert("end", f"{key}=\n")
            self.log(f"FOUND placeholders: {len(placeholders)}")
        except Exception as exc:
            self.log(f"ERROR: {exc}")
            messagebox.showerror("Error", str(exc))

    def _parse_values(self) -> dict[str, str]:
        values: dict[str, str] = {}
        raw = self.values_text.get("1.0", "end").strip()
        for line in raw.splitlines():
            if not line.strip():
                continue
            if "=" not in line:
                raise ValueError(f"Invalid line: {line}")
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
        return values

    def generate_document(self):
        template_path = self.var_template.get().strip()
        output_dir = self.var_output_dir.get().strip() or str(Path.cwd() / "generated_docs")
        output_name = self.var_output_name.get().strip() or "tender-document.docx"
        if not template_path:
            messagebox.showwarning("Template missing", "Select a .docx template.")
            return
        try:
            values = self._parse_values()
            output_path = str(Path(output_dir) / output_name)
            render_docx_template(template_path, output_path, values)
            self.log(f"GENERATED: {output_path}")
            messagebox.showinfo("Done", f"Document saved:\n{output_path}")
        except Exception as exc:
            self.log(f"ERROR: {exc}")
            messagebox.showerror("Error", str(exc))

    def get_profile_data(self) -> dict:
        return {
            "template": self.var_template.get(),
            "output_dir": self.var_output_dir.get(),
            "output_name": self.var_output_name.get(),
            "values_text": self.values_text.get("1.0", "end"),
        }

    def apply_profile_data(self, data: dict) -> None:
        self.var_template.set(data.get("template", self.var_template.get()))
        self.var_output_dir.set(data.get("output_dir", self.var_output_dir.get()))
        self.var_output_name.set(data.get("output_name", self.var_output_name.get()))
        self.values_text.delete("1.0", "end")
        self.values_text.insert("1.0", data.get("values_text", ""))


class ProcurementsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Public Procurements App")
        self.geometry("1200x780")
        self.minsize(1000, 680)
        self.var_include_password = tk.BooleanVar(value=False)

        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Button(top, text="Load profile", command=self.load_profile).pack(side="left")
        ttk.Button(top, text="Save profile", command=self.save_profile).pack(side="left", padx=6)
        ttk.Checkbutton(
            top,
            text="Include password in saved profile",
            variable=self.var_include_password,
        ).pack(side="left", padx=(12, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.search_tab = TenderSearchFrame(notebook)
        self.docs_tab = DocumentationFrame(notebook)
        notebook.add(self.search_tab, text="Tender Search")
        notebook.add(self.docs_tab, text="Documentation Builder")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _collect_profile(self) -> dict:
        search_data = self.search_tab.get_profile_data()
        if not self.var_include_password.get():
            search_data["password"] = ""
        return {
            "version": 1,
            "search": search_data,
            "docs": self.docs_tab.get_profile_data(),
            "meta": {
                "password_included": bool(self.var_include_password.get()),
            },
        }

    def _apply_profile(self, data: dict) -> None:
        self.search_tab.apply_profile_data(data.get("search", {}))
        self.docs_tab.apply_profile_data(data.get("docs", {}))

    def save_profile(self):
        path = filedialog.asksaveasfilename(
            title="Save profile",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="procurements-profile.json",
        )
        if not path:
            return
        if self.var_include_password.get():
            proceed = messagebox.askyesno(
                "Confirm password export",
                "You are about to save the password in plain text inside the JSON profile. Continue?",
            )
            if not proceed:
                return
        try:
            profile = self._collect_profile()
            Path(path).write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
            messagebox.showinfo("Saved", f"Profile saved:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def load_profile(self):
        path = filedialog.askopenfilename(
            title="Load profile",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self._apply_profile(data)
            messagebox.showinfo("Loaded", f"Profile loaded:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_close(self):
        self.search_tab.shutdown()
        self.destroy()


if __name__ == "__main__":
    ProcurementsApp().mainloop()
