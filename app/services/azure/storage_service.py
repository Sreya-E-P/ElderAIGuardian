"""
Azure Storage Service for blob storage operations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from app.core.logging import logger

# Try to import Azure Storage with fallback
try:
    from azure.storage.blob import BlobServiceClient, ContainerClient
    AZURE_STORAGE_AVAILABLE = True
except ImportError:
    AZURE_STORAGE_AVAILABLE = False
    BlobServiceClient = None
    ContainerClient = None
    logger.warning("⚠️ Azure Storage not available - using mock")


class StorageService:
    """
    Service for Azure Blob Storage operations
    Handles file uploads, downloads, and management
    """
    
    def __init__(self, blob_client: Optional[BlobServiceClient] = None):
        self.blob_client = blob_client
        self.is_healthy = False
        self.storage_available = AZURE_STORAGE_AVAILABLE and blob_client is not None
        
        # In-memory mock storage
        self.mock_storage = {}
        
    async def initialize(self):
        """Initialize the storage service"""
        self.is_healthy = True
        logger.info("=" * 60)
        logger.info("Initializing Storage Service...")
        logger.info(f"  Azure Storage Available: {self.storage_available}")
        logger.info("=" * 60)
    
    async def upload_blob(
        self,
        container_name: str,
        blob_name: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Upload a blob to storage
        """
        blob_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        if not self.storage_available or not self.blob_client:
            # Mock storage
            if container_name not in self.mock_storage:
                self.mock_storage[container_name] = {}
            
            self.mock_storage[container_name][blob_name] = {
                "data": data,
                "content_type": content_type,
                "metadata": metadata or {},
                "blob_id": blob_id,
                "uploaded_at": timestamp,
                "size": len(data)
            }
            
            logger.info(f"📦 [MOCK] Uploaded blob {blob_name} to container {container_name} ({len(data)} bytes)")
            
            return {
                "success": True,
                "blob_id": blob_id,
                "blob_name": blob_name,
                "container_name": container_name,
                "url": f"https://mockstorage.blob.core.windows.net/{container_name}/{blob_name}",
                "size": len(data),
                "uploaded_at": timestamp,
                "simulated": True
            }
        
        try:
            # Get container client
            container_client = self.blob_client.get_container_client(container_name)
            
            # Ensure container exists
            try:
                await container_client.create_container()
            except Exception:
                # Container might already exist
                pass
            
            # Get blob client
            blob_client = container_client.get_blob_client(blob_name)
            
            # Upload data
            await blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings={"content_type": content_type} if content_type else None,
                metadata=metadata
            )
            
            logger.info(f"📦 Uploaded blob {blob_name} to container {container_name} ({len(data)} bytes)")
            
            return {
                "success": True,
                "blob_id": blob_id,
                "blob_name": blob_name,
                "container_name": container_name,
                "url": blob_client.url,
                "size": len(data),
                "uploaded_at": timestamp,
                "etag": getattr(blob_client, 'etag', None)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to upload blob: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "blob_name": blob_name,
                "container_name": container_name
            }
    
    async def download_blob(
        self,
        container_name: str,
        blob_name: str
    ) -> Optional[bytes]:
        """
        Download a blob from storage
        """
        if not self.storage_available or not self.blob_client:
            # Mock storage
            if (container_name in self.mock_storage and 
                blob_name in self.mock_storage[container_name]):
                return self.mock_storage[container_name][blob_name]["data"]
            return None
        
        try:
            blob_client = self.blob_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            download_stream = await blob_client.download_blob()
            data = await download_stream.readall()
            
            logger.info(f"📥 Downloaded blob {blob_name} from container {container_name} ({len(data)} bytes)")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to download blob: {str(e)}")
            return None
    
    async def delete_blob(
        self,
        container_name: str,
        blob_name: str
    ) -> bool:
        """
        Delete a blob from storage
        """
        if not self.storage_available or not self.blob_client:
            # Mock storage
            if (container_name in self.mock_storage and 
                blob_name in self.mock_storage[container_name]):
                del self.mock_storage[container_name][blob_name]
                return True
            return False
        
        try:
            blob_client = self.blob_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            await blob_client.delete_blob()
            logger.info(f"🗑️ Deleted blob {blob_name} from container {container_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete blob: {str(e)}")
            return False
    
    async def list_blobs(
        self,
        container_name: str,
        prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List blobs in a container
        """
        if not self.storage_available or not self.blob_client:
            # Mock storage
            if container_name not in self.mock_storage:
                return []
            
            blobs = []
            for blob_name, blob_data in self.mock_storage[container_name].items():
                if prefix and not blob_name.startswith(prefix):
                    continue
                blobs.append({
                    "name": blob_name,
                    "size": blob_data["size"],
                    "content_type": blob_data["content_type"],
                    "metadata": blob_data["metadata"],
                    "uploaded_at": blob_data["uploaded_at"]
                })
            return blobs
        
        try:
            container_client = self.blob_client.get_container_client(container_name)
            
            blobs = []
            async for blob in container_client.list_blobs(name_starts_with=prefix):
                blobs.append({
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None,
                    "metadata": blob.metadata,
                    "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                    "etag": blob.etag
                })
            
            return blobs
            
        except Exception as e:
            logger.error(f"❌ Failed to list blobs: {str(e)}")
            return []
    
    async def blob_exists(
        self,
        container_name: str,
        blob_name: str
    ) -> bool:
        """
        Check if a blob exists
        """
        if not self.storage_available or not self.blob_client:
            # Mock storage
            return (container_name in self.mock_storage and 
                    blob_name in self.mock_storage[container_name])
        
        try:
            blob_client = self.blob_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            return await blob_client.exists()
            
        except Exception:
            return False
    
    async def get_blob_properties(
        self,
        container_name: str,
        blob_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get blob properties
        """
        if not self.storage_available or not self.blob_client:
            # Mock storage
            if (container_name in self.mock_storage and 
                blob_name in self.mock_storage[container_name]):
                blob_data = self.mock_storage[container_name][blob_name]
                return {
                    "name": blob_name,
                    "size": blob_data["size"],
                    "content_type": blob_data["content_type"],
                    "metadata": blob_data["metadata"],
                    "uploaded_at": blob_data["uploaded_at"]
                }
            return None
        
        try:
            blob_client = self.blob_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            properties = await blob_client.get_blob_properties()
            
            return {
                "name": blob_name,
                "size": properties.size,
                "content_type": properties.content_settings.content_type if properties.content_settings else None,
                "metadata": properties.metadata,
                "created_on": properties.creation_time.isoformat() if properties.creation_time else None,
                "last_modified": properties.last_modified.isoformat() if properties.last_modified else None,
                "etag": properties.etag
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get blob properties: {str(e)}")
            return None
    
    async def create_container(
        self,
        container_name: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Create a container
        """
        if not self.storage_available or not self.blob_client:
            # Mock storage
            if container_name not in self.mock_storage:
                self.mock_storage[container_name] = {}
            return True
        
        try:
            container_client = self.blob_client.get_container_client(container_name)
            await container_client.create_container(metadata=metadata)
            logger.info(f"📁 Created container: {container_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create container: {str(e)}")
            return False
    
    async def delete_container(
        self,
        container_name: str
    ) -> bool:
        """
        Delete a container
        """
        if not self.storage_available or not self.blob_client:
            # Mock storage
            if container_name in self.mock_storage:
                del self.mock_storage[container_name]
            return True
        
        try:
            container_client = self.blob_client.get_container_client(container_name)
            await container_client.delete_container()
            logger.info(f"🗑️ Deleted container: {container_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete container: {str(e)}")
            return False
    
    async def container_exists(
        self,
        container_name: str
    ) -> bool:
        """
        Check if a container exists
        """
        if not self.storage_available or not self.blob_client:
            # Mock storage
            return container_name in self.mock_storage
        
        try:
            container_client = self.blob_client.get_container_client(container_name)
            return await container_client.exists()
            
        except Exception:
            return False
    
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        return self.is_healthy
    
    async def close(self):
        """Close the storage service"""
        logger.info("StorageService closed")