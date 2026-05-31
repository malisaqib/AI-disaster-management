import os
import logging
from typing import List, Dict, Any
import chromadb
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


load_dotenv()
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

class EmbeddingEngine:
    def __init__(self):
        logger.info("Initializing Embedding Engine with ChromaDB default embeddings...")
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(
            name="disasterlink_docs",
            metadata={"hnsw:space": "cosine"}
        )

    def _build_structured_text(self, report: Dict[str, Any]) -> str:
        return (
            f"INCIDENT REPORT: {report['report_title']}\n"
            f"Organization: {report['org_name']} | Team: {report['team_name']}\n"
            f"Location: {report['district']}, {report['province']}\n"
            f"Date: {report['report_date']} | Severity: {report['severity_flag']}\n\n"
            f"DESCRIPTION: {report['report_body']}"
        )

    def ingest_reports(self, reports: List[Dict[str, Any]]):
        if not reports:
            logger.warning("No reports provided for ingestion.")
            return

        logger.info(f"Preparing to embed {len(reports)} reports...")
        
        ids = []
        texts = []
        metadatas = []

        try:
            # 1. Prepare Batches
            for report in reports:
                ids.append(f"report_{report['report_id']}")
                texts.append(self._build_structured_text(report))
                metadatas.append({
                    "report_id": int(report['report_id']),
                    "district": report['district'],
                    "province": report['province'],
                    "severity": report['severity_flag'],
                    "date": report['report_date'],
                    "org_name": report['org_name'],
                })

            # 2. Batch Encoding (Vectorization)
            # 3. Batch Upsert to Vector DB (ChromaDB computes embeddings automatically)
            self.collection.upsert(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully synchronized {len(reports)} reports to ChromaDB.")

        except Exception as e:
            logger.error(f"Critical failure during ingestion pipeline: {str(e)}")
            raise

if __name__ == "__main__":
    from db_connector import get_reports
    reports = get_reports()
    engine = EmbeddingEngine()
    engine.ingest_reports(reports)
