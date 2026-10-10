# Yoga queue wrapper. Run once from the repo folder (venv is activated here):
#   .\scripts\queue.ps1
# Restarts the queue on any exit except 3 (finished). Leave the window open all weekend.
Set-Location (Join-Path $PSScriptRoot "..")
if (Test-Path ".venv\Scripts\Activate.ps1") { . .\.venv\Scripts\Activate.ps1 }
New-Item -ItemType Directory -Force -Path logs | Out-Null
while ($true) {
    python -u scripts\run_queue.py --laptop thomas 2>&1 | Tee-Object -FilePath logs\queue_thomas.log -Append
    if ($LASTEXITCODE -eq 3) { Write-Host "queue finished"; break }
    $msg = "$(Get-Date) queue exited with $LASTEXITCODE; restarting in 60 s"
    Write-Host $msg; Add-Content logs\queue_thomas.log $msg
    Start-Sleep -Seconds 60
}
