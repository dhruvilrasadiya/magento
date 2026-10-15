# Magento Bot - Technical Documentation

## Project Overview

Magento Bot is an intelligent AI-powered system for Magento e-commerce platforms that combines advanced data engineering with agentic AI capabilities. The system provides automated data processing, intelligent query handling, and comprehensive business analytics through a multi-agent architecture.

### Key Components
- **Data Engineering Pipeline**: Apache Airflow-based ETL orchestration
- **Agentic AI System**: LangGraph and LangChain-powered multi-agent framework
- **API Backend**: FastAPI with streaming support and authentication
- **Frontend**: React-based user interface
- **Storage**: MongoDB for structured data, Qdrant for vector embeddings

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  Data Pipeline  │    │   AI Agents     │
│                 │    │                 │    │                 │
│ • Magento API   │───▶│ • Apache Airflow│───▶│ • Master Agent  │
│ • DGE API       │    │ • ETL Scripts   │    │ • Product Agent │
│ • PDF Files     │    │ • Data Validation│    │ • Order Agent   │
│ • Customer Data │    │                 │    │ • Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Storage      │    │   API Backend   │    │    Frontend     │
│                 │    │                 │    │                 │
│ • MongoDB       │◀───│ • FastAPI       │◀───│ • React App     │
│ • Qdrant Vector │    │ • Authentication│    │ • Chat Interface│
│ • File Storage  │    │ • Session Mgmt  │    │ • User Dashboard│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Contributors

- **Niral Patel** - Lead Developer & Architect
- **Smit Patel** - Backend Developer & Data Engineer  
- **pratik.jadav** - Frontend Developer & UI/UX
- **get** - Data Pipeline Developer

---

# Commit-wise Technical Documentation

## Phase 1: Foundation & Initial Setup (April 2025)

### Commit: 81b8e70 - Initial commit
**Author:** Niral Patel  
**Date:** 2025-04-14  
**Message:** Initial commit

**Summary of Changes:**
- Established the foundational architecture for the agentic AI system
- Created core directory structure with separation of concerns
- Implemented initial agent framework with specialized agents

**Technical Details:**
- **Agents Created:**
  - `CombinerAgent`: Consolidates responses from multiple agents
  - `CRMAgent`: Handles customer relationship management queries
  - `InventoryAgent`: Manages inventory-related operations
  - `MasterAgent`: Central orchestrator for query routing
  - `OrderAgent`: Processes order-related queries
  - `PDFAgent`: Handles document processing and extraction

- **Infrastructure Setup:**
  - Docker containerization with separate containers for API and Airflow
  - Apache Airflow configuration for data pipeline orchestration
  - Qdrant vector database setup for embeddings storage
  - MongoDB integration for structured data persistence

- **API Framework:**
  - FastAPI backend with modular route structure
  - User session management and authentication scaffolding
  - Message schema definitions for chat functionality
  - Database abstraction layers for chat and user data

**Key Files Added:**
```
agentic_ai/
├── agents/          # AI agent implementations
├── orchestrator/    # Agent coordination logic
├── state/          # State management
└── utils/          # Utility functions

api/
├── database/       # Database models and connections
├── routes/         # API endpoint definitions
└── schemas/        # Data validation schemas

data_pipeline/
├── dags/           # Airflow DAG definitions
├── scripts/        # ETL processing scripts
└── utils/          # Pipeline utilities
```

**Design Decisions:**
- Modular agent architecture for scalability and maintainability
- Separation of data pipeline from API services
- Vector database choice (Qdrant) for semantic search capabilities
- FastAPI for high-performance async API handling

---

### Commit: 4901e84 - updateuser module
**Author:** Smit Patel  
**Date:** 2025-04-16  
**Message:** updateuser module

**Summary of Changes:**
- Enhanced user management functionality
- Improved user data models and validation
- Added user-specific configuration options

**Technical Details:**
- Extended user schema with additional fields
- Implemented user preference management
- Added validation layers for user data integrity

---

