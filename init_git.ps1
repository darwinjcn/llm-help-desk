# Inicializa el repositorio y hace el primer push a GitHub.
# Uso:  .\init_git.ps1 -RepoUrl "https://github.com/TU-USUARIO/llm-help-desk.git"
# Si aún no creaste el repo en GitHub, el script hace init + commit y te dice qué falta.

param(
    [string]$RepoUrl = ""
)

$ErrorActionPreference = "Stop"

# 1. Verificar que git está instalado
try { git --version | Out-Null } catch {
    Write-Error "Git no está instalado. Descárgalo de https://git-scm.com/download/win"
}

# 2. Identidad (solo pide si no está configurada)
if (-not (git config user.name)) { git config --global user.name "Tu Nombre" }
if (-not (git config user.email)) { git config --global user.email "tu-email@example.com" }

# 3. Inicializar y primer commit (asunto + cuerpo, cada -m es un parrafo)
if (-not (Test-Path ".git")) { git init }
git add .
git commit `
    -m "Help desk con agentes IA locales: RAG, human-in-the-loop y evals medibles" `
    -m "Backend FastAPI con RBAC (cliente/agente/admin), JWT y auditoria completa en agent_runs." `
    -m "Triage y resolucion con Qwen 2.5 3B via Ollama en el host: salidas JSON validadas con Pydantic, reglas de negocio deterministas sobre el modelo, anti-alucinacion por citas [KB-XXX] y textguard contra bucles." `
    -m "RAG con pgvector filtrado por la categoria del triage: recall@3 medido de 0.75 a 1.0 con la suite de evals reproducible (make evals)." `
    -m "Frontend React/TypeScript (tickets, base de conocimiento, dashboard IA) y stack en Docker Compose con Ollama nativo en host (<6 GB RAM)."

# 4. Push si dieron la URL
if ($RepoUrl -ne "") {
    git branch -M main
    if (git remote | Select-String -Quiet "^origin$") { git remote set-url origin $RepoUrl }
    else { git remote add origin $RepoUrl }
    git push -u origin main
    Write-Host "`nListo: codigo publicado en $RepoUrl" -ForegroundColor Green
} else {
    Write-Host "`nCommit local listo. Para publicar:" -ForegroundColor Yellow
    Write-Host "  1. Crea un repo VACIO en github.com (sin README ni .gitignore)"
    Write-Host "  2. Ejecuta de nuevo:  .\init_git.ps1 -RepoUrl `"https://github.com/TU-USUARIO/llm-help-desk.git`""
}
