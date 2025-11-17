"""Tests für Vector Store Module"""

import pytest
from src.dara_system.vector_store import InMemoryVectorStore, VectorEntry, VectorStoreError


class TestInMemoryVectorStore:
    """Tests für InMemoryVectorStore"""

    def test_initialization(self):
        """Test: Vector Store Initialisierung"""
        store = InMemoryVectorStore(embedding_dim=128)
        assert store.embedding_dim == 128
        assert store.count() == 0

    def test_add_vectors(self):
        """Test: Vektoren hinzufügen"""
        store = InMemoryVectorStore(embedding_dim=3)

        vectors = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        texts = ["text1", "text2"]
        metadata = [{"key": "value1"}, {"key": "value2"}]

        ids = store.add_vectors(vectors, metadata=metadata, texts=texts)

        assert len(ids) == 2
        assert store.count() == 2

    def test_dimension_mismatch(self):
        """Test: Fehler bei falscher Dimension"""
        store = InMemoryVectorStore(embedding_dim=3)

        vectors = [[1.0, 2.0, 3.0], [4.0, 5.0]]  # Zweiter Vektor falsche Dimension

        with pytest.raises(VectorStoreError):
            store.add_vectors(vectors)

    def test_similarity_search(self):
        """Test: Ähnlichkeitssuche"""
        store = InMemoryVectorStore(embedding_dim=3)

        # Füge Vektoren hinzu
        vectors = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
        ]
        store.add_vectors(vectors)

        # Suche nach ähnlichem Vektor
        query = [0.9, 0.1, 0.0]
        results = store.similarity_search(query, k=2)

        assert len(results) == 2
        # Erster Result sollte [1,0,0] sein (am ähnlichsten)
        assert results[0][1] > results[1][1]  # Höherer Similarity Score

    def test_get_by_id(self):
        """Test: Abrufen nach ID"""
        store = InMemoryVectorStore(embedding_dim=2)

        ids = store.add_vectors([[1.0, 2.0]], ids=["test_id"])

        entry = store.get_by_id("test_id")
        assert entry is not None
        assert entry.id == "test_id"
        assert entry.vector == [1.0, 2.0]

    def test_delete_by_id(self):
        """Test: Löschen nach ID"""
        store = InMemoryVectorStore(embedding_dim=2)

        store.add_vectors([[1.0, 2.0]], ids=["test_id"])
        assert store.count() == 1

        deleted = store.delete_by_id("test_id")
        assert deleted is True
        assert store.count() == 0

    def test_clear(self):
        """Test: Store leeren"""
        store = InMemoryVectorStore(embedding_dim=2)

        store.add_vectors([[1.0, 2.0], [3.0, 4.0]])
        assert store.count() == 2

        store.clear()
        assert store.count() == 0

    def test_metadata_filter(self):
        """Test: Filterung nach Metadaten"""
        store = InMemoryVectorStore(embedding_dim=2)

        metadata = [
            {"category": "A"},
            {"category": "B"},
            {"category": "A"},
        ]

        store.add_vectors([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], metadata=metadata)

        # Suche nur in Kategorie A
        results = store.similarity_search(
            [1.0, 0.0],
            k=5,
            filter_metadata={"category": "A"}
        )

        assert len(results) == 2  # Nur 2 Einträge in Kategorie A