### Commit: 570634a - Order initial pipeline ready
**Author:** Niral Patel  
**Date:** 2025-04-17  
**Message:** Order initial pipeline ready

**Summary of Changes:**
- Implemented comprehensive order data processing pipeline
- Created dedicated Airflow DAG for order management
- Established order data models and database schemas

**Technical Details:**
- **New Components:**
  - `order_dag.py`: Airflow DAG for order data processing
  - `orders.py`: Database model definitions for order entities
  - Order data fetching and preparation scripts

- **Pipeline Features:**
  - Automated order data extraction from Magento API
  - Data transformation and validation processes
  - Vector embedding generation for semantic search
  - Integration with Qdrant for order data storage

- **Removed Legacy Components:**
  - Deprecated `order_inventory_dag.py` in favor of specialized DAGs
  - Cleaned up obsolete scripts and sample data files

**Key Improvements:**
- Structured approach to order data management
- Improved data quality through validation pipelines
- Enhanced search capabilities through vector embeddings

---

### Commit: 04b74ba - Update Agentic AI code master / order agent updated
**Author:** Niral Patel  
**Date:** 2025-04-17  
**Message:** Update Agentic AI code master / order agent updated

**Summary of Changes:**
- Enhanced agent collaboration and communication
- Improved order data processing with metadata filtering
- Upgraded orchestration system with session management

**Technical Details:**
- **Agent Enhancements:**
  - `CombinerAgent`: Improved response consolidation logic
  - `MasterAgent`: Enhanced query analysis and task delegation
  - `OrderAgent`: Added metadata filtering for precise vector searches

- **Orchestration Improvements:**
  - Session ID propagation throughout agent workflow
  - Enhanced state management with metadata support
  - Improved agent communication protocols

- **Data Processing:**
  - Ollama embeddings integration for vector generation
  - Metadata-based filtering for improved search accuracy
  - Enhanced order data preparation and validation

**Architecture Impact:**
- Better separation of concerns between agents
- Improved data flow and state management
- Enhanced search precision through metadata filtering

---

## Phase 2: User Management & Product Integration (April-May 2025)

### Commit: 90a4b61 - update session management and product pipeline
**Author:** Smit Patel
**Date:** 2025-04-25
**Message:** update session management and product pipelinw

**Summary of Changes:**
- Introduced comprehensive product data management system
- Enhanced session management with advanced features
- Integrated new ProductAgent for product-related queries

**Technical Details:**
- **New Agent:** `ProductAgent` for handling product-specific queries
- **Product Pipeline:**
  - `product_dag.py`: Dedicated Airflow DAG for product data processing
  - Product data fetching from Magento API with pagination
  - Vector embedding generation for product search capabilities
  - Integration with Qdrant `product_data` collection

- **Session Management Enhancements:**
  - Session listing and retrieval functionality
  - Session renaming capabilities
  - Improved session metadata handling

- **Configuration Updates:**
  - Qdrant configuration extended for product data
  - LLM configuration updates for multi-collection support
  - Ollama embeddings integration

**Key Features:**
- Product search and recommendation capabilities
- Enhanced user session experience
- Scalable product data processing pipeline

---

### Commit: 857ffa1 - Updated User Management
**Author:** Smit Patel
**Date:** 2025-04-30
**Message:** Updatet User Management

**Summary of Changes:**
- Implemented comprehensive JWT-based authentication system
- Added user creation, listing, and management endpoints
- Enhanced security with authentication middleware

**Technical Details:**
- **Authentication System:**
  - JWT token generation and validation
  - Secure user registration and login endpoints
  - Password hashing and validation
  - Refresh token mechanism

- **API Security:**
  - Protected endpoints with authentication middleware
  - User-specific data access controls
  - Session-based authorization

- **Database Updates:**
  - Enhanced ChatSession model with name field
  - User data validation and schema improvements
  - Secure user data storage practices

**Security Features:**
- Token-based authentication
- Protected API endpoints
- User data encryption and validation

---

### Commit: 9cf8fb0 - Refine code
**Author:** Niral Patel
**Date:** 2025-05-01
**Message:** Refine code

