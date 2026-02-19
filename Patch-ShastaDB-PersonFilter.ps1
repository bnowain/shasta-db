# Patch-ShastaDB-PersonFilter.ps1
# Run from: E:\0-Automated-Apps\Shasta-DB
# This patches the UI to use person name (optional) instead of person_id (int) to avoid 422s.

param(
  [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

function Backup-File([string]$Path) {
  if (!(Test-Path $Path)) { throw "Missing file: $Path" }
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $bak = "$Path.bak_$ts"
  Copy-Item $Path $bak
  return $bak
}

function Replace-InFile([string]$Path, [scriptblock]$Transform) {
  $bak = Backup-File $Path
  $txt = Get-Content $Path -Raw -Encoding UTF8
  $new = & $Transform $txt

  if ($new -eq $txt) {
    Write-Host "[WARN] No changes made to $Path (pattern not found?)"
  } else {
    Set-Content -Path $Path -Value $new -Encoding UTF8
    Write-Host "[OK] Patched $Path (backup: $bak)"
  }
}

$mainPy     = Join-Path $ProjectRoot "app\main.py"
$uiHtml     = Join-Path $ProjectRoot "app\templates\ui.html"
$fileList   = Join-Path $ProjectRoot "app\templates\partials\file_list.html"

# --- 1) Patch ui.html: Person input becomes name-based ---
Replace-InFile $uiHtml {
  param($t)

  # Replace the whole Person row block (old person_id numeric field)
  $pattern = [regex]::Escape('<div class="row">') + '\s*<label>Person</label>.*?</div>'
  $regex = New-Object System.Text.RegularExpressions.Regex($pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)

  $replacement = @'
<div class="row">
  <label>Person</label>
  <input name="person" id="person" type="text" placeholder="Clint Curtis (optional)" />
  <small class="hint">Type a name (partial match ok). Leave blank for all.</small>
</div>
'@

  if ($regex.IsMatch($t)) {
    $t = $regex.Replace($t, $replacement, 1)
  } else {
    # Fallback: if the exact block isn't found, do a simpler replacement on the input name/id if present
    $t = $t -replace 'name="person_id"', 'name="person"'
    $t = $t -replace 'id="personId"', 'id="person"'
    $t = $t -replace 'type="number"', 'type="text"'
    $t = $t -replace 'Person ID \(for now\)', 'Person'
  }

  $t
}

# --- 2) Patch main.py: /ui/list uses person: str and filters by Person.name ilike ---
Replace-InFile $mainPy {
  param($t)

  # A) ui_list signature: person_id -> person
  $t = $t -replace 'person_id:\s*int\s*\|\s*None\s*=\s*None,', 'person: str = "",'
  $t = $t -replace 'person_id:\s*str\s*=\s*""\s*,', 'person: str = "",'

  # B) _apply_filters signature: person_id -> person
  $t = $t -replace 'def _apply_filters\(([^)]*?)person_id:\s*int\s*\|\s*None([^)]*?)\):', 'def _apply_filters($1person: str$2):'
  $t = $t -replace 'def _apply_filters\(([^)]*?)person_id([^)]*?)\):', 'def _apply_filters($1person$2):'

  # C) Replace person filter block inside _apply_filters
  # Replace the old block if present
  $oldBlockRegex = New-Object System.Text.RegularExpressions.Regex(
@'
if\s+person_id:\s*
\s*stmt\s*=\s*stmt\.join\(InstancePerson,\s*InstancePerson\.instance_id\s*==\s*Instance\.id\)\.where\(InstancePerson\.person_id\s*==\s*person_id\)
'@,
    [System.Text.RegularExpressions.RegexOptions]::Singleline
  )

  $newBlock = @'
if person and person.strip():
        # filter instances linked to any person whose name matches (case-insensitive)
        stmt = (
            stmt.join(InstancePerson, InstancePerson.instance_id == Instance.id)
                .join(Person, Person.id == InstancePerson.person_id)
                .where(Person.name.ilike(f"%{person.strip()}%"))
        )
'@

  if ($oldBlockRegex.IsMatch($t)) {
    $t = $oldBlockRegex.Replace($t, $newBlock, 1)
  } else {
    # If old block isn't found (maybe already partially edited), try to remove any remaining person_id join filter
    $t = $t -replace 'if\s+person_id\s*:\s*.*?hide_junk', ('if person and person.strip():' + "`r`n" + $newBlock + "`r`n" + '    if hide_junk')
  }

  # D) ui_list: call _apply_filters(...) should pass person, not person_id
  $t = $t -replace '_apply_filters\(([^)]*?),\s*person_id\s*,\s*hide_junk\)', '_apply_filters($1, person, hide_junk)'

  # E) ui_list context: expose person (optional)
  $t = $t -replace '"person_id"\s*:\s*person_id\s*,', '"person": person,'
  $t = $t -replace '"person_id"\s*:\s*person_id_int\s*,', '"person": person,'

  $t
}

# --- 3) Patch file_list.html: remove person_id query-string preservation (hx-include already preserves filters) ---
Replace-InFile $fileList {
  param($t)

  # Remove conditional person_id fragments in hx-get URLs (Prev/Next)
  $t = $t -replace '\{%\s*if\s+person_id\s*%\}&person_id=\{\{\s*person_id\s*\}\}\{%\s*endif\s*%\}', ''
  $t = $t -replace '\{%\s*if\s+person\s*%\}&person=\{\{.*?\}\}\{%\s*endif\s*%\}', ''

  $t
}

Write-Host ""
Write-Host "Done. Restart uvicorn (or let --reload pick up changes):" -ForegroundColor Cyan
Write-Host "  uvicorn app.main:app --reload --port 8844"
Write-Host "Then open: http://127.0.0.1:8844/ui"
