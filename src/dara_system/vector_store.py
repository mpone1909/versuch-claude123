"""
Vector Store Module

Abstraktion für Vektor-Speicherung und Ähnlichkeitssuche.
Aktuell: In-Memory-Implementierung für Entwicklung und Tests.
Zukünftig: Integration mit Vektordatenbanken (Pinecone, Weaviate, ChromaDB, etc.)
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


@dataclass
class VectorEntry:
    """Repräsentiert einen Eintrag im Vector Store."""
    id: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    text: Optional[str] = None


class VectorStoreError(Exception):
    """Fehler bei Vector Store Operationen"""
    pass


class InMemoryVectorStore:
    """
    In-Memory Vector Store für Entwicklung und Tests.

    Speichert Vektoren im RAM und führt einfache Ähnlichkeitssuche durch.
    Für Produktion sollte dies durch eine echte Vektordatenbank ersetzt werden.
    """

    def __init__(self, embedding_dim: Optional[int] = None):
        """
        Initialisiert den Vector Store.

        Args:
            embedding_dim: Erwartete Dimensionalität der Vektoren (optional)
        """
        self.embedding_dim = embedding_dim
        self.entries: Dict[str, VectorEntry] = {}
        logger.info(f"InMemoryVectorStore initialisiert (dim={embedding_dim})")

    def add_vectors(
        self,
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
        texts: Optional[List[str]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Fügt Vektoren zum Store hinzu.

        Args:
            vectors: Liste von Embedding-Vektoren
            metadata: Optional, Metadaten pro Vektor
            texts: Optional, zugehörige Texte
            ids: Optional, IDs für die Einträge (werden generiert wenn nicht angegeben)

        Returns:
            Liste der IDs der eingefügten Einträge

        Raises:
            VectorStoreError: Bei Dimensionskonflikten oder anderen Fehlern
        """
        if not vectors:
            return []

        # Validiere Dimensionen
        if self.embedding_dim is None:
            self.embedding_dim = len(vectors[0])

        for vec in vectors:
            if len(vec) != self.embedding_dim:
                raise VectorStoreError(
                    f"Vektor-Dimension {len(vec)} stimmt nicht mit "
                    f"Store-Dimension {self.embedding_dim} überein"
                )

        # Bereite optionale Parameter vor
        if metadata is None:
            metadata = [{} for _ in vectors]
        if texts is None:
            texts = [None] * len(vectors)
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in vectors]

        # Füge Einträge hinzu
        added_ids = []
        for vector, meta, text, entry_id in zip(vectors, metadata, texts, ids):
            entry = VectorEntry(
                id=entry_id,
                vector=vector,
                metadata=meta,
                text=text
            )
            self.entries[entry_id] = entry
            added_ids.append(entry_id)

        logger.info(f"Hinzugefügt: {len(added_ids)} Vektoren zum Store")
        return added_ids

    def similarity_search(
        self,
        query_vector: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[VectorEntry, float]]:
        """
        Sucht die k ähnlichsten Vektoren zu einem Query-Vektor.

        Args:
            query_vector: Such-Vektor
            k: Anzahl der zurückzugebenden Ergebnisse
            filter_metadata: Optional, Filter auf Metadaten

        Returns:
            Liste von (VectorEntry, similarity_score) Tupeln, sortiert nach Ähnlichkeit

        Raises:
            VectorStoreError: Bei Dimensionskonflikten
        """
        if len(query_vector) != self.embedding_dim:
            raise VectorStoreError(
                f"Query-Vektor-Dimension {len(query_vector)} != Store-Dimension {self.embedding_dim}"
            )

        # Filtere Einträge nach Metadaten falls angegeben
        candidates = self.entries.values()
        if filter_metadata:
            candidates = [
                entry for entry in candidates
                if self._matches_filter(entry.metadata, filter_metadata)
            ]

        # Berechne Ähnlichkeiten
        similarities = []
        query_np = np.array(query_vector)

        for entry in candidates:
            entry_np = np.array(entry.vector)
            # Cosine Similarity
            similarity = self._cosine_similarity(query_np, entry_np)
            similarities.append((entry, similarity))

        # Sortiere nach Ähnlichkeit (absteigend)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Gib Top-k zurück
        return similarities[:k]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Berechnet Cosine Similarity zwischen zwei Vektoren.

        Args:
            vec1, vec2: Numpy Arrays

        Returns:
            Similarity Score (0-1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _matches_filter(
        self,
        metadata: Dict[str, Any],
        filter_dict: Dict[str, Any]
    ) -> bool:
        """
        Prüft ob Metadaten einem Filter entsprechen.

        Args:
            metadata: Zu prüfende Metadaten
            filter_dict: Filter-Bedingungen

        Returns:
            True wenn alle Filter-Bedingungen erfüllt sind
        """
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True

    def get_by_id(self, entry_id: str) -> Optional[VectorEntry]:
        """
        Holt einen Eintrag anhand seiner ID.

        Args:
            entry_id: ID des Eintrags

        Returns:
            VectorEntry oder None wenn nicht gefunden
        """
        return self.entries.get(entry_id)

    def delete_by_id(self, entry_id: str) -> bool:
        """
        Löscht einen Eintrag anhand seiner ID.

        Args:
            entry_id: ID des zu löschenden Eintrags

        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        if entry_id in self.entries:
            del self.entries[entry_id]
            logger.info(f"Eintrag {entry_id} gelöscht")
            return True
        return False

    def clear(self):
        """Löscht alle Einträge aus dem Store."""
        count = len(self.entries)
        self.entries.clear()
        logger.info(f"Store geleert: {count} Einträge entfernt")

    def count(self) -> int:
        """
        Gibt die Anzahl der gespeicherten Vektoren zurück.

        Returns:
            Anzahl der Einträge
        """
        return len(self.entries)
