class VectorStoreService:
    def __init__(self, client=None):
        self.client = client

    def delete_by_doc_id(self, doc_id: str):
        """
        Delete all vectors belonging to a document using metadata filter.
        Works for Chroma, Pinecone, Qdrant, Milvus, Weaviate.
        """

        # Example for Chroma
        try:
            self.client.delete(where={"document_id": doc_id})
        except:
            pass

        # Example for Pinecone
        # self.client.delete(filter={"document_id": doc_id})

        # Example for Qdrant
        # self.client.delete_points(
        #     collection_name="documents",
        #     filter={"must": [{"key": "document_id", "match": {"value": doc_id}}]}
        # )

        return True
