# MySQL Chat History Integration

This document provides setup and usage instructions for the MySQL chat history integration feature.

## Overview

The MySQL chat history integration adds persistent storage capabilities to the chatbot system, allowing chat sessions, messages, and metadata to be stored in a MySQL database. This provides:

- **Persistent chat history**: Chat conversations are stored permanently in MySQL
- **Session management**: Create, update, and manage chat sessions
- **Message storage**: All messages (user and assistant) are stored with metadata
- **Statistics and analytics**: Track usage patterns and generate reports
- **Search capabilities**: Search through chat history
- **Export functionality**: Export chat data in various formats

## Features

### Database Models
- **ChatSession**: Stores session information (ID, title, user, timestamps)
- **ChatMessage**: Stores individual messages with role, content, and metadata
- **ChatMetadata**: Stores session-level metadata and statistics
- **ChatHistoryStats**: Stores aggregated statistics for reporting

### API Endpoints
- `POST /api/chat/sessions` - Create new chat session
- `GET /api/chat/sessions` - List chat sessions with pagination
- `GET /api/chat/sessions/{session_id}/full` - Get full session data
- `PUT /api/chat/sessions/{session_id}` - Update session
- `DELETE /api/chat/sessions/{session_id}/permanent` - Delete session permanently
- `GET /api/chat/sessions/{session_id}/statistics` - Get session statistics
- `GET /api/chat/statistics/global` - Get global statistics
- `GET /api/chat/search` - Search chat sessions
- `POST /api/chat/cleanup` - Clean up old sessions
- `GET /api/chat/sessions/{session_id}/export` - Export session data
- `GET /api/chat/health` - Comprehensive health check

### Services
- **ChatHistoryService**: High-level service for chat history operations
- **DatabaseManager**: Manages database connections and pooling
- **Migration system**: Alembic-based database migrations

## Setup Instructions

### Prerequisites
- MySQL 8.0+ installed and running
- Python 3.9+ with required dependencies
- Access to create databases and users

### 1. Database Setup

#### Create Database and User
```sql
-- Create database
CREATE DATABASE chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (optional, recommended for production)
CREATE USER 'chatbot_user'@'localhost' IDENTIFIED BY 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON chatbot.* TO 'chatbot_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Update Configuration
Edit `backend/config.toml` with your database settings:

```toml
[database]
host = "localhost"
port = 3306
username = "chatbot_user"  # or "root" for development
password = "your_secure_password"
database = "chatbot"
ssl = false
pool_size = 20
max_overflow = 30
pool_recycle = 3600
echo_sql = false
```

### 2. Install Dependencies

```bash
cd backend
pip install -e .
```

Or install specific dependencies:
```bash
pip install sqlalchemy[asyncio]==2.0.36
pip install asyncmy==0.2.9
pip install alembic==1.14.0
```

### 3. Run Database Migrations

```bash
# Run all migrations
python migrate_db.py upgrade

# Check current migration status
python migrate_db.py current

# View migration history
python migrate_db.py history
```

### 4. Start the Application

```bash
# Using the Makefile
make dev-backend

# Or directly
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Usage Examples

### Creating a Chat Session
```python
import requests

# Create a new session
response = requests.post(
    "http://localhost:8000/api/chat/sessions",
    json={
        "session_id": "my_session_123",
        "title": "Customer Support Chat",
        "user_id": "user_456",
        "metadata": {"department": "support"}
    }
)

session = response.json()
print(f"Created session: {session['session_id']}")
```

### Sending Messages
```python
# Send a message
response = requests.post(
    "http://localhost:8000/api/chat/send",
    json={
        "message": "Hello, I need help with my account",
        "session_id": "my_session_123"
    }
)

chat_response = response.json()
print(f"Assistant: {chat_response['response']}")
```

### Retrieving Chat History
```python
# Get session history
response = requests.get(
    "http://localhost:8000/api/chat/sessions/my_session_123/full"
)

history = response.json()
print(f"Session: {history['session']['title']}")
print(f"Messages: {len(history['messages'])}")

for message in history['messages']:
    print(f"{message['role']}: {message['content'][:50]}...")
```

