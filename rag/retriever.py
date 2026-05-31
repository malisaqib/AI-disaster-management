import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


load_dotenv()

DEFAULT_PATH = os.path.join(os.getcwd(), "chroma_db")
CHROMA_PATH = os.getenv("CHROMA_PATH", DEFAULT_PATH)

class RetrievalEngine:
    def __init__(self):
        try:
            logger.info(f"Connecting to ChromaDB at: {CHROMA_PATH}")
            self.client = chromadb.PersistentClient(path=CHROMA_PATH)
            self.collection = self.client.get_or_create_collection(
                name="disasterlink_docs",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Failed to initialize RetrievalEngine: {e}")
            raise

    def retrieve(self, query: str, top_k: int = 3, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        try:
            # Query the Vector Database (ChromaDB computes embeddings automatically)
            search_params = {
                "query_texts": [query],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"]
            }

            if filters:
                search_params["where"] = filters

            results = self.collection.query(**search_params)

            # 3. Format the output
            output = []
            
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
               
                similarity_score = round(1.0 - dist, 3)
                
                output.append({
                    "report_id": meta.get("report_id"),
                    "text": doc,
                    "metadata": meta,
                    "score": similarity_score
                })

            logger.info(f"Retrieved {len(output)} relevant documents for query: '{query}'")
            return output

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []

if __name__ == "__main__":
    try:
        engine = RetrievalEngine()
        question = "medical emergencies in Sindh"
        logger.info(f"Testing Query: {question}")
        
        search_results = engine.retrieve(question, top_k=3)
        
        for i, res in enumerate(search_results):
            print(f"\n--- Result {i+1} (Score: {res['score']}) ---")
            print(f"ID: {res['report_id']} | Location: {res['metadata']['district']}, {res['metadata']['province']}")
            print(f"Snippet: {res['text'][:150]}...")
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")

