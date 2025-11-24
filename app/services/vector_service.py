class VectorStoreService:
    def __init__(self, client=None):
        self.client = client

    def delete_by_doc_id(self, doc_id: str):
        """
        Delete all vectors belonging to a document using metadata filter.
        """

        try:
            self.client.delete(where={"document_id": doc_id})
        except:
            pass

        return True
