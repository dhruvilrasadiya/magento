.PHONY: setup run-api run-airflow test lint clean

# Setup project
setup:
	python -m venv venv
	.\venv\Scripts\activate && pip install -r requirements.txt

# Run FastAPI server
run-api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run Airflow webserver
run-airflow:
	docker-compose up airflow

# Run tests
test:
	pytest tests/ -v

# Run linting
lint:
	black . --exclude '(/env/)'
	isort . --skip-glob='*/env/*'
	mypy . --exclude 'env'

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Create initial database
init-db:
	docker-compose up -d mongodb
	docker-compose up -d data_qdrant

# Start all services
start-all: docker-up
	@echo "Starting all services..."
	@echo "Airflow UI available at: http://localhost:8080"
	@echo "FastAPI UI available at: http://localhost:8000/docs"
	@echo "MongoDB running on: localhost:27017"
	@echo "Qdrant instances running on: 6333, 6334, 6335"
