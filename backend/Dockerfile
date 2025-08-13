# マルチステージビルドを使用した最適化されたDockerfile
FROM python:3.9-slim as builder

# 環境変数の設定
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 仮想環境の作成
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ソースコードのコピー
COPY . .

# アプリケーションのビルド
RUN pip install -e .

# 本番環境用のステージ
FROM python:3.9-slim

# 環境変数の設定
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# ユーザーの作成
RUN addgroup --system app && adduser --system --group app

# 仮想環境のコピー
COPY --from=builder /opt/venv /opt/venv

# アプリケーションディレクトリの作成
WORKDIR /app

# ソースコードのコピー
COPY --from=builder --chown=app:app /backend/api /app/api
COPY --from=builder --chown=app:app /backend/main.py /app/main.py
COPY --from=builder --chown=app:app /backend/config.toml /app/config.toml

# 静的ファイルのコピー（存在する場合）
RUN mkdir -p /app/static && \
    if [ -d "/backend/static" ]; then \
        cp -r /backend/static/* /app/static/; \
    fi

# ヘルスチェックの設定
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ポートの公開
EXPOSE 8000

# アプリケーションの実行
USER app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]