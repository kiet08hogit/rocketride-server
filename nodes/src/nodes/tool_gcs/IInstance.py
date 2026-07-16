from ai.common.tool import tool_function
from rocketlib import IInstanceBase
from typing import List, Dict, Any
import tempfile
import os

class IInstance(IInstanceBase):
    """GCS instance, providing tool functions for reading and listing files."""

    @tool_function(
        description="Download a file from Google Cloud Storage. Returns a dictionary containing the local temporary path of the downloaded file.",
        args={
            "file_name": "The name/path of the file in the bucket to download."
        }
    )
    def download_file(self, file_name: str) -> Dict[str, Any]:
        client = self.glb.client
        if not client:
            return {"error": "GCS client is not connected."}
        
        bucket_name = self.glb.bucket_name
        if not bucket_name:
            return {"error": "Bucket name not configured."}
            
        # Optional prefix prefixing
        if self.glb.prefix:
            file_name = f"{self.glb.prefix.rstrip('/')}/{file_name.lstrip('/')}"
            
        try:
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(file_name)
            
            # Download to a temporary file
            fd, temp_path = tempfile.mkstemp(prefix="gcs_")
            os.close(fd)
            blob.download_to_filename(temp_path)
            
            return {"success": True, "local_path": temp_path}
        except Exception as e:
            return {"error": f"Failed to download file: {e}"}

    @tool_function(
        description="List files in the configured Google Cloud Storage bucket.",
        args={
            "prefix": "Optional prefix to filter files.",
            "max_results": "Maximum number of files to return (default 10)."
        }
    )
    def list_files(self, prefix: str = "", max_results: int = 10) -> List[str]:
        client = self.glb.client
        if not client:
            return ["Error: GCS client is not connected."]
            
        bucket_name = self.glb.bucket_name
        if not bucket_name:
            return ["Error: Bucket name not configured."]
            
        # Combine node-level prefix and runtime prefix
        full_prefix = ""
        if self.glb.prefix:
            full_prefix = self.glb.prefix.rstrip('/') + '/'
        if prefix:
            full_prefix += prefix.lstrip('/')
            
        try:
            bucket = client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=full_prefix, max_results=max_results)
            return [blob.name for blob in blobs]
        except Exception as e:
            return [f"Failed to list files: {e}"]
