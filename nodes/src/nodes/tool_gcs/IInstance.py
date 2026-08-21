from ai.common.tool import tool_function
from rocketlib import IInstanceBase
from typing import List, Dict, Any
import tempfile
import os


def join_gcs_prefix(node_prefix: str, extra: str = '') -> str:
    """Join the configured bucket prefix with an optional runtime path.

    A non-empty node prefix always ends with ``/`` so ``list_blobs`` matches
    that directory rather than any key that merely starts with the same text.
    """
    full_prefix = ''
    if node_prefix:
        full_prefix = node_prefix.rstrip('/') + '/'
    if extra:
        full_prefix += extra.lstrip('/')
    return full_prefix


class IInstance(IInstanceBase):
    """GCS instance, providing tool functions for reading and listing files."""

    @tool_function(
        description=(
            'Download a file from Google Cloud Storage. Returns a dictionary containing '
            'the local temporary path of the downloaded file. Only the most recent download '
            'is retained; a new download deletes the previous temp file. Remaining files are '
            'removed when the node shuts down (endGlobal). Objects larger than the configured '
            'maxDownloadBytes are rejected.'
        ),
        args={'file_name': 'The name/path of the file in the bucket to download.'},
    )
    def download_file(self, file_name: str) -> Dict[str, Any]:
        client = self.glb.client
        if not client:
            return {'error': 'GCS client is not connected.'}

        bucket_name = self.glb.bucket_name
        if not bucket_name:
            return {'error': 'Bucket name not configured.'}

        file_name = join_gcs_prefix(self.glb.prefix, file_name)

        temp_path = None
        try:
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(file_name)
            blob.reload()
            size = blob.size or 0
            max_bytes = self.glb.max_download_bytes
            if size > max_bytes:
                return {
                    'error': (
                        f'Object {file_name!r} is {size} bytes, which exceeds '
                        f'maxDownloadBytes ({max_bytes}). Increase the limit or download a smaller object.'
                    )
                }

            # Download to a temporary file
            fd, temp_path = tempfile.mkstemp(prefix='gcs_')
            os.close(fd)
            blob.download_to_filename(temp_path)
            # Re-check after download: the object can change between reload() and fetch.
            actual_size = os.path.getsize(temp_path)
            if actual_size > max_bytes:
                os.remove(temp_path)
                temp_path = None
                return {
                    'error': (
                        f'Object {file_name!r} downloaded {actual_size} bytes, which exceeds '
                        f'maxDownloadBytes ({max_bytes}). Increase the limit or download a smaller object.'
                    )
                }

            self.glb.retain_temp_file(temp_path)
            return {'success': True, 'local_path': temp_path, 'size': actual_size}
        except Exception as e:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            return {'error': f'Failed to download file: {e}'}

    @tool_function(
        description='List files in the configured Google Cloud Storage bucket.',
        args={
            'prefix': 'Optional prefix to filter files.',
            'max_results': 'Maximum number of files to return (default 10).',
        },
    )
    def list_files(self, prefix: str = '', max_results: int = 10) -> List[str]:
        client = self.glb.client
        if not client:
            return ['Error: GCS client is not connected.']

        bucket_name = self.glb.bucket_name
        if not bucket_name:
            return ['Error: Bucket name not configured.']

        full_prefix = join_gcs_prefix(self.glb.prefix, prefix)

        try:
            bucket = client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=full_prefix, max_results=max_results)
            return [blob.name for blob in blobs]
        except Exception as e:
            return [f'Failed to list files: {e}']
