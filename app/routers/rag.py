from fastapi import APIRouter
from rag.retriever import RetrievalEngine
from rag.generator import GenerationEngine
from rag.db_connector import get_reports
from rag.embed_pipeline import EmbeddingEngine
from app.schemas.rag import RAGQuery, RAGResponse, RAGSource, IngestResponse

router = APIRouter(prefix="/rag", tags=["RAG AI Assistant"])


@router.post("/query", response_model=RAGResponse)
def rag_query(data: RAGQuery):
    retriever = RetrievalEngine()
    generator = GenerationEngine()

    docs = retriever.retrieve(data.query, top_k=data.top_k, filters=data.filters)
    result = generator.generate_response(data.query, docs)

    return RAGResponse(
        answer=result["answer"],
        sources=[
            RAGSource(id=s["id"], location=s["location"], score=s["score"])
            for s in result["sources"]
        ],
        status=result["status"],
    )


@router.post("/ingest", response_model=IngestResponse)
def rag_ingest():
    reports = get_reports()
    engine = EmbeddingEngine()
    engine.ingest_reports(reports)

    return IngestResponse(
        status="success",
        reports_ingested=len(reports),
    )


@router.get("/debug")
def rag_debug():
    import os
    from rag.embed_pipeline import CHROMA_PATH as EMBED_PATH
    from rag.retriever import CHROMA_PATH as RETRIEVE_PATH
    retriever = RetrievalEngine()
    return {
        "cwd": os.getcwd(),
        "embed_path": EMBED_PATH,
        "retrieve_path": RETRIEVE_PATH,
        "paths_match": EMBED_PATH == RETRIEVE_PATH,
        "collection_count": retriever.collection.count(),
    }
