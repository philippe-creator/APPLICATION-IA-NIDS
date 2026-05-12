# Script de lancement pour Démonstration SCCT & NIDS Architecture Microservices
Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

Write-Host "--- INITIALISATION DE L'ÉCOSYSTÈME CYBER-IA ---"

# 1. Nettoyage des processus
Write-Host "[1/4] Arrêt des services existants..."
foreach ($port in @(8000, 9000)) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
    if ($proc) { Stop-Process -Id $proc.Id -Force }
  }
}
Start-Sleep -Seconds 1

# 2. Lancement des serveurs
Write-Host "[2/4] Lancement du Serveur Admin/NIDS (Port 9000)..."
Start-Process ".\.venv\Scripts\python" -ArgumentList "-m uvicorn admin_main:app --port 9000" -WindowStyle Hidden
Start-Sleep -Seconds 3

Write-Host "[3/4] Lancement de l'Application Métier (Port 8000)..."
Start-Process ".\.venv\Scripts\python" -ArgumentList "-m uvicorn app_main:app --port 8000" -WindowStyle Hidden
Start-Sleep -Seconds 3

# 3. Ouverture des navigateurs avec Chrome
Write-Host "[4/4] Ouverture de l'interface dans Google Chrome..."
Start-Process "chrome.exe" -ArgumentList "http://127.0.0.1:8000/app"
Start-Sleep -Seconds 1
Start-Process "chrome.exe" -ArgumentList "http://127.0.0.1:9000/dashboard"

Write-Host "`n--- SYSTÈME PRÊT ---"
Write-Host "L'App est sur le port 8000, l'Admin sur le port 9000."