**Summary of Changes:**
- Migrated from Ollama to OpenAI for improved performance
- Enhanced configuration management with environment variables
- Improved database connection handling

**Technical Details:**
- **LLM Migration:**
  - Switched from Ollama to OpenAI GPT models
  - Updated embedding generation to use OpenAI
  - Improved model performance and reliability

- **Configuration Management:**
  - Environment variable integration for Qdrant configuration
  - MongoDB connection string externalization
  - Improved security through configuration externalization

- **Code Refinements:**
  - Removed deprecated Qdrant configuration files
  - Cleaned up unused dependencies and imports
  - Enhanced error handling and logging

**Performance Improvements:**
- Better model response quality with OpenAI
- Improved embedding generation speed
- Enhanced system reliability and maintainability

---

## Phase 3: Analytics & Advanced Features (May 2025)

### Commit: 27928272 - analysis agent initiated
**Author:** Niral Patel
**Date:** 2025-05-15
**Message:** analysis agent initiated

**Summary of Changes:**
- Introduced comprehensive analytics and business intelligence system
- Created AnalyticsAgent for data-driven insights
- Implemented automated metrics calculation and analysis

**Technical Details:**
- **New Analytics Agent:**
  - `AnalyticsAgent`: Processes business intelligence queries
  - Vector search integration for analytics data
  - LLM-powered insight generation

- **Analytics Pipeline:**
  - `analytics_pipeline_dag.py`: Automated analytics data processing
  - `calculate_metrics.py`: Business metrics computation
  - `analyze_metrics.py`: Insight generation and analysis

- **Data Processing:**
  - Order, product, and customer data aggregation
  - Key performance indicator (KPI) calculation
  - Trend analysis and pattern recognition
  - Vector storage in `analysis_data` Qdrant collection

- **Database Integration:**
  - `AnalyticsDocumentLog` model for tracking processed documents
  - MongoDB storage for analytics metadata
  - Qdrant integration for semantic analytics search

**Business Intelligence Features:**
- Automated business metrics calculation
- Trend analysis and forecasting
- Customer behavior insights
- Product performance analytics

**Removed Components:**
- Deprecated `CRMAgent` in favor of specialized analytics
- Cleaned up legacy CRM pipeline components

---

### Commit: 59fe1a0 - modify data pipelines and agent refinement
**Author:** Niral Patel
**Date:** 2025-05-22
**Message:** modify data pipelines and agent refinement

**Summary of Changes:**
- Enhanced agent logic for handling multiple queries and improved context processing
- Updated data pipeline scheduling and order processing
- Refined agent communication and dependency management

**Technical Details:**
- **Agent Improvements:**
  - Enhanced context processing using dependency information
  - Improved multi-query handling capabilities
  - Better JSON parsing and duplicate key handling in MasterAgent
  - Refined system prompts for better agent performance

- **Pipeline Updates:**
  - Modified DAG scheduling to run daily
  - Updated order fetching to support ID-based queries
  - Added product order fetching tasks
  - Improved data preparation and validation processes

**Key Enhancements:**
- Better agent coordination and communication
- Improved data processing reliability
- Enhanced query handling capabilities

---

### Commit: 318fcf7 - Fix chat history bug
**Author:** pratik.jadav
**Date:** 2025-05-29
**Message:** Fix chat history bug.

**Summary of Changes:**
- Resolved critical chat history loading and display issues
- Enhanced frontend chat interface with improved UX features
- Implemented pagination and scroll management

**Technical Details:**
- **Frontend Improvements:**
  - Fixed chat history loading and scrolling issues
  - Implemented message pagination with `MESSAGES_PER_PAGE`
  - Added scroll-to-bottom functionality
  - Enhanced chat session management

- **API Enhancements:**
  - New `/message-ids` endpoint for retrieving chat message IDs
  - Improved session-based message retrieval
  - Enhanced authentication token management

- **Code Organization:**
  - Moved configuration files to dedicated `config` directory
  - Refactored imports and dependencies
  - Improved code structure and maintainability

