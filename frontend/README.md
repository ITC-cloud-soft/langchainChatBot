# Chatbot Frontend

React + TypeScriptを使用したチャットボットフロントエンドアプリケーションです。Material-UIを採用し、チャット機能、LLM設定管理、ナレッジベース管理を提供します。

## Features

- **リアルタイムチャット**: WebSocketによるストリーミングチャット
- **LLM設定管理**: API設定、モデル選択、パラメータ調整
- **ナレッジベース管理**: ドキュメントのアップロード、検索、管理
- **レスポンシブデザイン**: Material-UIによるモダンなUI
- **マークダウン対応**: チャットメッセージのマークダウン表示

## Technology Stack

- **React 18**: モダンなUIフレームワーク
- **TypeScript**: 型安全な開発
- **Material-UI v5**: UIコンポーネントライブラリ
- **React Router v6**: ルーティング
- **Axios**: HTTPクライアント
- **React Hook Form**: フォーム管理
- **notistack**: 通知コンポーネント
- **react-markdown**: マークダウン表示
- **Vite**: ビルドツール

## Installation

### Prerequisites

- Node.js >= 16.0.0
- npm or yarn or pnpm

### Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
yarn install
# or
pnpm install

# Create environment file
cp .env.example .env
# Edit .env with your API URL
```

## Development

### Start Development Server

```bash
# Development server
npm run dev
# or
yarn dev
# or
pnpm dev

# HTTPS development server
npm run dev:https
# or
yarn dev:https
# or
pnpm dev:https
```

Access the application at http://localhost:3000

### Build for Production

```bash
# Build for production
npm run build
# or
yarn build
# or
pnpm build

# Preview production build
npm run preview
# or
yarn preview
# or
pnpm preview

# Clean build artifacts
npm run build:clean
# or
yarn build:clean
# or
pnpm build:clean
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
# Backend API URL
REACT_APP_API_URL=http://localhost:8000

# Environment (development/production)
REACT_APP_ENVIRONMENT=development

# Log level (debug/info/warn/error)
REACT_APP_LOG_LEVEL=info

# Version information
REACT_APP_VERSION=1.0.0
```

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── Layout.tsx       # Main layout component
│   └── common/          # Shared components
│       ├── DataTable.tsx
│       ├── ErrorAlert.tsx
│       ├── FileUploadArea.tsx
│       ├── LoadingSpinner.tsx
│       ├── PageContainer.tsx
│       ├── SearchBar.tsx
│       └── StatusChip.tsx
├── pages/               # Page components
│   ├── ChatPage.tsx     # Chat interface
│   ├── LlmConfigPage.tsx # LLM configuration
│   └── KnowledgePage.tsx # Knowledge base management
├── services/            # API services
│   └── api.ts          # API client and types
├── hooks/              # Custom React hooks
│   ├── useApi.ts       # API communication
│   └── useConfig.ts    # Configuration management
├── utils/              # Utility functions
│   ├── config.ts       # Configuration utilities
│   ├── index.ts        # General utilities
│   └── logger.ts       # Logging utilities
└── App.tsx             # Main application component
```

## Key Features

### Chat Interface
- Real-time message streaming
- Session management
- Reference document display
- Markdown support
- Auto-scrolling
- Message history

### LLM Configuration
- Import/export settings
- Model selection
- Parameter adjustment
- Configuration testing
- Reset to defaults

### Knowledge Base Management
- Document upload
- Directory batch upload
- Document search
- Collection management
- Document deletion

## API Integration

The frontend integrates with the backend API through `src/services/api.ts`:

- **Base URL**: Configurable via `REACT_APP_API_URL`
- **Authentication**: Bearer token stored in localStorage
- **Error Handling**: Automatic handling of 401/403/404/500 errors

### API Modules
- `chatApi`: Chat message sending, streaming, history
- `llmConfigApi`: LLM configuration CRUD operations
- `knowledgeApi`: Knowledge base document management
- `healthApi`: System health checks
- `configApi`: Configuration management

## Configuration

### Path Aliases
TypeScript path aliases are configured:
- `@/*` → `src/*`
- `@/components/*` → `src/components/*`
- `@/utils/*` → `src/utils/*`
- `@/hooks/*` → `src/hooks/*`
- `@/pages/*` → `src/pages/*`
- `@/services/*` → `src/services/*`

### Backend Connection
During development, requests are proxied to `http://localhost:8000` via the proxy configuration in `package.json`.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Write tests for new features
4. Update documentation as needed

## License

MIT License