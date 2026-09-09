#!/bin/bash
# Soft Rent a Car — Azure Deployment Script
# Run: chmod +x deploy/azure/deploy.sh && ./deploy/azure/deploy.sh

set -e

# ── Configuration ──────────────────────────────────────────────────────
RESOURCE_GROUP="rg-softrentacar"
LOCATION="eastus"
ACR_NAME="softrentacaracr"
APP_NAME="soft-rentacar-app"
ENVIRONMENT_NAME="soft-rentacar-env"

echo "🚗 Deploying Soft Rent a Car to Azure..."

# ── Login ──────────────────────────────────────────────────────────────
echo "→ Logging in to Azure..."
az login --output none

# ── Resource Group ─────────────────────────────────────────────────────
echo "→ Creating resource group: $RESOURCE_GROUP"
az group create --name $RESOURCE_GROUP --location $LOCATION --output none

# ── Container Registry ─────────────────────────────────────────────────
echo "→ Creating Container Registry: $ACR_NAME"
az acr create \
    --name $ACR_NAME \
    --resource-group $RESOURCE_GROUP \
    --sku Basic \
    --admin-enabled true \
    --output none

# ── Build & Push Docker Image ──────────────────────────────────────────
echo "→ Building and pushing Docker image..."
az acr build \
    --registry $ACR_NAME \
    --image softrentacar:latest \
    --file Dockerfile \
    . 

ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# ── Container Apps Environment ──────────────────────────────────────────
echo "→ Creating Container Apps environment..."
az containerapp env create \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --output none

# ── Deploy Container App ───────────────────────────────────────────────
echo "→ Deploying Container App: $APP_NAME"
az containerapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image "$ACR_LOGIN_SERVER/softrentacar:latest" \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --target-port 8501 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 1.0 \
    --memory 2.0Gi \
    --env-vars \
        "OPENAI_API_KEY=${OPENAI_API_KEY:-}" \
        "CARTO_API_KEY=${CARTO_API_KEY:-}" \
    --output none

APP_URL=$(az containerapp show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn -o tsv)

echo ""
echo "✅ Deployment complete!"
echo "🌐 App URL: https://$APP_URL"
echo ""
echo "📌 Next steps:"
echo "   1. Set environment secrets in Azure portal → Container App → Secrets"
echo "   2. Configure custom domain (optional)"
echo "   3. Set up Azure Monitor alerts"