**User Experience Improvements:**
- Smoother chat interface interactions
- Better message loading and display
- Enhanced session management

---

## Phase 4: DGE Integration & Advanced Analytics (June 2025)

### Commit: 0de41ae - DGE Pipeline initiated
**Author:** Smit Patel
**Date:** 2025-06-20
**Message:** DGE Pipeline initiated

**Summary of Changes:**
- Introduced comprehensive DGE (Data Governance Engine) integration
- Implemented product mapping between DGE and Magento systems
- Created automated data synchronization pipelines

**Technical Details:**
- **DGE Integration:**
  - `dge_product_dag.py`: Automated DGE product data processing
  - `product_mapping_dag.py`: Product mapping between DGE and Magento
  - DGE API client implementation for data fetching

- **Product Mapping System:**
  - SKU-based product mapping between systems
  - Automated product synchronization
  - Data consistency validation and reconciliation

- **Enhanced Product Agent:**
  - Store-specific product queries support
  - DGE and Magento data integration
  - Improved context handling for multi-system queries

- **New Scripts and Tools:**
  - `fetch_dge_products.py`: DGE product data extraction
  - `product_mapper.py`: Automated product mapping logic
  - `fetch_magento_products_by_sku.py`: Magento product retrieval by SKU

**Integration Features:**
- Bi-directional data synchronization
- Store-specific product management
- Automated data consistency checks
- Enhanced product search capabilities

---

### Commit: 48e5510 - update DGE flow
**Author:** get
**Date:** 2025-06-25
**Message:** update DGE flow

**Summary of Changes:**
- Enhanced DGE data processing workflow
- Improved analytics agent with product and customer insights
- Updated product mapping and data synchronization processes

**Technical Details:**
- **Analytics Enhancements:**
  - Updated analytics agent for product and customer insights
  - Enhanced query routing for analytics-related requests
  - Improved total product counts from DGE integration

- **DGE Client Implementation:**
  - `DGEClient` class for standardized DGE API interactions
  - Improved error handling and data validation
  - Enhanced pagination support for large datasets

- **Product Agent Updates:**
  - Better DGE/Magento data support
  - Improved context handling and metadata extraction
  - Enhanced product search and recommendation capabilities

**Workflow Improvements:**
- Streamlined DGE data processing
- Better integration between analytics and product data
- Enhanced data quality and consistency

---

### Commit: 93f8817 - initial state in DAG added
**Author:** Niral
**Date:** 2025-06-26
**Message:** initial state in DAG added

**Summary of Changes:**
- Implemented initial state functionality for comprehensive data refreshes
- Enhanced data pipeline flexibility with full refresh capabilities
- Improved product and customer data processing

**Technical Details:**
- **Initial State Implementation:**
  - Added `is_initial` parameter to DAGs for full data refresh control
  - Implemented pagination support for complete data extraction
  - Enhanced data processing for initial loads vs. incremental updates

- **New Functions:**
  - `fetch_customers_paginated`: Complete customer data extraction
  - `fetch_all_orders_paginated`: Comprehensive order data fetching
  - Enhanced product fetching with date-based filtering

- **Product Agent Updates:**
  - Renamed "price" type to "dge_price" for DGE pricing details
  - Improved price data handling and display

- **Pipeline Enhancements:**
  - Added `cleanup_product_bundle` task for data maintenance
  - Improved product mapping and synchronization processes

**Data Management Features:**
- Full data refresh capabilities
- Improved data consistency and integrity
- Enhanced pagination for large datasets

---

## Phase 5: Email Integration & Advanced Features (July 2025)

### Commit: 3e3cfec - email agent initiated
**Author:** Niral
**Date:** 2025-07-08
**Message:** email agent initiated

**Summary of Changes:**
- Introduced email functionality with dedicated EmailAgent
- Implemented email sending capabilities and API integration
- Enhanced chat interface with email command support

**Technical Details:**
- **Email Agent Implementation:**
  - New `EmailAgent` for handling email-related queries and operations
  - Integration with email service APIs
  - Support for automated email generation and sending

