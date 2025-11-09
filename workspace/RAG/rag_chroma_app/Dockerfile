FROM python:3.11-slim

# プロジェクトを /app に配置し、Streamlit 作業ディレクトリは rag_chroma_app 配下にする
WORKDIR /app/rag_chroma_app

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
# copy requirements from rag_chroma_app directory
COPY rag_chroma_app/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

# ソースコードをプロジェクトルートごとコピー
COPY . /app

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
