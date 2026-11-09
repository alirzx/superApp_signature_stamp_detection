.PHONY: doctor build model model-verify up down ps logs health test frontend-build

doctor:
	docker compose version
	docker compose --env-file .env config --quiet
build:
	docker compose --env-file .env build model-setup api ui
model:
	docker compose --env-file .env run -T --rm --no-deps model-setup
model-verify:
	docker compose --env-file .env run -T --rm --no-deps --entrypoint python model-setup -m scripts.prepare_model --verify-only
up:
	docker compose --env-file .env up --build -d
ps:
	docker compose --env-file .env ps -a
logs:
	docker compose --env-file .env logs --tail=100 model-setup api ui
health:
	docker compose --env-file .env exec -T api python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/health/ready').read().decode())"
	docker compose --env-file .env exec -T ui wget -q -O - http://127.0.0.1:8080/healthz
test:
	PYTHONPATH=backend python -m pytest backend/tests -q
frontend-build:
	cd frontend && npm install && npm run build
down:
	docker compose --env-file .env down
