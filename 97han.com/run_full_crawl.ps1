$logFile = "crawl_progress.log"
$date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$date] Starting Comprehensive Full Site Crawl with 40 threads..." | Out-File -FilePath $logFile -Append -Encoding utf8

function Run-Task {
    param($name, $cmd, $args)
    $msg = "[$([DateTime]::Now)] Starting $name..."
    Write-Host $msg
    $msg | Out-File -FilePath $logFile -Append -Encoding utf8
    
    & $cmd $args | ForEach-Object {
        $line = $_
        Write-Host $line
        $line | Out-File -FilePath $logFile -Append -Encoding utf8
    }
    
    $msg = "[$([DateTime]::Now)] Finished $name."
    Write-Host $msg
    $msg | Out-File -FilePath $logFile -Append -Encoding utf8
}

# 1. 电影 (CID=1, 共1027页)
Run-Task "Movies (CID=1)" "python" @("main.py", "movie", "--start-page", "1", "--threads", "40")

# 2. 电视剧 (CID=2, 共549页)
Run-Task "TV Series (CID=2)" "python" @("main.py", "tv", "--cid", "2", "--category-name", "电视剧", "--start-page", "1", "--threads", "40")

# 3. 综艺 (CID=3, 共111页)
Run-Task "Variety Shows (CID=3)" "python" @("main.py", "tv", "--cid", "3", "--category-name", "综艺", "--start-page", "1", "--threads", "40")

# 4. 动漫 (CID=4, 共238页)
Run-Task "Anime (CID=4)" "python" @("main.py", "tv", "--cid", "4", "--category-name", "动漫", "--start-page", "1", "--threads", "40")

# 5. 短剧 (CID=30, 共319页)
Run-Task "Short Drama (CID=30)" "python" @("main.py", "tv", "--cid", "30", "--category-name", "短剧", "--start-page", "1", "--threads", "40")

# 6. 伦理MV (CID=36, 共177页)
Run-Task "Ethics MV (CID=36)" "python" @("main.py", "tv", "--cid", "36", "--category-name", "伦理MV", "--start-page", "1", "--threads", "40")

# Export
Run-Task "Export" "python" @("main.py", "export", "--format", "excel")

"[$([DateTime]::Now)] All Tasks Completed." | Out-File -FilePath $logFile -Append -Encoding utf8
