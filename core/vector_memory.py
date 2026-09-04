# ========== vector_memory.py ==========
# ChromaDB orqali semantic xotira tizimi
# Foydalanuvchining bilimlarini vektor shaklida saqlash va qidirish

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class VectorMemory:
    """ChromaDB orqali semantic xotira"""

    def __init__(self, collection_name: str = "knowledge_base"):
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._embedder = None
        self._init()

    def _init(self):
        """ChromaDB va embedding modelini ishga tushirish"""
        try:
            import chromadb
            from chromadb.config import Settings

            os.makedirs(CHROMA_PATH, exist_ok=True)

            self._client = chromadb.PersistentClient(path=CHROMA_PATH)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Mikasa AI semantic knowledge base"},
            )

            try:
                from chromadb.utils import embedding_functions

                self._embedder = (
                    embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=EMBEDDING_MODEL
                    )
                )
            except Exception as e:
                logger.warning(f"Embedding function xatolik: {e}, default ishlatiladi")
                self._embedder = None

            logger.info(f"VectorMemory initialized: {CHROMA_PATH}")
        except ImportError:
            logger.error("ChromaDB o'rnatilmagan: pip install chromadb")
            self._client = None
        except Exception as e:
            logger.error(f"VectorMemory init xatolik: {e}")
            self._client = None

    def add_document(
        self, text: str, metadata: Dict[str, Any] = None, doc_id: str = None
    ) -> bool:
        """Hujjatni vektor bazasiga qo'shish"""
        if not self._client:
            return False

        try:
            if doc_id is None:
                import uuid

                doc_id = str(uuid.uuid4())

            if metadata is None:
                metadata = {}
            metadata["added_at"] = datetime.now().isoformat()

            if self._embedder:
                embeddings = self._embedder([text])
            else:
                embeddings = None

            self._collection.add(
                documents=[text],
                ids=[doc_id],
                metadatas=[metadata],
                embeddings=embeddings,
            )
            logger.info(f"Document added: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Document qo'shish xatolik: {e}")
            return False

    def add_file(self, file_path: str, metadata: Dict[str, Any] = None) -> bool:
        """Fayldan hujjat yuklab olish"""
        if not os.path.exists(file_path):
            logger.error(f"Fayl topilmadi: {file_path}")
            return False

        try:
            text = self._read_file(file_path)
            if not text.strip():
                return False

            if metadata is None:
                metadata = {}
            metadata["source"] = file_path
            metadata["file_name"] = os.path.basename(file_path)
            metadata["file_type"] = os.path.splitext(file_path)[1].lower()

            return self.add_document(text, metadata)
        except Exception as e:
            logger.error(f"File yuklash xatolik: {e}")
            return False

    def _read_file(self, file_path: str) -> str:
        """Faylni o'qish"""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif ext in (
            ".md",
            ".py",
            ".js",
            ".html",
            ".css",
            ".json",
            ".yaml",
            ".yml",
            ".xml",
        ):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif ext == ".pdf":
            try:
                import pypdf

                reader = pypdf.PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                logger.warning("pypdf o'rnatilmagan")
                return ""
            except Exception as e:
                logger.error(f"PDF o'qish xatolik: {e}")
                return ""

        elif ext in (".docx", ".doc"):
            try:
                from docx import Document

                doc = Document(file_path)
                return "\n".join([p.text for p in doc.paragraphs])
            except ImportError:
                logger.warning("python-docx o'rnatilmagan")
                return ""
            except Exception as e:
                logger.error(f"DOCX o'qish xatolik: {e}")
                return ""

        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()[:10000]

    def search(
        self, query: str, n_results: int = 5, filter_metadata: Dict = None
    ) -> List[Dict]:
        """Semantic qidiruv"""
        if not self._client:
            return []

        try:
            where = None
            if filter_metadata:
                where = filter_metadata

            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            docs = []
            if results and results.get("ids"):
                for i in range(len(results["ids"][0])):
                    docs.append(
                        {
                            "id": results["ids"][0][i],
                            "text": results["documents"][0][i]
                            if results.get("documents")
                            else "",
                            "metadata": results["metadatas"][0][i]
                            if results.get("metadatas")
                            else {},
                            "distance": results["distances"][0][i]
                            if results.get("distances")
                            else 1.0,
                            "relevance": 1.0 - results["distances"][0][i]
                            if results.get("distances")
                            else 0.0,
                        }
                    )

            return docs
        except Exception as e:
            logger.error(f"Search xatolik: {e}")
            return []

    def search_by_keyword(self, keyword: str, n_results: int = 10) -> List[Dict]:
        """Kalit so'z bo'yicha qidiruv (chamadan tezroq)"""
        if not self._client:
            return []

        try:
            results = self._collection.get(
                where=None, include=["documents", "metadatas"]
            )

            keyword_lower = keyword.lower()
            matches = []

            if results and results.get("ids"):
                for i in range(len(results["ids"])):
                    text = results["documents"][i] if results.get("documents") else ""
                    if keyword_lower in text.lower():
                        matches.append(
                            {
                                "id": results["ids"][i],
                                "text": text[:500],
                                "metadata": results["metadatas"][i]
                                if results.get("metadatas")
                                else {},
                            }
                        )
                        if len(matches) >= n_results:
                            break

            return matches
        except Exception as e:
            logger.error(f"Keyword search xatolik: {e}")
            return []

    def get_relevant_context(self, query: str, max_chars: int = 4000) -> str:
        """Prompt uchun relevant kontekst olish"""
        results = self.search(query, n_results=5)

        if not results:
            return ""

        context_parts = ["\n\n=== BILIM BAZASIDAN ==="]
        total_chars = 0

        for doc in results:
            if doc["relevance"] < 0.3:
                continue

            text = doc["text"]
            source = doc.get("metadata", {}).get("source", "Noma'lum manba")

            if total_chars + len(text) > max_chars:
                break

            context_parts.append(f"\n[Manba: {source}]")
            context_parts.append(text[:2000])
            total_chars += len(text)

        context_parts.append("=" * 30)
        return "\n".join(context_parts)

    def delete(self, doc_id: str) -> bool:
        """Hujjatni o'chirish"""
        if not self._client:
            return False

        try:
            self._collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Delete xatolik: {e}")
            return False

    def count(self) -> int:
        """Hujjatlar sonini olish"""
        if not self._client:
            return 0
        return self._collection.count()

    def get_all_metadata(self) -> List[Dict]:
        """Barcha metadata larni olish"""
        if not self._client:
            return []

        try:
            results = self._collection.get(include=["metadatas"])
            if results and results.get("metadatas"):
                return results["metadatas"]
            return []
        except Exception as e:
            logger.error(f"Get all metadata xatolik: {e}")
            return []


_vector_memory_instance: Optional[VectorMemory] = None


def get_vector_memory() -> VectorMemory:
    """Global vector memory instance"""
    global _vector_memory_instance
    if _vector_memory_instance is None:
        _vector_memory_instance = VectorMemory()
    return _vector_memory_instance
