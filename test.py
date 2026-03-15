print("Testing imports...")
try:
    from azure.keyvault.secrets import SecretClient
    print("✅ Azure KeyVault import successful!")
    from azure.identity import DefaultAzureCredential
    print("✅ Azure Identity import successful!")
except Exception as e:
    print(f"❌ Import failed: {e}")
