#!/usr/bin/env python3
"""
Seed threat intelligence data into Cosmos DB for MCP threat feed
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.logging import setup_logging, logger
from azure.cosmos import CosmosClient

async def seed_threats():
    """Seed threat intelligence data"""
    
    logger.info("=" * 60)
    logger.info("Seeding threat intelligence data to Cosmos DB")
    logger.info("=" * 60)
    
    # Connect to Cosmos DB
    try:
        client = CosmosClient.from_connection_string(settings.COSMOS_DB_CONNECTION)
        database = client.get_database_client(settings.COSMOS_DB_DATABASE or "elderaidb")
        
        # Get or create container
        container_name = "threat_intel"
        try:
            container = database.get_container_client(container_name)
            logger.info(f"Connected to container: {container_name}")
        except:
            from azure.cosmos.partition_key import PartitionKey
            container = database.create_container(
                id=container_name,
                partition_key=PartitionKey(path="/type"),
                offer_throughput=400
            )
            logger.info(f"Created container: {container_name}")
        
        # Seed phishing threats
        phishing_threats = [
            {
                "id": str(uuid.uuid4()),
                "type": "phishing",
                "data": {
                    "url": "fake-bank-verification.com",
                    "impersonating": "chase.com",
                    "technique": "email phishing"
                },
                "severity": "HIGH",
                "source": "APWG",
                "confidence": 0.95,
                "active": True,
                "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "type": "phishing",
                "data": {
                    "url": "secure-account-update.net",
                    "impersonating": "paypal.com",
                    "technique": "SMS phishing"
                },
                "severity": "CRITICAL",
                "source": "PhishTank",
                "confidence": 0.98,
                "active": True,
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "type": "phishing",
                "data": {
                    "url": "microsoft-verify-account.com",
                    "impersonating": "microsoft.com",
                    "technique": "tech support"
                },
                "severity": "HIGH",
                "source": "Microsoft Threat Intelligence",
                "confidence": 0.99,
                "active": True,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        # Seed phone scam threats
        phone_threats = [
            {
                "id": str(uuid.uuid4()),
                "type": "phone_scam",
                "data": {
                    "number": "+15551234567",
                    "scam_type": "tech_support",
                    "caller_id": "Microsoft Support"
                },
                "severity": "HIGH",
                "source": "FTC",
                "reports": 234,
                "active": True,
                "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "type": "phone_scam",
                "data": {
                    "number": "+15559876543",
                    "scam_type": "irs_impersonation",
                    "caller_id": "IRS"
                },
                "severity": "CRITICAL",
                "source": "FTC",
                "reports": 567,
                "active": True,
                "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "type": "phone_scam",
                "data": {
                    "number": "+15551112222",
                    "scam_type": "grandparent_scam",
                    "caller_id": "Grandson"
                },
                "severity": "HIGH",
                "source": "AARP",
                "reports": 89,
                "active": True,
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        ]
        
        # Seed email scam threats
        email_threats = [
            {
                "id": str(uuid.uuid4()),
                "type": "email_scam",
                "data": {
                    "domain": "secure-verify.net",
                    "impersonating": "microsoft.com",
                    "subject": "Your account has been locked"
                },
                "severity": "HIGH",
                "source": "Spamhaus",
                "reports": 45,
                "active": True,
                "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "type": "email_scam",
                "data": {
                    "domain": "account-security.com",
                    "impersonating": "paypal.com",
                    "subject": "Suspicious login attempt"
                },
                "severity": "HIGH",
                "source": "Spamhaus",
                "reports": 123,
                "active": True,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        # Seed current tactics
        tactic_threats = [
            {
                "id": str(uuid.uuid4()),
                "type": "tactic",
                "data": {
                    "name": "Fake Package Delivery",
                    "description": "Scammers send fake delivery notifications with tracking links",
                    "indicators": ["USPS", "FedEx", "UPS", "tracking number"]
                },
                "severity": "HIGH",
                "source": "FBI IC3",
                "active": True,
                "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "type": "tactic",
                "data": {
                    "name": "AI Voice Cloning",
                    "description": "Scammers use AI to clone family member voices for grandparent scams",
                    "indicators": ["help me", "emergency", "money", "don't tell anyone"]
                },
                "severity": "CRITICAL",
                "source": "FTC",
                "active": True,
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        ]
        
        # Insert all threats
        all_threats = phishing_threats + phone_threats + email_threats + tactic_threats
        
        for threat in all_threats:
            try:
                container.upsert_item(threat)
                logger.info(f"✅ Added threat: {threat['type']} - {threat.get('data', {}).get('url', threat.get('data', {}).get('number', threat.get('data', {}).get('name', 'unknown')))}")
            except Exception as e:
                logger.error(f"❌ Failed to add threat: {e}")
        
        logger.info("=" * 60)
        logger.info(f"✅ Successfully seeded {len(all_threats)} threats to Cosmos DB")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Failed to seed threats: {e}")
        raise

if __name__ == "__main__":
    setup_logging()
    asyncio.run(seed_threats())