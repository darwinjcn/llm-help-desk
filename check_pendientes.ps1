# Verifica los 2 pendientes del proyecto en tu máquina Windows:
#   1) Que dice qwen-helpdesk (para decidir si se conserva o se elimina)
#   2) Que backend/reports/latest.json exista y sea legible (volumen de reportes OK)
# Uso: ejecutar desde la carpeta raiz del proyecto ->  .\check_pendientes.ps1

$ErrorActionPreference = "Continue"

Write-Host "=== 1. Modelos instalados en Ollama (uso de disco) ===" -ForegroundColor Cyan
ollama list

Write-Host "`n=== 2. Detalle de qwen-helpdesk (Modelfile / prompt de sistema) ===" -ForegroundColor Cyan
ollama show qwen-helpdesk

Write-Host "`n=== 3. Reporte de evals en tu carpeta local ===" -ForegroundColor Cyan
$ruta = "backend\reports\latest.json"
if (Test-Path $ruta) {
    $r = Get-Content $ruta -Raw | ConvertFrom-Json
    Write-Host "OK: $ruta existe y es legible" -ForegroundColor Green
    Write-Host ("  Fecha:                  {0}" -f $r.fecha)
    Write-Host ("  Modelo triage:          {0}" -f $r.modelo_triage)
    Write-Host ("  Muestras:               {0}" -f $r.n_muestras)
    Write-Host ("  Precision categoria:    {0}" -f $r.precision_categoria)
    Write-Host ("  Precision prioridad:    {0}" -f $r.precision_prioridad)
    Write-Host ("  Tasa validacion JSON:   {0}" -f $r.tasa_validacion_json)
    Write-Host ("  Recall RAG top-3:       {0}" -f $r.recall_rag_top3)
    Write-Host ("  Latencia p50/p95 (ms):  {0} / {1}" -f $r.latencia_ms.p50, $r.latencia_ms.p95)
} else {
    Write-Host "NO existe $ruta" -ForegroundColor Yellow
    Write-Host "Si ya corriste 'make evals' antes del rebuild, el volumen se aplico despues."
    Write-Host "Solucion:"
    Write-Host "    docker compose up -d --build   # aplica el volumen ./backend/reports"
    Write-Host "    make evals                     # regenera el reporte"
}

Write-Host "`n=== 4. Criterio de decision para qwen-helpdesk ===" -ForegroundColor Cyan
Write-Host "La app SOLO usa qwen2.5:3b-instruct y nomic-embed-text (backend/app/config.py)."
Write-Host "- Si el Modelfile mostrado arriba no trae un SYSTEM prompt que quieras conservar:"
Write-Host "      ollama rm qwen-helpdesk      # libera ~2 GB"
Write-Host "- Si trae un prompt util, portalo a un Modelfile versionado en el repo"
Write-Host "  (backend/models/Modelfile) y referencia el modelo en .env, no en config por defecto."
