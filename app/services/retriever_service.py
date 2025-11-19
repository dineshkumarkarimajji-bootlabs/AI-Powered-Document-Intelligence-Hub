import os
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import uuid

from app.core.config import settings
from app.common_utils.text_splitters import chunk_text
from app.services.ocr_service import extract_text


class Retriever:
    def __init__(
        self,
        embedding_model_name=settings.EMBEDDING_MODEL,
        chunk_size=300,
        persist_dir=settings.CHROMA_DB_DIR
    ):
        self.chunk_size = chunk_size
        self.persist_dir = persist_dir

        os.makedirs(persist_dir, exist_ok=True)

        # Embedding model
        self.embedding_model = SentenceTransformer(embedding_model_name)

        # Embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )

        # Chroma client
        self.client = chromadb.PersistentClient(path=persist_dir)

    def get_collection_for_role(self, role: str):
        role = role.lower()
        collection_name = f"documents_{role}"

        existing = [c.name for c in self.client.list_collections()]

        if collection_name in existing:
            return self.client.get_collection(collection_name)

        return self.client.create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )

    def add_document(self, file_path: str, user: str, user_role: str):
        collection = self.get_collection_for_role(user_role)

        text = extract_text(file_path)
        if not text.strip():
            return {"message": "No text extracted"}

        chunks = chunk_text(text, self.chunk_size)
        file_name = os.path.basename(file_path)

        metadatas = [{
            "source": file_name,
            "user": user,
            "role": user_role
        } for _ in chunks]

        ids = [str(uuid.uuid4()) for _ in chunks]

        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids,
        )

        return {"message": "Indexed", "chunks": len(chunks)}

    def query(self, query_text: str, top_k: int = 5, user: str = None, user_role: str = None):
        collection = self.get_collection_for_role(user_role)
        where_filter = {}
        conditions = []

        if user:
            conditions.append({"user": {"$eq": user}})
        if user_role:
            conditions.append({"role": {"$eq": user_role}})

        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}

        results = collection.query(
            query_texts=[query_text],
            n_results=top_k * 2,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        final = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            final.append({
                "text": doc,
                "source": meta.get("source"),
                "score": float(dist),
                "user": meta.get("user"),
                "role": meta.get("role"),
            })

            if len(final) >= top_k:
                break

        return final

    def evaluate(self, query_text: str, retrieved_docs: list, ground_truth: str = None):
        if not retrieved_docs:
            return {"avg_similarity": 0.0, "hallucination_rate": 1.0}

        similarities = [1 / (1 + r["score"]) for r in retrieved_docs]
        avg_similarity = sum(similarities) / len(similarities)
        hallucination_rate = 1 - avg_similarity

        return {
            "avg_similarity": float(avg_similarity),
            "hallucination_rate": float(hallucination_rate)
        }
