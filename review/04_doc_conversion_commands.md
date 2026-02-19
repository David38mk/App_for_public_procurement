# DOC to DOCX Conversion Commands (Per File)

## Scope
- Convert these 3 legacy files:
- `Упатства\Zaednicki_poimnik_za_JN.doc`
- `модели на тендерска документација\Отворена постапка\Model_Otvorena-postapka_usoglasena-so-izmeni-na-ZJN-14-25-1.doc`
- `модели на тендерска документација\Поедноставена отворена постапка\POP-Izmena-ZJN-14_25-1.doc`

## Pre-step: Backup
```powershell
$root = 'C:\Users\rabota\Desktop\App for public procurements'
$bk = Join-Path $root ('review\\doc_backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $bk -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'Упатства\\Zaednicki_poimnik_za_JN.doc') -Destination $bk -Force
Copy-Item -LiteralPath (Join-Path $root 'модели на тендерска документација\\Отворена постапка\\Model_Otvorena-postapka_usoglasena-so-izmeni-na-ZJN-14-25-1.doc') -Destination $bk -Force
Copy-Item -LiteralPath (Join-Path $root 'модели на тендерска документација\\Поедноставена отворена постапка\\POP-Izmena-ZJN-14_25-1.doc') -Destination $bk -Force
```

## Option A: Microsoft Word (recommended)
- Open each `.doc` in Word.
- `File -> Save As -> Word Document (*.docx)`.
- Save in the same folder with the same base name.

Expected targets:
- `Упатства\Zaednicki_poimnik_za_JN.docx`
- `модели на тендерска документација\Отворена постапка\Model_Otvorena-postapka_usoglasena-so-izmeni-na-ZJN-14-25-1.docx`
- `модели на тендерска документација\Поедноставена отворена постапка\POP-Izmena-ZJN-14_25-1.docx`

## Option B: Word COM script (works only in an interactive Windows logon session)
```powershell
$root = 'C:\Users\rabota\Desktop\App for public procurements'
$docs = @(
  (Join-Path $root 'Упатства\\Zaednicki_poimnik_za_JN.doc'),
  (Join-Path $root 'модели на тендерска документација\\Отворена постапка\\Model_Otvorena-postapka_usoglasena-so-izmeni-na-ZJN-14-25-1.doc'),
  (Join-Path $root 'модели на тендерска документација\\Поедноставена отворена постапка\\POP-Izmena-ZJN-14_25-1.doc')
)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$wdFormatXMLDocument = 12
try {
  foreach($src in $docs){
    $doc = $word.Documents.Open($src)
    $dst = [System.IO.Path]::ChangeExtension($src, '.docx')
    $doc.SaveAs([ref]$dst, [ref]$wdFormatXMLDocument)
    $doc.Close()
  }
} finally {
  $word.Quit()
}
```

## Validation Checklist (per file)
- Page count matches source.
- Tables keep borders/alignment.
- Header/footer and numbering are intact.
- Signature/stamp placeholders unchanged.
- Random paragraph spot-checks pass.

## Post-conversion policy
- Keep original `.doc` for 30 days in archive.
- Mark `.docx` as canonical in `review\index.csv` once validated.
