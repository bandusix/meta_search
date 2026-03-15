# PowerShell Script to Push to GitHub using PAT
$gitPath = "C:\Users\Alex\AppData\Local\atom\app-1.39.1\resources\app.asar.unpacked\node_modules\dugite\git\cmd\git.exe"

# 1. Set Git Alias
Set-Alias -Name git -Value $gitPath -Scope Global -ErrorAction SilentlyContinue

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Meta Search - GitHub Push Helper (Token Mode)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# 2. Get User Token
Write-Host "GitHub no longer supports password authentication." -ForegroundColor Yellow
Write-Host "Please enter your Personal Access Token (PAT)." -ForegroundColor Yellow
Write-Host "If you don't have one, create it here: https://github.com/settings/tokens" -ForegroundColor White
Write-Host "(Select 'repo' scope when creating the token)" -ForegroundColor White
Write-Host ""
$token = Read-Host "Paste your Token here (hidden)" -AsSecureString
$tokenPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token))

if (-not $tokenPlain) {
    Write-Host "[Error] Token cannot be empty." -ForegroundColor Red
    exit
}

# 3. Configure Remote with Token
$repoUrl = "https://bandusix:$tokenPlain@github.com/bandusix/meta_search.git"
Write-Host ""
Write-Host "[Info] Configuring remote authentication..." -ForegroundColor Cyan

# Remove existing origin to be safe
& git remote remove origin 2>$null
& git remote add origin $repoUrl

# 4. Push
Write-Host "[Action] Pushing to GitHub..." -ForegroundColor Cyan
try {
    & git push -u origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "==================================================" -ForegroundColor Green
        Write-Host "   SUCCESS! Project pushed to GitHub." -ForegroundColor Green
        Write-Host "   View at: https://github.com/bandusix/meta_search" -ForegroundColor Green
        Write-Host "==================================================" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[Error] Push failed." -ForegroundColor Red
        Write-Host "Please check:"
        Write-Host "1. Did you create the empty repository 'meta_search' on GitHub?"
        Write-Host "2. Is the token valid and has 'repo' permissions?"
    }
} catch {
    Write-Host "[Exception] $_" -ForegroundColor Red
}

# Clean up remote URL to remove token from config (security)
& git remote remove origin
& git remote add origin "https://github.com/bandusix/meta_search.git"

Write-Host ""
Write-Host "Press Enter to exit..."
Read-Host
