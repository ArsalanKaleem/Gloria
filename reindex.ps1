# reindex.ps1 - full corpus rebuild including the backend restart.
# The restart is REQUIRED: the API caches a Chroma handle at startup and
# will keep serving stale results without it.
$ErrorActionPreference = "Stop"
Write-Host "Clearing caches..." -ForegroundColor Cyan
docker compose exec backend sh -c "rm -f /app/data/processed/*.json"
docker compose exec backend sh -c "rm -rf /app/data/chroma/*"
Write-Host "Ingesting..." -ForegroundColor Cyan
docker compose exec backend python -m scripts.ingest_pdfs
Write-Host "Indexing..." -ForegroundColor Cyan
docker compose exec backend python -m scripts.index_documents
Write-Host "Restarting backend (drops stale Chroma handle)..." -ForegroundColor Cyan
docker compose restart backend
Start-Sleep -Seconds 20
Write-Host "Done." -ForegroundColor Green