### Getting Statistics
```python
# Get session statistics
response = requests.get(
    "http://localhost:8000/api/chat/sessions/my_session_123/statistics"
)

stats = response.json()
print(f"Total messages: {stats['total_messages']}")
print(f"User messages: {stats['message_counts_by_role']['user']}")
print(f"Assistant messages: {stats['message_counts_by_role']['assistant']}")

# Get global statistics
response = requests.get("http://localhost:8000/api/chat/statistics/global")
global_stats = response.json()
print(f"Total sessions: {global_stats['total_sessions']}")
print(f"Total messages: {global_stats['total_messages']}")
```

### Searching Chat History
```python
# Search for specific content
response = requests.get(
    "http://localhost:8000/api/chat/search?q=account&limit=10"
)

results = response.json()
for session in results['data']['sessions']:
    print(f"Found session: {session['title']}")
```

### Exporting Chat Data
```python
# Export session data
response = requests.get(
    "http://localhost:8000/api/chat/sessions/my_session_123/export?format=json"
)

export_data = response.json()
print(f"Exported {len(export_data['data']['messages'])} messages")
```

## Configuration Options

### Database Configuration
```toml
[database]
host = "localhost"          # MySQL server host
port = 3306                 # MySQL server port
username = "chatbot_user"   # MySQL username
password = "password"       # MySQL password
database = "chatbot"        # Database name
ssl = false                 # Use SSL connection
pool_size = 20              # Connection pool size
max_overflow = 30           # Max overflow connections
pool_recycle = 3600         # Connection recycling time (seconds)
echo_sql = false            # Log SQL queries
```

### Environment Variables
You can also configure database settings using environment variables:

```bash
export MYSQL_HOST="localhost"
export MYSQL_PORT="3306"
export MYSQL_USER="chatbot_user"
export MYSQL_PASSWORD="your_secure_password"
export MYSQL_DATABASE="chatbot"
export MYSQL_SSL="false"
```

## Database Schema

### chat_sessions Table
| Column | Type | Description |
|--------|------|-------------|
| id | INT | Primary key |
| session_id | VARCHAR(255) | Unique session identifier |
| title | VARCHAR(500) | Session title |
| user_id | VARCHAR(255) | User identifier |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |
| is_active | BOOLEAN | Session active status |
| metadata | JSON | Additional metadata |

### chat_messages Table
| Column | Type | Description |
|--------|------|-------------|
| id | INT | Primary key |
| session_id | VARCHAR(255) | Foreign key to sessions |
| message_id | VARCHAR(255) | Unique message identifier |
| role | VARCHAR(50) | Message role (user/assistant) |
| content | LONGTEXT | Message content |
| message_type | VARCHAR(50) | Message type (text/error) |
| timestamp | DATETIME | Message timestamp |
| source_documents | JSON | Source documents |
| error_info | JSON | Error information |
| metadata | JSON | Additional metadata |

### chat_metadata Table
| Column | Type | Description |
|--------|------|-------------|
| id | INT | Primary key |
| session_id | VARCHAR(255) | Foreign key to sessions |
| total_messages | INT | Total message count |
| total_tokens | INT | Total tokens used |
| last_user_message | VARCHAR(255) | Last user message |
| last_assistant_message | VARCHAR(255) | Last assistant message |
| model_used | VARCHAR(100) | Model used for responses |
| language | VARCHAR(10) | Session language |
| tags | JSON | Session tags |
| custom_fields | JSON | Custom fields |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

### chat_history_stats Table
| Column | Type | Description |
|--------|------|-------------|
| id | INT | Primary key |
| date | VARCHAR(10) | Date in YYYY-MM-DD format |
| total_sessions | INT | Total sessions for date |
| total_messages | INT | Total messages for date |
| total_users | INT | Total users for date |
| avg_session_length | INT | Average session length |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

## Migration Management

### Creating New Migrations
```bash
# Create a new migration
python migrate_db.py revision -m "Add new feature" --autogenerate

# Create migration without autogenerate
python migrate_db.py revision -m "Custom migration"
```

### Running Migrations
```bash
# Upgrade to latest version
python migrate_db.py upgrade

# Upgrade to specific version
python migrate_db.py upgrade --revision 001

# Downgrade one version
python migrate_db.py downgrade

# Downgrade to specific version
python migrate_db.py downgrade --revision base
```

