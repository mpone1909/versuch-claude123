"""
RAG Pipeline Module

Retrieval-Augmented Generation Pipeline für kontextbasierte Antworten.
Kombiniert Vector Store Retrieval mit (zukünftiger) LLM-Integration.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from .vector_store import InMemoryVectorStore, VectorEntry
from .embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """Ergebnis einer RAG-Query."""
    query: str
    retrieved_contexts: List[Dict[str, Any]]
    answer: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RAGPipelineError(Exception):
    """Fehler in der RAG Pipeline"""
    pass


class RAGPipeline:
    """
    RAG (Retrieval-Augmented Generation) Pipeline.

    Workflow:
    1. Query-Text wird in Embedding umgewandelt
    2. Ähnliche Kontexte werden aus Vector Store abgerufen
    3. (Zukünftig) Kontexte + Query werden an LLM gesendet
    4. Ergebnis wird zurückgegeben

    Aktuell: Fokus auf Retrieval, LLM-Integration vorbereitet aber nicht implementiert.
    """

    def __init__(
        self,
        vector_store: InMemoryVectorStore,
        embedding_provider: EmbeddingProvider,
        top_k: int = 5,
        similarity_threshold: float = 0.5
    ):
        """
        Initialisiert die RAG Pipeline.

        Args:
            vector_store: Vector Store für Retrieval
            embedding_provider: Provider für Query-Embeddings
            top_k: Anzahl der abzurufenden Kontexte
            similarity_threshold: Minimale Similarity für Ergebnisse
        """
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

        logger.info(
            f"RAGPipeline initialisiert (top_k={top_k}, "
            f"threshold={similarity_threshold})"
        )

    def query(
        self,
        query_text: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
        custom_top_k: Optional[int] = None
    ) -> RAGResult:
        """
        Führt eine RAG-Query aus.

        Args:
            query_text: Suchanfrage als Text
            filter_metadata: Optional, Filter für Metadaten
            custom_top_k: Optional, überschreibt Standard-top_k

        Returns:
            RAGResult mit abgerufenen Kontexten und (zukünftiger) Antwort

        Raises:
            RAGPipelineError: Bei Fehlern in der Pipeline
        """
        try:
            # 1. Erzeuge Query-Embedding
            logger.info(f"RAG Query: '{query_text[:100]}...'")
            query_embeddings = self.embedding_provider.get_embeddings([query_text])
            query_vector = query_embeddings[0]

            # 2. Retrieval aus Vector Store
            k = custom_top_k if custom_top_k is not None else self.top_k
            results = self.vector_store.similarity_search(
                query_vector=query_vector,
                k=k,
                filter_metadata=filter_metadata
            )

            # 3. Filtere nach Similarity Threshold
            filtered_results = [
                (entry, score) for entry, score in results
                if score >= self.similarity_threshold
            ]

            # 4. Formatiere Kontexte
            contexts = []
            for entry, score in filtered_results:
                context = {
                    "id": entry.id,
                    "text": entry.text,
                    "metadata": entry.metadata,
                    "similarity_score": score,
                }
                contexts.append(context)

            logger.info(f"Retrieved {len(contexts)} contexts (threshold={self.similarity_threshold})")

            # 5. (Zukünftig) LLM-Generierung
            # Aktuell: Placeholder
            answer = self._generate_placeholder_answer(query_text, contexts)

            return RAGResult(
                query=query_text,
                retrieved_contexts=contexts,
                answer=answer,
                metadata={
                    "num_contexts": len(contexts),
                    "top_k": k,
                    "threshold": self.similarity_threshold,
                }
            )

        except Exception as e:
            logger.error(f"Fehler in RAG Pipeline: {e}")
            raise RAGPipelineError(f"Query fehlgeschlagen: {e}") from e

    def _generate_placeholder_answer(
        self,
        query: str,
        contexts: List[Dict[str, Any]]
    ) -> str:
        """
        Generiert eine Placeholder-Antwort.

        HINWEIS: Dies ist ein Platzhalter für echte LLM-Integration!

        Args:
            query: Ursprüngliche Query
            contexts: Abgerufene Kontexte

        Returns:
            Placeholder-Antwort
        """
        if not contexts:
            return f"[Placeholder] Keine relevanten Kontexte für Query gefunden: '{query}'"

        # Einfacher Placeholder: Zeige Anzahl gefundener Kontexte
        context_summary = f"Gefunden: {len(contexts)} relevante Kontexte"
        top_context = contexts[0]

        answer = (
            f"[Placeholder-Antwort]\n"
            f"Query: {query}\n"
            f"{context_summary}\n"
            f"Top-Kontext (Score: {top_context['similarity_score']:.3f}): "
            f"{top_context['text'][:100] if top_context['text'] else 'N/A'}..."
        )

        return answer

    def index_documents(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Indexiert Dokumente für späteres Retrieval.

        Args:
            texts: Liste von Texten zum Indexieren
            metadata: Optional, Metadaten pro Text

        Returns:
            Liste der IDs der indexierten Dokumente
        """
        logger.info(f"Indexiere {len(texts)} Dokumente")

        # Erzeuge Embeddings
        embeddings = self.embedding_provider.get_embeddings(texts)

        # Füge zu Vector Store hinzu
        ids = self.vector_store.add_vectors(
            vectors=embeddings,
            metadata=metadata,
            texts=texts
        )

        logger.info(f"Erfolgreich {len(ids)} Dokumente indexiert")
        return ids

    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die Pipeline zurück.

        Returns:
            Dictionary mit Statistiken
        """
        return {
            "vector_store_count": self.vector_store.count(),
            "embedding_dim": self.embedding_provider.get_embedding_dimension(),
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
        }
