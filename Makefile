MODELO_TRIAGE ?= qwen2.5:3b-instruct
MODELO_EMBED ?= nomic-embed-text

.PHONY: up down logs models seed limpiar evals benchmark health

up:            ## Levanta el stack (postgres, backend, frontend; Ollama es nativo)
	docker compose up -d --build

down:          ## Detiene el stack
	docker compose down

logs:          ## Sigue los logs de todos los servicios
	docker compose logs -f

models:        ## Muestra cómo descargar los modelos (Ollama corre nativo en el host)
	@echo "Ejecuta en PowerShell (Ollama es nativo, no está en Docker):"
	@echo "    ollama pull $(MODELO_TRIAGE)"
	@echo "    ollama pull $(MODELO_EMBED)"

seed:          ## Carga datos de demostración (usuarios, KB, tickets)
	docker compose exec backend python scripts/seed_demo.py

limpiar:       ## Elimina TODOS los tickets demo (conserva usuarios y KB)
	docker compose exec backend python scripts/limpiar_tickets.py --si

evals:         ## Corre la suite de evaluación del agente
	docker compose exec backend python scripts/run_evals.py

benchmark:     ## Benchmark de modelos de triage (pásale --modelos si quieres)
	docker compose exec backend python scripts/benchmark_modelos.py

health:        ## Verifica el estado del backend
	curl -s http://localhost:8001/api/health
