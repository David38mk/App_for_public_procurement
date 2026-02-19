# Public Procurements App (MVP)

## What this app does
- Searches tenders on `e-nabavki.gov.mk` (PublicAccess) from a keyword.
- Lets you select results and trigger download of available documents.
- Supports optional username/password login on download pages when public links are not enough.
- Builds tender documents from `.docx` templates with placeholders like `{{CLIENT_NAME}}`.
- Handles placeholders that are split across multiple Word runs.
- Saves and loads working profiles (`.json`) for both tabs.

## Run
1. Install Python 3.10+.
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Start:
```bash
python app/main.py
```

## Notes
- Chrome must be installed locally.
- The app auto-downloads compatible ChromeDriver via `webdriver-manager`.
- Template generation works best with simple placeholders (no spaces), example: `{{CONTRACT_SUBJECT}}`.
- Password is excluded from saved profiles by default.
- You can explicitly enable password saving via the checkbox in the top bar.
