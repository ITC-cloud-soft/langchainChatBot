# マルチステージビルドを使用した最適化されたDockerfile
FROM node:16-alpine AS builder

# 環境変数の設定
ENV NODE_ENV=production

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係のコピーとインストール
COPY package*.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# ソースコードのコピー
COPY . .

# アプリケーションのビルド
RUN pnpm build

# 本番環境用のステージ
FROM nginx:alpine

# 環境変数の設定
ENV NGINX_PORT=80

# ビルド成果物のコピー
COPY --from=builder /app/dist /usr/share/nginx/html

# カスタムNginx設定のコピー
COPY nginx.conf /etc/nginx/nginx.conf

# ヘルスチェックの設定
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${NGINX_PORT}/ || exit 1

# ポートの公開
EXPOSE 80

# Nginxの起動
CMD ["nginx", "-g", "daemon off;"]