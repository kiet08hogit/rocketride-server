from ai.common.tool import tool_function
from rocketlib import IInstanceBase
from typing import Dict, Any


class IInstance(IInstanceBase):
    """Firestore instance, providing tool functions for reading and writing documents."""

    @tool_function(
        description='Insert or update a document in a Firestore collection. If the document exists, it merges the data.',
        args={
            'collection': 'The collection name.',
            'document_id': 'The ID of the document to set. If empty, a new ID will be generated.',
            'data': 'The JSON dictionary to store in the document.',
        },
    )
    def set_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> str:
        client = self.glb.client
        if not client:
            return 'Error: Firestore client is not connected.'

        if not collection:
            collection = self.glb.collection

        try:
            coll_ref = client.collection(collection)
            if document_id:
                doc_ref = coll_ref.document(document_id)
                doc_ref.set(data, merge=True)
                return f'Successfully set document {document_id} in {collection}.'
            else:
                _, doc_ref = coll_ref.add(data)
                return f'Successfully added document with ID {doc_ref.id} to {collection}.'
        except Exception as e:
            return f'Failed to set document: {e}'

    @tool_function(
        description='Get a single document from a Firestore collection.',
        args={'collection': 'The collection name.', 'document_id': 'The document ID.'},
    )
    def get_document(self, collection: str, document_id: str) -> Dict[str, Any]:
        client = self.glb.client
        if not client:
            return {'error': 'Firestore client is not connected.'}

        if not collection:
            collection = self.glb.collection

        try:
            doc = client.collection(collection).document(document_id).get()
            if doc.exists:
                return doc.to_dict()
            else:
                return {'error': f'Document {document_id} not found.'}
        except Exception as e:
            return {'error': f'Failed to get document: {e}'}
