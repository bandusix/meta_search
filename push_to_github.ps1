# PowerShell Script to Push to GitHub
$gitPath = "C:\Users\Alex\AppData\Local\atom\app-1.39.1\resources\app.asar.unpacked\node_modules\dugite\git\cmd\git.exe"

# 1. Set Git Alias
Set-Alias -Name git -Value $gitPath -Scope Global -ErrorAction SilentlyContinue

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Meta Search - GitHub Push Helper" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# 2. Check Remote
$remotes = & git remote -v
if (-not $remotes) {
    Write-Host "[Info] Adding remote origin..." -ForegroundColor Yellow
    & git remote add origin https://github.com/bandusix/meta_search.git
} else {
    Write-Host "[Info] Remote origin already exists:" -ForegroundColor Green
    $remotes
}

Write-Host ""
Write-Host "[Action] Attempting to push to GitHub..." -ForegroundColor Cyan
Write-Host "If a GitHub login window appears, please sign in." -ForegroundColor Yellow
Write-Host ""

# 3. Push
try {
    & git push -u origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[Success] Code successfully pushed to https://github.com/bandusix/meta_search" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[Error] Push failed." -ForegroundColor Red
        Write-Host "Possible reasons:"
        Write-Host "1. The repository 'meta_search' does not exist on your GitHub account."
        Write-Host "   -> Go to https://github.com/new and create it (do not initialize with README)."
        Write-Host "2. Authentication failed or was cancelled."
        Write-Host "3. Network issues."
    }
} catch {
    Write-Host "[Exception] $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press Enter to exit..."
Read-Host
