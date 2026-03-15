"""
Azure Event Service for Event Grid and Service Bus operations
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid
import json

from app.core.logging import logger

# Try to import Azure Event Grid with fallback
try:
    from azure.eventgrid import EventGridPublisherClient, EventGridEvent
    from azure.core.credentials import AzureKeyCredential
    AZURE_EVENTGRID_AVAILABLE = True
except ImportError:
    AZURE_EVENTGRID_AVAILABLE = False
    EventGridPublisherClient = None
    EventGridEvent = None
    AzureKeyCredential = None
    logger.warning("⚠️ Azure Event Grid not available - using mock")

# Try to import Azure Service Bus with fallback
try:
    from azure.servicebus import ServiceBusClient, ServiceBusMessage
    AZURE_SERVICEBUS_AVAILABLE = True
except ImportError:
    AZURE_SERVICEBUS_AVAILABLE = False
    ServiceBusClient = None
    ServiceBusMessage = None
    logger.warning("⚠️ Azure Service Bus not available - using mock")


class EventService:
    """
    Service for Azure Event Grid and Service Bus operations
    Handles event publishing and message queuing
    """
    
    def __init__(self, servicebus_client: Optional[ServiceBusClient] = None, eventgrid_client: Optional[EventGridPublisherClient] = None):
        self.servicebus_client = servicebus_client
        self.eventgrid_client = eventgrid_client
        self.is_healthy = False
        
        # Track availability
        self.servicebus_available = AZURE_SERVICEBUS_AVAILABLE and servicebus_client is not None
        self.eventgrid_available = AZURE_EVENTGRID_AVAILABLE and eventgrid_client is not None
        
        # In-memory mock storage
        self.mock_events = []
        self.mock_queues = {}
        self.mock_topics = {}
        
    async def initialize(self):
        """Initialize the event service"""
        self.is_healthy = True
        logger.info("=" * 60)
        logger.info("Initializing Event Service...")
        logger.info(f"  Azure Service Bus Available: {self.servicebus_available}")
        logger.info(f"  Azure Event Grid Available: {self.eventgrid_available}")
        logger.info("=" * 60)
    
    # ==================== Event Grid Methods ====================
    
    async def publish_event(
        self,
        topic_endpoint: str,
        events: List[Dict[str, Any]],
        topic_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish events to Event Grid topic
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        if not self.eventgrid_available or not self.eventgrid_client:
            # Mock event publishing
            for event in events:
                event_with_metadata = {
                    "id": event.get("id", str(uuid.uuid4())),
                    "event_type": event.get("event_type", "Custom.Event"),
                    "subject": event.get("subject", "/elders/unknown"),
                    "data": event.get("data", {}),
                    "data_version": event.get("data_version", "1.0"),
                    "metadata": {
                        "published_at": timestamp,
                        "topic": topic_endpoint
                    }
                }
                self.mock_events.append(event_with_metadata)
            
            logger.info(f"📨 [MOCK] Published {len(events)} events to Event Grid")
            
            return {
                "success": True,
                "event_id": event_id,
                "published_count": len(events),
                "simulated": True,
                "timestamp": timestamp
            }
        
        try:
            # Create EventGrid events
            grid_events = []
            for event in events:
                grid_event = EventGridEvent(
                    id=event.get("id", str(uuid.uuid4())),
                    event_type=event.get("event_type", "Custom.Event"),
                    subject=event.get("subject", "/elders/unknown"),
                    data=event.get("data", {}),
                    data_version=event.get("data_version", "1.0")
                )
                grid_events.append(grid_event)
            
            # Send events
            await self.eventgrid_client.send(grid_events)
            
            logger.info(f"📨 Published {len(events)} events to Event Grid")
            
            return {
                "success": True,
                "event_id": event_id,
                "published_count": len(events),
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to publish events: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "event_id": event_id
            }
    
    async def get_events(
        self,
        filter: Optional[Dict] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get published events (mock only)
        """
        if not self.eventgrid_available:
            # Mock get events
            events = self.mock_events.copy()
            
            # Apply filter if provided
            if filter:
                filtered_events = []
                for event in events:
                    matches = True
                    for key, value in filter.items():
                        if key in event and event[key] != value:
                            matches = False
                            break
                    if matches:
                        filtered_events.append(event)
                events = filtered_events
            
            return events[:limit]
        
        # In production, you'd query Event Grid for dead letters or use a separate storage
        logger.warning("Getting events from Event Grid is not directly supported - use a separate event store")
        return []
    
    # ==================== Service Bus Methods ====================
    
    async def send_message(
        self,
        queue_name: str,
        message_body: Union[str, Dict, bytes],
        message_id: Optional[str] = None,
        content_type: str = "application/json",
        time_to_live: Optional[int] = None  # seconds
    ) -> Dict[str, Any]:
        """
        Send a message to a Service Bus queue
        """
        msg_id = message_id or str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        if not self.servicebus_available or not self.servicebus_client:
            # Mock message sending
            if queue_name not in self.mock_queues:
                self.mock_queues[queue_name] = []
            
            message = {
                "message_id": msg_id,
                "body": message_body,
                "content_type": content_type,
                "sent_at": timestamp,
                "time_to_live": time_to_live
            }
            
            self.mock_queues[queue_name].append(message)
            
            logger.info(f"📨 [MOCK] Sent message to queue '{queue_name}': {msg_id}")
            
            return {
                "success": True,
                "message_id": msg_id,
                "queue_name": queue_name,
                "simulated": True,
                "timestamp": timestamp
            }
        
        try:
            # Create Service Bus message
            if isinstance(message_body, (dict, list)):
                message_body = json.dumps(message_body)
            
            message = ServiceBusMessage(
                body=message_body,
                message_id=msg_id,
                content_type=content_type,
                time_to_live=time_to_live
            )
            
            # Get sender and send message
            sender = self.servicebus_client.get_queue_sender(queue_name)
            async with sender:
                await sender.send_messages(message)
            
            logger.info(f"📨 Sent message to queue '{queue_name}': {msg_id}")
            
            return {
                "success": True,
                "message_id": msg_id,
                "queue_name": queue_name,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to send message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message_id": msg_id,
                "queue_name": queue_name
            }
    
    async def receive_messages(
        self,
        queue_name: str,
        max_messages: int = 10,
        max_wait_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from a Service Bus queue
        """
        if not self.servicebus_available or not self.servicebus_client:
            # Mock receiving messages
            if queue_name not in self.mock_queues:
                return []
            
            messages = self.mock_queues[queue_name][:max_messages]
            self.mock_queues[queue_name] = self.mock_queues[queue_name][max_messages:]
            
            logger.info(f"📨 [MOCK] Received {len(messages)} messages from queue '{queue_name}'")
            
            return messages
        
        try:
            receiver = self.servicebus_client.get_queue_receiver(queue_name)
            received_messages = []
            
            async with receiver:
                messages = await receiver.receive_messages(
                    max_message_count=max_messages,
                    max_wait_time=max_wait_time
                )
                
                for msg in messages:
                    received_messages.append({
                        "message_id": msg.message_id,
                        "body": str(msg),
                        "content_type": msg.content_type,
                        "delivery_count": msg.delivery_count,
                        "enqueued_time": msg.enqueued_time.isoformat() if msg.enqueued_time else None,
                        "expires_at": msg.expires_at.isoformat() if msg.expires_at else None
                    })
                    await receiver.complete_message(msg)
            
            logger.info(f"📨 Received {len(received_messages)} messages from queue '{queue_name}'")
            
            return received_messages
            
        except Exception as e:
            logger.error(f"❌ Failed to receive messages: {str(e)}")
            return []
    
    async def send_to_topic(
        self,
        topic_name: str,
        message_body: Union[str, Dict, bytes],
        message_id: Optional[str] = None,
        content_type: str = "application/json"
    ) -> Dict[str, Any]:
        """
        Send a message to a Service Bus topic
        """
        msg_id = message_id or str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        if not self.servicebus_available or not self.servicebus_client:
            # Mock topic sending
            if topic_name not in self.mock_topics:
                self.mock_topics[topic_name] = []
            
            message = {
                "message_id": msg_id,
                "body": message_body,
                "content_type": content_type,
                "sent_at": timestamp
            }
            
            self.mock_topics[topic_name].append(message)
            
            logger.info(f"📨 [MOCK] Sent message to topic '{topic_name}': {msg_id}")
            
            return {
                "success": True,
                "message_id": msg_id,
                "topic_name": topic_name,
                "simulated": True,
                "timestamp": timestamp
            }
        
        try:
            # Create Service Bus message
            if isinstance(message_body, (dict, list)):
                message_body = json.dumps(message_body)
            
            message = ServiceBusMessage(
                body=message_body,
                message_id=msg_id,
                content_type=content_type
            )
            
            # Get sender and send message
            sender = self.servicebus_client.get_topic_sender(topic_name)
            async with sender:
                await sender.send_messages(message)
            
            logger.info(f"📨 Sent message to topic '{topic_name}': {msg_id}")
            
            return {
                "success": True,
                "message_id": msg_id,
                "topic_name": topic_name,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to send message to topic: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message_id": msg_id,
                "topic_name": topic_name
            }
    
    async def receive_from_subscription(
        self,
        topic_name: str,
        subscription_name: str,
        max_messages: int = 10,
        max_wait_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from a Service Bus topic subscription
        """
        if not self.servicebus_available or not self.servicebus_client:
            # Mock receiving from subscription
            if topic_name not in self.mock_topics:
                return []
            
            messages = self.mock_topics[topic_name][:max_messages]
            self.mock_topics[topic_name] = self.mock_topics[topic_name][max_messages:]
            
            logger.info(f"📨 [MOCK] Received {len(messages)} messages from topic '{topic_name}' subscription '{subscription_name}'")
            
            return messages
        
        try:
            receiver = self.servicebus_client.get_subscription_receiver(
                topic_name=topic_name,
                subscription_name=subscription_name
            )
            received_messages = []
            
            async with receiver:
                messages = await receiver.receive_messages(
                    max_message_count=max_messages,
                    max_wait_time=max_wait_time
                )
                
                for msg in messages:
                    received_messages.append({
                        "message_id": msg.message_id,
                        "body": str(msg),
                        "content_type": msg.content_type,
                        "delivery_count": msg.delivery_count,
                        "enqueued_time": msg.enqueued_time.isoformat() if msg.enqueued_time else None,
                        "expires_at": msg.expires_at.isoformat() if msg.expires_at else None
                    })
                    await receiver.complete_message(msg)
            
            logger.info(f"📨 Received {len(received_messages)} messages from topic '{topic_name}' subscription '{subscription_name}'")
            
            return received_messages
            
        except Exception as e:
            logger.error(f"❌ Failed to receive messages from subscription: {str(e)}")
            return []
    
    async def create_queue(self, queue_name: str) -> bool:
        """
        Create a queue (mock only)
        """
        if queue_name not in self.mock_queues:
            self.mock_queues[queue_name] = []
            logger.info(f"📁 [MOCK] Created queue: {queue_name}")
        return True
    
    async def create_topic(self, topic_name: str) -> bool:
        """
        Create a topic (mock only)
        """
        if topic_name not in self.mock_topics:
            self.mock_topics[topic_name] = []
            logger.info(f"📁 [MOCK] Created topic: {topic_name}")
        return True
    
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        return self.is_healthy
    
    async def close(self):
        """Close the event service"""
        if self.servicebus_client:
            await self.servicebus_client.close()
        logger.info("EventService closed")