- **Email Features:**
  - Email composition and sending capabilities
  - Template-based email generation
  - Integration with existing agent workflow

**Communication Enhancement:**
- Automated email capabilities
- Enhanced user communication options
- Integrated email workflow within chat interface

---

### Commit: 8f6c5d1 - Add Chat Command Panel For Email, And Add Send Email Model
**Author:** pratik.jadav
**Date:** 2025-07-08
**Message:** Add Chat Command Panel For Email, And Add Send Email Model

**Summary of Changes:**
- Enhanced chat interface with email command panel
- Implemented email sending models and UI components
- Improved user interaction for email functionality

**Technical Details:**
- **Frontend Enhancements:**
  - Chat command panel for email operations
  - Email composition interface
  - Send email modal and form components

- **User Interface:**
  - Intuitive email command integration
  - Enhanced chat experience with email capabilities
  - Improved user workflow for email operations

---

### Commit: 7a553a9 - Integrate Send Mail API
**Author:** pratik.jadav
**Date:** 2025-07-08
**Message:** Intigrate Send Mail API.

**Summary of Changes:**
- Completed email API integration
- Implemented full email sending functionality
- Enhanced system communication capabilities

**Technical Details:**
- **API Integration:**
  - Complete email sending API implementation
  - Error handling and validation for email operations
  - Integration with external email service providers

- **System Enhancement:**
  - Full email workflow implementation
  - Enhanced communication capabilities
  - Improved user experience with email features

---

## Technical Architecture Summary

### Core Technologies
- **Backend:** FastAPI, Python 3.9+
- **AI Framework:** LangGraph, LangChain, OpenAI GPT-4
- **Data Pipeline:** Apache Airflow
- **Databases:** MongoDB (structured data), Qdrant (vector embeddings)
- **Frontend:** React, TypeScript, Vite
- **Containerization:** Docker, Docker Compose
- **Authentication:** JWT-based security

### Agent Architecture
```
Master Agent (Query Router)
├── Product Agent (Product queries & DGE integration)
├── Order Agent (Order processing & analytics)
├── Customer Agent (Customer data & insights)
├── Analytics Agent (Business intelligence & KPIs)
├── PDF Agent (Document processing)
├── Email Agent (Email operations)
└── Greet Agent (User interaction & onboarding)
```

### Data Flow
1. **Data Ingestion:** Airflow DAGs extract data from Magento, DGE, and other sources
2. **Data Processing:** ETL scripts clean, transform, and validate data
3. **Vector Storage:** Processed data is embedded and stored in Qdrant collections
4. **Query Processing:** User queries are routed to appropriate agents
5. **Response Generation:** Agents use vector search + LLM to generate responses
6. **User Interface:** React frontend provides chat interface and dashboards

### Key Features
- **Multi-Agent System:** Specialized agents for different business domains
- **Vector Search:** Semantic search capabilities across all data types
- **Real-time Analytics:** Automated business intelligence and KPI tracking
- **Data Integration:** Seamless integration between Magento and DGE systems
- **User Management:** Comprehensive authentication and session management
- **Email Integration:** Automated email capabilities within the chat interface

### Security & Performance
- JWT-based authentication with refresh tokens
- Environment variable configuration management
- Docker containerization for scalability
- Async API handling for high performance
- Vector database optimization for fast semantic search

---

## Development Guidelines

### Code Organization
- Modular agent architecture for easy extension
- Separation of concerns between data pipeline and API
- Configuration externalization for security and flexibility
- Comprehensive error handling and logging

### Testing Strategy
- Unit tests for individual agents and components
- Integration tests for data pipeline workflows
- API endpoint testing with authentication
- Frontend component testing

### Deployment
- Docker-based containerization
- Environment-specific configuration
- Scalable architecture supporting horizontal scaling
- Monitoring and logging integration

This documentation serves as a comprehensive reference for developers working on the Magento Bot project, providing detailed insights into the evolution, architecture, and technical implementation of the system.

