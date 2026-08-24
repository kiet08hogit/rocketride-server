from __future__ import annotations

from typing import Any

from rocketlib import IInstanceBase, tool_function

from .IGlobal import IGlobal


def _as_dict(args: Any) -> dict:
    return args if isinstance(args, dict) else {}


class IInstance(IInstanceBase):
    """Firestore instance, providing tool functions for reading and writing documents."""

    IGlobal: IGlobal

    @tool_function(
        description='Insert or update a document in a Firestore collection. If the document exists, it merges the data.',
        input_schema={
            'type': 'object',
            'required': ['data'],
            'properties': {
                'collection': {'type': 'string', 'description': 'The collection name.'},
                'document_id': {
                    'type': 'string',
                    'description': 'The ID of the document to set. If empty, a new ID will be generated.',
                },
                'data': {
                    'type': 'object',
                    'description': 'The JSON dictionary to store in the document.',
                },
            },
        },
    )
    def set_document(self, args: dict | None = None) -> str:
        args = _as_dict(args)
        collection = str(args.get('collection') or '')
        document_id = str(args.get('document_id') or '')
        data = args.get('data') if isinstance(args.get('data'), dict) else {}

        client = self.IGlobal.client
        if not client:
            return 'Error: Firestore client is not connected.'

        if not collection:
            collection = self.IGlobal.collection

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
        input_schema={
            'type': 'object',
            'required': ['document_id'],
            'properties': {
                'collection': {'type': 'string', 'description': 'The collection name.'},
                'document_id': {'type': 'string', 'description': 'The document ID.'},
            },
        },
    )
    def get_document(self, args: dict | None = None) -> dict[str, Any]:
        args = _as_dict(args)
        collection = str(args.get('collection') or '')
        document_id = str(args.get('document_id') or '')

        client = self.IGlobal.client
        if not client:
            return {'error': 'Firestore client is not connected.'}

        if not collection:
            collection = self.IGlobal.collection

        try:
            doc = client.collection(collection).document(document_id).get()
            if doc.exists:
                return doc.to_dict()
            else:
                return {'error': f'Document {document_id} not found.'}
        except Exception as e:
            return {'error': f'Failed to get document: {e}'}
