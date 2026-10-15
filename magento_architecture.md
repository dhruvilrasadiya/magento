# MAGENTO E-COMMERCE AI BOT - COMPLETE PROJECT DESCRIPTION
================================================================

## PROJECT OVERVIEW
==================

The Magento-bot is an intelligent AI-powered system designed for Magento e-commerce platforms that combines advanced data engineering with agentic AI capabilities. This comprehensive solution provides intelligent customer support, data analysis, and automated assistance for e-commerce operations.

### Key Features:
- **Multi-Agent AI System**: Specialized AI agents for different data domains
- **Real-time Data Processing**: Apache Airflow-based ETL pipeline
- **Vector Database Integration**: Qdrant for semantic search and retrieval
- **RESTful API**: FastAPI backend with streaming support
- **Session Management**: Persistent chat sessions with user authentication
- **Scalable Architecture**: Docker-based microservices deployment

## SYSTEM ARCHITECTURE
=====================

### 1. DATA SOURCES LAYER
------------------------
The system integrates multiple data sources to provide comprehensive e-commerce intelligence:

**Magento API Integration:**
- Order data (order IDs, items, shipping status, totals, fulfillment)
- Product data (stock levels, pricing, brands, suppliers, attributes)
- Customer data (profiles, addresses, order history, invoices)
- Inventory management data

**Document Processing:**
- PDF documents (product specifications, datasheets, manuals)
- CRM data (customer support tickets, emails)
- Blog posts and knowledge base articles

**Analytics Data:**
- Business KPIs and metrics
- Sales trends and revenue analysis
- Product performance data
- Customer behavior analytics

### 2. DATA PIPELINE LAYER (Apache Airflow)
-------------------------------------------
The ETL pipeline orchestrates data processing through multiple specialized DAGs:

**Order Pipeline DAG:**
- Fetches order data from Magento API
- Processes and normalizes order information
- Stores structured data and creates vector embeddings
- Runs daily with configurable parameters

**Product Pipeline DAG:**
- Retrieves product catalog information
- Processes inventory and stock data
- Handles product-order relationships
- Updates product performance metrics

**PDF Processing DAG:**
- Extracts text from PDF documents
- Chunks content for optimal vector storage
- Creates embeddings for semantic search
- Processes product specifications and manuals

**Customer Pipeline DAG:**
- Fetches customer profiles and data
- Processes customer interaction history
- Creates customer behavior embeddings
- Handles CRM data integration

**Analytics Pipeline DAG:**
- Calculates business metrics and KPIs
- Processes sales and revenue data
- Generates performance analytics
- Creates trend analysis data

### 3. VECTOR DATABASE LAYER (Qdrant)
-------------------------------------
Multiple specialized vector databases for semantic search:

**Collections:**
- `order_data`: Order-related embeddings and metadata
- `product_data`: Product information and specifications
- `pdf_data`: Document content and technical specifications
- `customer_data`: Customer profiles and interaction history

**Features:**
- Cosine similarity search
- Metadata filtering
- Real-time updates
- Scalable vector storage

### 4. AGENTIC AI SYSTEM (LangGraph + LangChain)
-----------------------------------------------
The core intelligence layer built with LangGraph orchestration:

**Master Agent:**
- Analyzes incoming queries
- Determines which specialized agents to activate
- Manages agent dependencies and execution order
- Routes queries to appropriate agents

**Specialized Agents:**

1. **Order Agent:**
   - Handles order-specific queries
   - Accesses order database and history
   - Provides order status and tracking information
   - Manages order-related customer support

2. **Product Agent:**
   - Manages product catalog queries
   - Provides pricing and availability information
   - Handles product recommendations
   - Accesses inventory data

3. **PDF Agent:**
   - Processes document-based queries
   - Searches through product specifications
   - Provides technical documentation
   - Handles manual and datasheet queries

4. **Customer Agent:**
   - Manages customer profile information
   - Handles customer history queries
   - Provides personalized recommendations
   - Manages customer support interactions

5. **Analytics Agent:**
   - Provides business intelligence insights
   - Generates reports and metrics
   - Handles trend analysis queries
   - Manages KPI reporting

6. **Greet Agent:**
   - Handles casual conversation
   - Manages greeting interactions
   - Provides general assistance
   - Manages conversational flow

7. **Combiner Agent:**
   - Synthesizes responses from multiple agents
   - Creates unified, coherent responses
   - Manages agent dependency resolution
   - Provides final response formatting

**Agent Orchestration:**
- State-based execution flow
- Dependency management between agents
- Parallel and sequential processing
- Error handling and recovery

### 5. API LAYER (FastAPI)
-------------------------
RESTful API providing comprehensive backend services:

**Authentication System:**
- JWT-based authentication
- Role-based access control (admin, supervisor, superadmin)
- Token refresh mechanism
- Password reset functionality

**Chat System:**
- Real-time chat processing
- Streaming response support
- Session-based conversations
- Message history management

