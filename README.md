# Magento-bot

An intelligent AI-powered bot system for Magento e-commerce platform that combines data engineering and agentic AI capabilities.

## Project Overview

This project consists of two main components:

1. **Data Engineering Pipeline**
   - Apache Airflow for ETL orchestration
   - Multiple data sources integration (Magento, PDFs, CRM)
   - Vector database storage using Qdrant
   - MongoDB for structured data and session management

2. **Agentic AI System**
   - Built with LangGraph and LangChain
   - Multiple specialized agents for different data domains
   - FastAPI backend with streaming support
   - State management and persistence

## Architecture

### Data Sources
- Magento Order & Inventory Data (API)
- PDF Documents (local/S3)
- Blogs & Tickets (CMS/file-based)

### Storage
- MongoDB: Metadata and session data
- Qdrant Vector Databases:
  - order_inventory_qdrant
  - pdf_qdrant
  - crm_qdrant

## Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Make (for Makefile usage)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/magento-bot.git
cd magento-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start the services:
```bash
docker-compose up -d
```

## Usage

### Starting the API Server
```bash
make run-api
```

### Running Airflow Tasks
```bash
make run-airflow
```

### Running Tests
```bash
make test
```

## Project Structure

```
magento-bot/
├── agentic_ai/          # AI Agents and orchestration
├── api/                 # FastAPI application
├── data_pipeline/       # Airflow DAGs and scripts
├── configs/            # Configuration files
├── docker/             # Docker-related files
└── tests/              # Test suite
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
