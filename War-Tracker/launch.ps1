# launch.ps1 - Antigravity Launcher
Write-Host "🚀 Initializing Antigravity Launch Sequence..." -ForegroundColor Cyan

# 1. Check Redis
Write-Host "   Checking for Redis..." -NoNewline
try {
    $redis = Get-Command "redis-server" -ErrorAction SilentlyContinue
    if ($redis) {
        Write-Host " Found (System Path)" -ForegroundColor Green
        # Optional: Start it if not running?
    } else {
        $docker = Get-Command "docker" -ErrorAction SilentlyContinue
        if ($docker) {
             # Check if container running
             $cont = docker ps -q -f name=redis-server
             if ($cont) {
                 Write-Host " Found (Docker Container)" -ForegroundColor Green
             } else {
                 Write-Host " Starting Docker Redis..." -ForegroundColor Yellow
                 docker start redis-server
             }
        } else {
            Write-Host " MISSING!" -ForegroundColor Red
            Write-Host "   ⚠️  CRITICAL: Redis is not detected." -ForegroundColor Red
            Write-Host "   Please install Memurai (https://www.memurai.com/) or run Redis in Docker."
            Write-Host "   The system will try to start, but workers will fail to connect."
            Start-Sleep -Seconds 3
        }
    }
} catch {
    Write-Host " Error checking Redis." -ForegroundColor Red
}

# 2. Define Python Path (Hardcoded to avoid activation issues)
$VENV_PYTHON = ".\venv\Scripts\python.exe"
$CELERY = ".\venv\Scripts\celery.exe"

if (-not (Test-Path $VENV_PYTHON)) {
    Write-Host "   ❌ Virtual Environment not found at .\venv" -ForegroundColor Red
    exit 1
}

# 3. Start Celery Worker (New Window)
Write-Host "   Starting Celery Worker (The Muscle)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '$CELERY' -A celery_app.celery worker --loglevel=info --pool=solo"

# 4. Start Scraper (New Window)
Write-Host "   Starting Ingestion Engine (The Brain)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '$VENV_PYTHON' ingest.py 2011"

Write-Host "✅ Launch Command Sent. Check the new windows!" -ForegroundColor Cyan
