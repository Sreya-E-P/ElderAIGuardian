"""
Azure Search Service for cognitive search operations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from app.core.logging import logger

# Try to import Azure Search with fallback
try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_SEARCH_AVAILABLE = True
except ImportError:
    AZURE_SEARCH_AVAILABLE = False
    SearchClient = None
    SearchIndexClient = None
    AzureKeyCredential = None
    logger.warning("⚠️ Azure Search not available - using mock")


class SearchService:
    """
    Service for Azure Cognitive Search operations
    Handles document indexing and search queries
    """
    
    def __init__(self, search_client: Optional[SearchClient] = None):
        self.search_client = search_client
        self.is_healthy = False
        self.search_available = AZURE_SEARCH_AVAILABLE and search_client is not None
        
        # In-memory mock search storage
        self.mock_documents = []
        self.mock_indexes = {}
        
    async def initialize(self):
        """Initialize the search service"""
        self.is_healthy = True
        logger.info("=" * 60)
        logger.info("Initializing Search Service...")
        logger.info(f"  Azure Search Available: {self.search_available}")
        logger.info("=" * 60)
    
    async def search(
        self,
        query: str,
        filter: Optional[str] = None,
        top: int = 10,
        skip: int = 0,
        select: Optional[List[str]] = None,
        order_by: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform a search query
        """
        if not self.search_available or not self.search_client:
            # Mock search
            results = []
            for doc in self.mock_documents:
                # Simple text matching
                if query.lower() in doc.get("content", "").lower() or query.lower() in doc.get("title", "").lower():
                    results.append(doc)
            
            # Apply pagination
            paginated_results = results[skip:skip+top]
            
            logger.info(f"🔍 [MOCK] Search for '{query}' returned {len(paginated_results)} results")
            
            return {
                "results": paginated_results,
                "count": len(results),
                "query": query,
                "top": top,
                "skip": skip,
                "simulated": True
            }
        
        try:
            # Perform actual search
            search_options = {
                "top": top,
                "skip": skip,
                "include_total_count": True
            }
            
            if filter:
                search_options["filter"] = filter
            
            if select:
                search_options["select"] = select
            
            if order_by:
                search_options["order_by"] = order_by
            
            results = []
            async for result in self.search_client.search(query, **search_options):
                results.append(result)
            
            logger.info(f"🔍 Search for '{query}' returned {len(results)} results")
            
            return {
                "results": results,
                "count": len(results),
                "query": query,
                "top": top,
                "skip": skip
            }
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            return {
                "results": [],
                "count": 0,
                "error": str(e),
                "query": query
            }
    
    async def suggest(
        self,
        query: str,
        suggester_name: str,
        top: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get search suggestions
        """
        if not self.search_available or not self.search_client:
            # Mock suggestions
            suggestions = []
            for doc in self.mock_documents:
                if query.lower() in doc.get("title", "").lower():
                    suggestions.append({
                        "text": doc.get("title", ""),
                        "document": doc
                    })
            
            return suggestions[:top]
        
        try:
            suggestions = []
            async for suggestion in self.search_client.suggest(
                query,
                suggester_name,
                top=top
            ):
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Suggest failed: {str(e)}")
            return []
    
    async def autocomplete(
        self,
        query: str,
        suggester_name: str
    ) -> List[str]:
        """
        Get autocomplete suggestions
        """
        if not self.search_available or not self.search_client:
            # Mock autocomplete
            suggestions = []
            for doc in self.mock_documents:
                title = doc.get("title", "")
                if query.lower() in title.lower():
                    suggestions.append(title)
            
            return list(set(suggestions))[:10]
        
        try:
            results = await self.search_client.autocomplete(
                query,
                suggester_name
            )
            
            return [r["text"] for r in results]
            
        except Exception as e:
            logger.error(f"❌ Autocomplete failed: {str(e)}")
            return []
    
    async def index_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Index documents for searching
        """
        if not self.search_available or not self.search_client:
            # Mock indexing
            for doc in documents:
                if "id" not in doc:
                    doc["id"] = str(uuid.uuid4())
                self.mock_documents.append(doc)
            
            logger.info(f"📄 [MOCK] Indexed {len(documents)} documents")
            
            return {
                "success": True,
                "indexed_count": len(documents),
                "simulated": True
            }
        
        try:
            result = await self.search_client.upload_documents(documents)
            
            logger.info(f"📄 Indexed {len(documents)} documents")
            
            return {
                "success": True,
                "indexed_count": len(documents),
                "results": result
            }
            
        except Exception as e:
            logger.error(f"❌ Indexing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_documents(
        self,
        document_keys: List[str]
    ) -> Dict[str, Any]:
        """
        Delete documents from index
        """
        if not self.search_available or not self.search_client:
            # Mock deletion
            self.mock_documents = [
                doc for doc in self.mock_documents
                if doc.get("id") not in document_keys
            ]
            
            logger.info(f"🗑️ [MOCK] Deleted {len(document_keys)} documents")
            
            return {
                "success": True,
                "deleted_count": len(document_keys),
                "simulated": True
            }
        
        try:
            documents_to_delete = [{"id": key} for key in document_keys]
            result = await self.search_client.delete_documents(documents_to_delete)
            
            logger.info(f"🗑️ Deleted {len(document_keys)} documents")
            
            return {
                "success": True,
                "deleted_count": len(document_keys),
                "results": result
            }
            
        except Exception as e:
            logger.error(f"❌ Deletion failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_document(
        self,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID
        """
        if not self.search_available or not self.search_client:
            # Mock get
            for doc in self.mock_documents:
                if doc.get("id") == document_id:
                    return doc
            return None
        
        try:
            document = await self.search_client.get_document(document_id)
            return document
            
        except Exception as e:
            logger.error(f"❌ Get document failed: {str(e)}")
            return None
    
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        return self.is_healthy
    
    async def close(self):
        """Close the search service"""
        logger.info("SearchService closed")