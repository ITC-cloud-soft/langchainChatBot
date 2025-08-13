# Chatbot Backend

FastAPIとLangChainを使用したチャットボットバックエンドです。MySQLとQdrantをサポートしています。

## Features

- FastAPI backend
- LangChain integration
- Qdrant vector database
- MySQL database
- Configuration management
- WebSocket support for real-time chat
- RESTful API endpoints

## Installation

### Using uv (recommended)

```bash
# Install dependencies
uv sync

# Or if you need to install setuptools-scm with version
SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CHATBOT_BACKEND=1.0.0 uv sync
```

### Using pip

```bash
pip install -e .
```

## Development

### Starting the Server

```bash
# Development mode with auto-reload
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Configuration

The application uses TOML configuration files. Copy `config.toml.example` to `config.toml` and modify as needed:

```bash
cp config.toml.example config.toml
```

Also, copy the environment variables template:

```bash
cp .env.example .env
```

### Configuration Sections

- `[app]`: Application settings
- `[backend]`: Server configuration
- `[qdrant]`: Vector database settings
- `[mysql]`: MySQL database settings
- `[ollama]`: Ollama embedding model settings
- `[llm]`: Language model settings
- `[upload]`: File upload settings
- `[security]`: Security settings

### Important Configuration Files

- `config.toml`: Main configuration file (contains sensitive data, not committed to git)
- `.env`: Environment variables (contains sensitive data, not committed to git)
- `config.toml.example`: Template for main configuration
- `.env.example`: Template for environment variables

### Required Settings

Before starting the application, you need to configure:

1. **LLM Settings** in `config.toml`:
   - `llm.api_key`: Your LLM service API key
   - `llm.api_base`: Your LLM service base URL
   - `llm.model_name`: Model name to use

2. **Database Settings** in `config.toml`:
   - `database.password`: MySQL database password
   - `security.secret_key`: JWT secret key

3. **Environment Variables** in `.env`:
   - `SECRET_KEY`: JWT secret key (can also be set in config.toml)

## API Documentation

Once the server is running, you can access:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

## Key Endpoints

- `GET /health` - Health check
- `POST /api/chat/send` - Send chat message
- `GET /api/chat/sessions/{session_id}/history` - Get chat history
- `GET /api/config` - Get configuration
- `POST /api/config/update` - Update configuration
- `WebSocket /ws/{client_id}` - Real-time chat

## Environment Variables

Optional environment variables:

- `CONFIG_PATH`: Path to configuration file (default: config.toml)
- `LOG_LEVEL`: Logging level (default: INFO)
- `DEBUG`: Debug mode (default: false)