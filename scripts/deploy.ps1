#!/usr/bin/env pwsh

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$true)]
    [string]$Location,
    
    [string]$Environment = "production"
)

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🚀 DEPLOYING ELDER AI GUARDIAN TO AZURE               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host "Location: $Location" -ForegroundColor Yellow
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host ""

# Login to Azure
Write-Host "🔑 Logging into Azure..." -ForegroundColor Green
az login --only-show-errors

# Create resource group
Write-Host "`n📦 Creating resource group..." -ForegroundColor Green
az group create `
    --name $ResourceGroup `
    --location $Location `
    --tags Environment=$Environment

# Deploy Azure services
Write-Host "`n🚀 Deploying Azure services..." -ForegroundColor Green
az deployment group create `
    --resource-group $ResourceGroup `
    --template-file infrastructure/main.bicep `
    --parameters environment=$Environment

# Get deployment outputs
$outputs = az deployment group show `
    --resource-group $ResourceGroup `
    --name main `
    --query properties.outputs `
    --output json | ConvertFrom-Json

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "`n📋 Deployment outputs:" -ForegroundColor Cyan
$outputs.PSObject.Properties | ForEach-Object {
    Write-Host "  $($_.Name): $($_.Value.value)" -ForegroundColor White
}

# Build and push Docker image
Write-Host "`n🐳 Building Docker image..." -ForegroundColor Green
docker build -t elderai-guardian:latest .

# Tag for Azure Container Registry
if ($outputs.acrLoginServer) {
    $acrServer = $outputs.acrLoginServer.value
    docker tag elderai-guardian:latest "$acrServer/elderai-guardian:latest"
    
    Write-Host "`n📤 Pushing to ACR..." -ForegroundColor Green
    docker push "$acrServer/elderai-guardian:latest"
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     ✅ DEPLOYMENT COMPLETE!                                ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green