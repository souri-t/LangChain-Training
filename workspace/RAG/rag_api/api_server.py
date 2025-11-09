"""
RAG WebAPI サーバー（FastAPI）
検索機能とファイル一覧取得機能をRESTful APIとして提供

このサーバーは Streamlit UI と独立して動作します。
ChromaDB と Embedder はローカル Ollama から共有リソースを使用します。
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import yaml
import os
import sys

# 親ディレクトリの services を参照するため パスを調整
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(parent_dir, "rag_chroma_app"))

from services.RAG.rag_service import RAGService
from services.Vector.generic_embedder import GenericEmbedder
from services.Vector.azure_openai_embedder import AzureOpenAIEmbedder
from services.Vector.sentence_transformer_service import SentenceTransformerEmbedder

# FastAPI アプリケーションの初期化
app = FastAPI(
    title="RAG WebAPI",
    description="ChromaDB RAG アプリケーションの検索・ファイル一覧取得API",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ===================== リクエスト/レスポンスモデル =====================

class SearchRequest(BaseModel):
    """検索リクエスト"""
    query: str = Field(..., min_length=1, description="検索クエリ（必須、1文字以上）")
    threshold: float = Field(default=0.2, ge=0.0, le=1.0, description="類似度閾値（0.0～1.0、デフォルト: 0.2）")
    n_results: int = Field(default=5, ge=1, le=100, description="返却する最大件数（1～100、デフォルト: 5）")


class FileInfo(BaseModel):
    """ファイル情報"""
    filename: str
    directory: str
    created_at: str
    doc_id: Optional[str]


class FilesResponse(BaseModel):
    """ファイル一覧レスポンス"""
    files: List[FileInfo]
    total_count: int


class SearchResult(BaseModel):
    """検索結果（個別）"""
    rank: int
    filename: str
    score: float
    document: str
    created_at: Optional[str]


class SearchResponse(BaseModel):
    """検索レスポンス"""
    query: str
    threshold: float
    hit_count: int
    results: List[SearchResult]


class SuccessResponseFiles(BaseModel):
    """成功レスポンス（ファイル一覧）"""
    success: bool = True
    data: FilesResponse


class SuccessResponseSearch(BaseModel):
    """成功レスポンス（検索）"""
    success: bool = True
    data: SearchResponse


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    success: bool = False
    error: str
    details: Optional[Dict] = None


# ===================== 設定ロード =====================

def load_config():
    """config.yaml から設定を読み込む"""
    # 環境変数 CONFIG_PATH があれば優先して使用（docker-compose で指定）
    env_path = os.environ.get("CONFIG_PATH")
    if env_path:
        if not os.path.exists(env_path):
            raise FileNotFoundError(f"config.yaml not found (CONFIG_PATH): {env_path}")
        with open(env_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # 環境変数が無ければ、親ディレクトリから相対パスを参照
    config_path = os.path.join(parent_dir, "rag_chroma_app", "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"config.yaml not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_embedder(config):
    """config に基づいて適切な Embedder を作成"""
    embedder_type = config.get('embedder', {}).get('type', 'generic')
    
    if embedder_type == 'generic':
        return GenericEmbedder(
            api_key=config['generic']['api_key'],
            embedding_url=config['generic']['embedding_url'],
            model=config['generic']['model']
        )
    elif embedder_type == 'azure-openai':
        return AzureOpenAIEmbedder(
            api_key=config['azure_openai']['api_key'],
            endpoint=config['azure_openai']['endpoint'],
            deployment_name=config['azure_openai']['deployment_name'],
            api_version=config['azure_openai'].get('api_version', '2024-02-01')
        )
    elif embedder_type == 'sentence-transformer':
        return SentenceTransformerEmbedder(
            model_name=config['sentence_transformer']['model_name']
        )
    else:
        raise ValueError(f"不正な embedder.type: {embedder_type}")


# ===================== ヘルスチェック =====================

@app.get("/")
async def root():
    """APIが動作しているか確認"""
    return {
        "message": "RAG WebAPI is running",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}


# ===================== ファイル一覧取得 API =====================

@app.get("/api/files", response_model=SuccessResponseFiles, tags=["File Management"])
async def get_files():
    """
    登録済みファイル一覧を取得する
    
    Returns:
        SuccessResponseFiles: ファイル情報リストと総件数
    
    Raises:
        HTTPException: 処理エラーが発生した場合
    """
    try:
        config = load_config()
        embedder = create_embedder(config)
        
        rag_service = RAGService(
            embedder=embedder,
            chroma_persist_directory=config['chroma']['persist_directory']
        )
        
        file_list = rag_service.get_file_list()
        
        files = [
            FileInfo(
                filename=f.get('filename', '(不明)'),
                directory=f.get('directory', '/'),
                created_at=f.get('created_at', '-'),
                doc_id=f.get('doc_id')
            )
            for f in file_list
        ]
        
        return SuccessResponseFiles(
            data=FilesResponse(
                files=files,
                total_count=len(files)
            )
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "ファイル一覧取得処理でエラー",
                "details": str(e)
            }
        )


# ===================== 検索 API =====================

@app.post("/api/search", response_model=SuccessResponseSearch, tags=["Search"])
async def search(request: SearchRequest):
    """
    キーワード検索を実行する
    
    Args:
        request (SearchRequest): 検索リクエスト（query, threshold, n_results）
    
    Returns:
        SuccessResponseSearch: 検索結果リストとヒット件数
    
    Raises:
        HTTPException: 
            - 400: リクエスト検証エラー
            - 404: 検索結果が見つからない
            - 500: サーバーエラー
    """
    try:
        config = load_config()
        embedder = create_embedder(config)
        
        rag_service = RAGService(
            embedder=embedder,
            chroma_persist_directory=config['chroma']['persist_directory']
        )
        
        results = rag_service.search(
            query=request.query,
            n_results=request.n_results,
            threshold=request.threshold
        )
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": "検索結果が見つかりません",
                    "details": "条件に合致するドキュメントがありません。"
                }
            )
        
        search_results = [
            SearchResult(
                rank=i + 1,
                filename=r['filename'],
                score=r['score'],
                document=r['document'],
                created_at=None
            )
            for i, r in enumerate(results)
        ]
        
        return SuccessResponseSearch(
            data=SearchResponse(
                query=request.query,
                threshold=request.threshold,
                hit_count=len(results),
                results=search_results
            )
        )
    
    except HTTPException:
        raise
    
    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "リクエスト検証エラー",
                "details": str(ve)
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "検索処理でエラー",
                "details": str(e)
            }
        )


# ===================== エラーハンドラ =====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTPException のカスタムエラーハンドラ"""
    if isinstance(exc.detail, dict):
        return exc.detail
    return {
        "success": False,
        "error": exc.detail,
        "details": None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
