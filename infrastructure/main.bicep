@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment name')
param environment string = 'production'

@description('Unique suffix for resources')
param uniqueSuffix string = uniqueString(resourceGroup().id)

// ============================================================================
// APP SERVICE PLAN
// ============================================================================
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: 'asp-elderai-${uniqueSuffix}'
  location: location
  sku: {
    name: 'P1v2'
    tier: 'PremiumV2'
    capacity: 2
  }
  properties: {
    reserved: true // Linux
  }
}

// ============================================================================
// WEB APP
// ============================================================================
resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: 'app-elderai-${uniqueSuffix}'
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'APP_ENV'
          value: environment
        }
        {
          name: 'AZURE_FOUNDRY_ENDPOINT'
          value: '@Microsoft.KeyVault(SecretUri=https://kv-elderai-${uniqueSuffix}.vault.azure.net/secrets/azure-foundry-endpoint)'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: '@Microsoft.KeyVault(SecretUri=https://kv-elderai-${uniqueSuffix}.vault.azure.net/secrets/azure-openai-endpoint)'
        }
        {
          name: 'COSMOS_DB_CONNECTION'
          value: '@Microsoft.KeyVault(SecretUri=https://kv-elderai-${uniqueSuffix}.vault.azure.net/secrets/cosmos-db-connection)'
        }
        {
          name: 'REDIS_HOST'
          value: redisElderai.outputs.hostName
        }
      ]
      alwaysOn: true
      http20Enabled: true
      websocketsEnabled: true
    }
    httpsOnly: true
  }
  
  resource appSettings 'config' = {
    name: 'appsettings'
    properties: {}
  }
}

// ============================================================================
// COSMOS DB
// ============================================================================
resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: 'cosmos-elderai-${uniqueSuffix}'
  location: location
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

// ============================================================================
// REDIS CACHE
// ============================================================================
resource redis 'Microsoft.Cache/redis@2023-08-01' = {
  name: 'redis-elderai-${uniqueSuffix}'
  location: location
  properties: {
    sku: {
      name: 'Standard'
      family: 'C'
      capacity: 1
    }
    enableNonSslPort: false
    redisConfiguration: {
      maxmemoryPolicy: 'allkeys-lru'
    }
  }
}

// ============================================================================
// KEY VAULT
// ============================================================================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-elderai-${uniqueSuffix}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableSoftDelete: true
    enablePurgeProtection: true
  }
}

// ============================================================================
// APPLICATION INSIGHTS
// ============================================================================
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-elderai-${uniqueSuffix}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-elderai-${uniqueSuffix}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output cosmosDbEndpoint string = cosmosDb.properties.documentEndpoint
output redisHost string = redis.properties.hostName
output keyVaultUri string = keyVault.properties.vaultUri
output appInsightsKey string = appInsights.properties.InstrumentationKey