### Migration Commands
```bash
# Show current version
python migrate_db.py current

# Show migration history
python migrate_db.py history
```

## Testing

### Running Tests
```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_chat_history_service.py -v

# Run with coverage
uv run pytest tests/ --cov=api --cov-report=html
```

### Test Coverage
The test suite covers:
- Database model operations
- Service layer functionality
- API endpoint behavior
- Error handling scenarios
- Database migrations

## Performance Considerations

### Database Optimization
- Use appropriate indexes on frequently queried columns
- Monitor connection pool usage
- Consider partitioning for large datasets
- Regular database maintenance (optimize, analyze)

### Connection Pooling
- Adjust pool size based on expected load
- Monitor pool overflow usage
- Set appropriate connection recycling times

### Query Optimization
- Use database-specific query optimization
- Implement pagination for large result sets
- Cache frequently accessed data

## Monitoring and Maintenance

### Health Checks
```bash
# Check overall health
curl http://localhost:8000/api/chat/health

# Check database health specifically
curl http://localhost:8000/api/chat/health | jq '.database'
```

### Cleanup Operations
```bash
# Clean up sessions older than 30 days
curl -X POST "http://localhost:8000/api/chat/cleanup?days_old=30"

# Get statistics before cleanup
curl http://localhost:8000/api/chat/statistics/global
```

### Backup and Recovery
```python
# Manual backup (implement based on your backup strategy)
import asyncio
from api.core.database import database_manager

async def backup_database():
    success = await database_manager.backup_database("backup.sql")
    if success:
        print("Backup created successfully")
    else:
        print("Backup failed")

asyncio.run(backup_database())
```

## Troubleshooting

### Common Issues

#### Database Connection Errors
1. **Check MySQL service is running**
   ```bash
   # On Linux/macOS
   sudo systemctl status mysql
   # On Windows
   net start mysql
   ```

2. **Verify database credentials**
   ```python
   # Test connection manually
   import asyncio
   from api.core.database import database_manager
   
   async def test_connection():
       health = await database_manager.health_check()
       print(health)
   
   asyncio.run(test_connection())
   ```

3. **Check database exists**
   ```sql
   SHOW DATABASES;
   USE chatbot;
   SHOW TABLES;
   ```

#### Migration Errors
1. **Check migration status**
   ```bash
   python migrate_db.py current
   python migrate_db.py history
   ```

2. **Manual migration**
   ```bash
   python migrate_db.py upgrade --revision 001
   ```

#### Performance Issues
1. **Monitor connection pool**
   ```bash
   # Check database connections
   mysql -u chatbot_user -p -e "SHOW STATUS LIKE 'Threads_connected';"
   ```

2. **Optimize queries**
   ```sql
   -- Check slow queries
   SHOW VARIABLES LIKE 'long_query_time';
   SHOW PROCESSLIST;
   ```

### Logging
Check application logs for detailed error information:
```bash
# Application logs
tail -f app.log

# MySQL logs (location varies by installation)
tail -f /var/log/mysql/error.log
```

## Security Considerations

### Database Security
1. **Use strong passwords** for database users
2. **Limit user privileges** to minimum required
3. **Use SSL connections** in production environments
4. **Regular security updates** for MySQL server

### Data Protection
1. **Sensitive data** should be encrypted at rest
2. **Access controls** for chat history data
3. **Data retention policies** for old sessions
4. **Backup security** for stored chat data

### Network Security
1. **Firewall rules** for database access
2. **VPN or secure tunnel** for remote access
3. **Network monitoring** for unusual activity

## Integration with Existing System

### Backward Compatibility
- Existing in-memory chat history continues to work
- Database storage is transparent to the chat service
- Graceful degradation if database is unavailable

### Data Migration
- Tool available to migrate existing chat history
- Export/import functionality for data portability
- Support for multiple storage backends

### Performance Impact
- Minimal impact on existing chat performance
- Asynchronous database operations
- Connection pooling for efficiency

This MySQL integration provides a robust, scalable solution for persistent chat history storage while maintaining compatibility with the existing chatbot system.