**Session Management:**
- Persistent chat sessions
- Session creation and management
- Session history and retrieval
- User-specific session isolation

**User Management:**
- User creation and management
- Role assignment and permissions
- User profile management
- Administrative controls

### 6. DATABASE LAYER
--------------------
Multi-database architecture for different data types:

**MongoDB:**
- User profiles and authentication data
- Chat sessions and message history
- Application metadata and configurations
- Session state management

**PostgreSQL:**
- Airflow metadata and task management
- DAG execution history
- Pipeline orchestration data

**Qdrant Vector Databases:**
- Semantic search capabilities
- Document embeddings storage
- Vector similarity operations
- Metadata filtering and search


## HOW TO USE THE ORCHESTRATOR
=============================

### 1. ORCHESTRATOR INITIALIZATION
---------------------------------
The AgentOrchestrator is the central component that manages the flow between AI agents:


### 2. QUERY PROCESSING FLOW
---------------------------
When a user query is received, the orchestrator follows this flow:

**Step 1: Master Agent Analysis**
- Receives the user query
- Analyzes query intent and content
- Determines which specialized agents are needed
- Sets up agent dependencies and execution order

**Step 2: Agent Selection**
- Based on query analysis, selects appropriate agents:
  - Order queries → order_agent
  - Product queries → product_agent
  - Technical specs → pdf_agent
  - Customer info → customer_agent
  - Analytics → analytics_agent
  - Greetings → greet_agent

**Step 3: Dependency Resolution**
- Manages agent execution order based on dependencies
- Ensures agents that depend on others run after their dependencies
- Handles parallel execution where possible

**Step 4: Agent Execution**
- Runs selected agents in the determined order
- Each agent processes its portion of the query
- Agents access their respective vector databases
- Results are stored in shared state

**Step 5: Response Combination**
- Combiner agent synthesizes all agent responses
- Creates a unified, coherent response
- Maintains context and dependencies
- Returns final response to user




## HOW TO USE AI AGENTS
======================

### 1. INDIVIDUAL AGENT USAGE
----------------------------
Each agent can be used independently for specific tasks:


### 2. AGENT CAPABILITIES
------------------------

**Order Agent:**
- Query order status and tracking
- Find orders by date range, customer, or product
- Analyze order patterns and trends
- Handle order-related customer support

**Product Agent:**
- Search product catalog
- Check inventory and availability
- Provide pricing information
- Generate product recommendations

**PDF Agent:**
- Search through technical documentation
- Extract product specifications
- Find relevant manual sections
- Answer technical questions

**Customer Agent:**
- Retrieve customer profiles
- Analyze customer history
- Provide personalized recommendations
- Handle customer service queries

**Analytics Agent:**
- Generate business reports
- Calculate KPIs and metrics
- Analyze sales trends
- Provide performance insights



## DATA PIPELINE USAGE
=====================



### 1. MONITORING PIPELINE EXECUTION
-----------------------------------
- Access Airflow UI 
- Monitor DAG execution status
- View task logs and debugging information
- Manage DAG schedules and configurations

### 2. DATA PROCESSING WORKFLOW
------------------------------

**Order Data Processing:**
1. Fetch orders from Magento API
2. Normalize and clean order data
3. Create embeddings for semantic search
4. Store in vector database
5. Update analytics metrics

**Product Data Processing:**
1. Retrieve product catalog
2. Process inventory information
3. Generate product embeddings
4. Update product performance data
5. Sync with order relationships

**PDF Document Processing:**
1. Extract text from PDF files
2. Chunk content for optimal search
3. Generate document embeddings
4. Store with metadata
5. Index for semantic retrieval



## TROUBLESHOOTING
==================

### 1. COMMON ISSUES
-------------------

**Vector Database Connection:**
- Ensure Qdrant is running on correct port
- Check QDRANT_HOST and QDRANT_PORT environment variables
- Verify collections are properly initialized

**Agent Execution Errors:**
- Check OpenAI API key and quota
- Verify model names are correct
- Ensure vector databases contain data

**Airflow DAG Failures:**
- Check Magento API credentials
- Verify data source accessibility
- Monitor task logs in Airflow UI

### 2. MONITORING AND LOGGING
-----------------------------

**Application Logs:**
- API logs: Available in FastAPI console output
- Agent logs: Printed during execution with timestamps
- Airflow logs: Available in Airflow UI task logs

**Performance Monitoring:**
- Monitor vector database query performance
- Track agent execution times
- Monitor API response times

### 3. SCALING CONSIDERATIONS
----------------------------

**Horizontal Scaling:**
- Deploy multiple API instances behind load balancer
- Scale Qdrant clusters for high-volume queries
- Use Redis for session state in multi-instance deployments

**Performance Optimization:**
- Implement caching for frequent queries
- Optimize vector database indexes
- Use connection pooling for databases
- Implement query result caching
