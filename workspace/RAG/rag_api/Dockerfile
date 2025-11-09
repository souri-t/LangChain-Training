FROM python:3.11-slim


# プロジェクトを /app に配置し、作業ディレクトリは rag_api 配下にする
WORKDIR /app/rag_api

# システムパッケージ
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libsndfile1 \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python 依存関係
# copy requirements from the rag_api directory (build context is the RAG root)
COPY rag_api/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

# ソースコードをプロジェクトルートごとコピー
COPY . /app

EXPOSE 8000

# 作業ディレクトリが /app/rag_api のため、モジュール指定は api_server:app とする
CMD ["python3", "-m", "uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
