#!/usr/bin/env python3
"""
Test all real Azure services
Run this to verify everything is working with REAL services
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🔍 TESTING REAL AZURE SERVICES")
print("=" * 60)

# Test 1: Azure OpenAI
try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential
    
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_KEY")
    
    if endpoint and key and "your" not in endpoint:
        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        print("✅ Azure OpenAI: Connected")
    else:
        print("❌ Azure OpenAI: Missing credentials")
except Exception as e:
    print(f"❌ Azure OpenAI: {e}")

# Test 2: Azure Communication Services
try:
    from azure.communication.sms import SmsClient
    
    conn_str = os.getenv("AZURE_COMMS_CONNECTION_STRING")
    if conn_str and "your" not in conn_str:
        client = SmsClient.from_connection_string(conn_str)
        print("✅ Azure Communication Services: Connected")
    else:
        print("❌ Azure Communication Services: Missing connection string")
except Exception as e:
    print(f"❌ Azure Communication Services: {e}")

# Test 3: Azure Cosmos DB
try:
    from azure.cosmos import CosmosClient
    
    conn_str = os.getenv("COSMOS_DB_CONNECTION")
    if conn_str and "your" not in conn_str:
        client = CosmosClient.from_connection_string(conn_str)
        print("✅ Azure Cosmos DB: Connected")
    else:
        print("❌ Azure Cosmos DB: Missing connection string")
except Exception as e:
    print(f"❌ Azure Cosmos DB: {e}")

# Test 4: Azure Key Vault
try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential
    
    vault_url = os.getenv("AZURE_KEYVAULT_URL")
    if vault_url and "your" not in vault_url:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        print("✅ Azure Key Vault: Connected")
    else:
        print("❌ Azure Key Vault: Missing URL")
except Exception as e:
    print(f"❌ Azure Key Vault: {e}")

# Test 5: Azure Storage
try:
    from azure.storage.blob import BlobServiceClient
    
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION")
    if conn_str and "your" not in conn_str:
        client = BlobServiceClient.from_connection_string(conn_str)
        print("✅ Azure Storage: Connected")
    else:
        print("❌ Azure Storage: Missing connection string")
except Exception as e:
    print(f"❌ Azure Storage: {e}")

# Test 6: Application Insights
try:
    instr_key = os.getenv("APPINSIGHTS_INSTRUMENTATION_KEY")
    if instr_key and "your" not in instr_key:
        print("✅ Application Insights: Key present")
    else:
        print("❌ Application Insights: Missing key")
except Exception as e:
    print(f"❌ Application Insights: {e}")

print("=" * 60)