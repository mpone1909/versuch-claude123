"""
Embeddings Module

Schnittstelle zur Erzeugung von Embeddings aus Texten.
Aktuell: Placeholder-Implementierung für strukturellen Aufbau.
Zukünftig: Integration mit echten Embedding-Modellen (OpenAI, Sentence Transformers, etc.)
"""

from typing import List, Dict, Any, Optional
import logging
import hashlib

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Fehler bei der Embedding-Erzeugung"""
    pass


class EmbeddingProvider:
    """
    Abstrakte Basis für Embedding-Provider.

    Diese Klasse definiert die Schnittstelle für Embedding-Generierung.
    Konkrete Implementierungen können später verschiedene Modelle nutzen.
    """

    def __init__(self, model_name: str = "placeholder", embedding_dim: int = 384):
        """
        Initialisiert den Embedding Provider.

        Args:
            model_name: Name des Embedding-Modells
            embedding_dim: Dimensionalität der Embeddings
        """
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        logger.info(f"EmbeddingProvider initialisiert: {model_name} (dim={embedding_dim})")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Erzeugt Embeddings für eine Liste von Texten.

        Args:
            texts: Liste von Texten

        Returns:
            Liste von Embedding-Vektoren (jeweils Liste von Floats)

        Raises:
            EmbeddingError: Bei Problemen in der Embedding-Erzeugung
        """
        if not texts:
            return []

        logger.info(f"Erzeuge Embeddings für {len(texts)} Texte")

        try:
            embeddings = []
            for text in texts:
                embedding = self._generate_single_embedding(text)
                embeddings.append(embedding)

            return embeddings
        except Exception as e:
            logger.error(f"Fehler bei Embedding-Erzeugung: {e}")
            raise EmbeddingError(f"Konnte Embeddings nicht erzeugen: {e}") from e

    def _generate_single_embedding(self, text: str) -> List[float]:
        """
        Erzeugt ein Embedding für einen einzelnen Text.

        HINWEIS: Dies ist eine Placeholder-Implementierung!
        Sie erzeugt deterministische "Pseudo-Embeddings" basierend auf dem Text-Hash.

        Für Produktion: Ersetzen durch echtes Embedding-Modell.

        Args:
            text: Eingabetext

        Returns:
            Embedding-Vektor
        """
        # Erzeuge deterministischen Hash
        text_hash = hashlib.sha256(text.encode()).digest()

        # Konvertiere zu normalisierten Float-Werten
        embedding = []
        for i in range(self.embedding_dim):
            byte_val = text_hash[i % len(text_hash)]
            # Normalisiere auf [-1, 1]
            normalized = (byte_val / 255.0) * 2 - 1
            embedding.append(normalized)

        return embedding

    def get_embedding_dimension(self) -> int:
        """
        Gibt die Dimensionalität der Embeddings zurück.

        Returns:
            Embedding-Dimension
        """
        return self.embedding_dim


class TextChunker:
    """
    Hilfklasse zum Aufteilen langer Texte in Chunks für Embeddings.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialisiert den Text Chunker.

        Args:
            chunk_size: Maximale Länge eines Chunks (in Zeichen)
            chunk_overlap: Überlappung zwischen Chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Teilt einen Text in überlappende Chunks auf.

        Args:
            text: Eingabetext

        Returns:
            Liste von Text-Chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)

            # Nächster Start mit Überlappung
            start = end - self.chunk_overlap

            # Verhindere Endlosschleife
            if start + self.chunk_size >= len(text) and chunks:
                break

        return chunks

    def chunk_texts_with_metadata(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunked mehrere Texte und erhält Metadaten.

        Args:
            texts: Liste von Texten
            metadata: Optional, Metadaten pro Text

        Returns:
            Liste von Dictionaries mit {text, chunk_index, original_index, metadata}
        """
        if metadata is None:
            metadata = [{} for _ in texts]

        results = []

        for orig_idx, (text, meta) in enumerate(zip(texts, metadata)):
            chunks = self.chunk_text(text)

            for chunk_idx, chunk in enumerate(chunks):
                results.append({
                    "text": chunk,
                    "chunk_index": chunk_idx,
                    "original_index": orig_idx,
                    "metadata": meta,
                })

        return results
