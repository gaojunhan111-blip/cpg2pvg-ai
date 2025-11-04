#!/bin/bash

# CPG2PVG-AI Secret Generation Script
# This script generates secure secrets for the application

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="cpg2pvg-ai"
SECRETS_FILE="k8s/secrets.yaml"
ENV_FILE=".env"

echo -e "${BLUE}🔐 CPG2PVG-AI Secret Generation Script${NC}"
echo "This script will generate secure secrets for production deployment."
echo

# Function to generate secure random value
generate_secret() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-${length}
}

# Function to generate base64 encoded value
encode_base64() {
    echo -n "$1" | base64
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command_exists openssl; then
    echo -e "${RED}❌ OpenSSL is required but not installed.${NC}"
    exit 1
fi

if ! command_exists kubectl; then
    echo -e "${RED}❌ kubectl is required but not installed.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo

# Check if we're in the right directory
if [[ ! -f "$SECRETS_FILE" ]]; then
    echo -e "${RED}❌ secrets.yaml not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Backup existing secrets file
if [[ -f "$SECRETS_FILE" && ! -f "${SECRETS_FILE}.backup" ]]; then
    echo -e "${YELLOW}💾 Creating backup of existing secrets...${NC}"
    cp "$SECRETS_FILE" "${SECRETS_FILE}.backup"
fi

echo -e "${YELLOW}🔑 Generating secure secrets...${NC}"

# Generate PostgreSQL passwords
echo "Generating PostgreSQL secrets..."
POSTGRES_PASSWORD=$(generate_secret 32)
POSTGRES_REPLICATION_PASSWORD=$(generate_secret 32)

# Generate Redis password
echo "Generating Redis secret..."
REDIS_PASSWORD=$(generate_secret 32)

# Generate MinIO credentials
echo "Generating MinIO credentials..."
MINIO_ACCESS_KEY=$(generate_secret 16 | tr '[:upper:]' '[:lower:]')
MINIO_SECRET_KEY=$(generate_secret 32)

# Generate application secrets
echo "Generating application secrets..."
APP_SECRET=$(generate_secret 64)
JWT_SECRET=$(openssl rand -hex 64)

# Generate Flower credentials
echo "Generating Flower credentials..."
FLOWER_USER="flower_admin"
FLOWER_PASSWORD=$(generate_secret 24)

echo -e "${GREEN}✅ Secret generation completed${NC}"
echo

# Display generated secrets (masked)
echo -e "${BLUE}📋 Generated Secrets (masked for security):${NC}"
echo "PostgreSQL Password: ${POSTGRES_PASSWORD:0:8}..."
echo "PostgreSQL Replication Password: ${POSTGRES_REPLICATION_PASSWORD:0:8}..."
echo "Redis Password: ${REDIS_PASSWORD:0:8}..."
echo "MinIO Access Key: $MINIO_ACCESS_KEY"
echo "MinIO Secret Key: ${MINIO_SECRET_KEY:0:8}..."
echo "Application Secret: ${APP_SECRET:0:16}..."
echo "JWT Secret: ${JWT_SECRET:0:16}..."
echo "Flower User: $FLOWER_USER"
echo "Flower Password: ${FLOWER_PASSWORD:0:8}..."
echo

# Ask user to confirm
read -p "Do you want to update the secrets files? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ Secret generation cancelled${NC}"
    exit 1
fi

# Update Kubernetes secrets file
echo -e "${YELLOW}📝 Updating Kubernetes secrets file...${NC}"

# Create temporary file with updated secrets
TEMP_SECRETS_FILE=$(mktemp)

# Read the original file and replace placeholders
while IFS= read -r line; do
    if [[ $line =~ \<BASE64_ENCODED_SECURE_PASSWORD\> ]]; then
        echo "  postgres-password: $(encode_base64 "$POSTGRES_PASSWORD")  # Generated securely"
    elif [[ $line =~ \<BASE64_ENCODED_REDIS_PASSWORD\> ]]; then
        echo "  redis-password: $(encode_base64 "$REDIS_PASSWORD")  # Generated securely"
    elif [[ $line =~ \<BASE64_ENCODED_MINIO_ACCESS_KEY\> ]]; then
        echo "  minio-access-key: $(encode_base64 "$MINIO_ACCESS_KEY")  # Generated securely"
    elif [[ $line =~ \<BASE64_ENCODED_MINIO_SECRET_KEY\> ]]; then
        echo "  minio-secret-key: $(encode_base64 "$MINIO_SECRET_KEY")  # Generated securely"
    elif [[ $line =~ \<BASE64_ENCODED_JWT_SECRET\> ]]; then
        echo "  jwt-secret: $(encode_base64 "$JWT_SECRET")  # Generated securely"
    elif [[ $line =~ \<BASE64_ENCODED_APP_SECRET\> ]]; then
        echo "  app-secret: $(encode_base64 "$APP_SECRET")  # Generated securely"
    else
        echo "$line"
    fi
done < "$SECRETS_FILE" > "$TEMP_SECRETS_FILE"

# Replace the original file
mv "$TEMP_SECRETS_FILE" "$SECRETS_FILE"

# Update other secret entries
sed -i.bak "s/password: eW91ci1zZWN1cmUtcG9zdGdyZXMtcGFzc3dvcmQ=/password: $(encode_base64 "$POSTGRES_PASSWORD")/" "$SECRETS_FILE"
sed -i.bak "s/replication-password: eW91ci1zZWN1cmUtcmVwbGljYXRpb24tcGFzc3dvcmQ=/replication-password: $(encode_base64 "$POSTGRES_REPLICATION_PASSWORD")/" "$SECRETS_FILE"
sed -i.bak "s/access-key: eW91ci1taW5pby1hY2Nlc3Mta2V5/access-key: $(encode_base64 "$MINIO_ACCESS_KEY")/" "$SECRETS_FILE"
sed -i.bak "s/secret-key: eW91ci1taW5pby1zZWNyZXQta2V5/secret-key: $(encode_base64 "$MINIO_SECRET_KEY")/" "$SECRETS_FILE"
rm "${SECRETS_FILE}.bak"

# Update flower auth secret
sed -i.bak "s/flower-auth: YWRtaW46YWRtaW4=/flower-auth: $(encode_base64 "$FLOWER_USER:$FLOWER_PASSWORD")/" "$SECRETS_FILE"
rm "${SECRETS_FILE}.bak"

echo -e "${GREEN}✅ Kubernetes secrets file updated${NC}"

# Create .env file for development
echo -e "${YELLOW}📝 Creating .env file for development...${NC}"

cat > "$ENV_FILE" << EOF
# CPG2PVG-AI Environment Variables
# Generated on $(date)
# SECURITY: These are generated secrets. Do not commit to version control!

# Database Configuration
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_REPLICATION_PASSWORD=$POSTGRES_REPLICATION_PASSWORD

# Redis Configuration
REDIS_PASSWORD=$REDIS_PASSWORD

# MinIO Configuration
MINIO_ROOT_USER=$MINIO_ACCESS_KEY
MINIO_ROOT_PASSWORD=$MINIO_SECRET_KEY
MINIO_ACCESS_KEY=$MINIO_ACCESS_KEY
MINIO_SECRET_KEY=$MINIO_SECRET_KEY

# Application Security
SECRET_KEY=$APP_SECRET
JWT_SECRET_KEY=$JWT_SECRET

# Flower Authentication
FLOWER_USER=$FLOWER_USER
FLOWER_PASSWORD=$FLOWER_PASSWORD

# Additional Configuration (add your values here)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_ANALYTICS_ID=
SENTRY_DSN=
SMTP_USERNAME=
SMTP_PASSWORD=
EOF

echo -e "${GREEN}✅ .env file created${NC}"

# Create k8s secret directly if kubectl is available
if command_exists kubectl && kubectl cluster-info &>/dev/null; then
    echo -e "${YELLOW}🚀 Applying secrets to Kubernetes cluster...${NC}"

    # Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

    # Apply secrets
    kubectl apply -f "$SECRETS_FILE" -n "$NAMESPACE"

    echo -e "${GREEN}✅ Secrets applied to Kubernetes cluster${NC}"
else
    echo -e "${YELLOW}⚠️  Kubernetes cluster not accessible. Secrets generated locally only.${NC}"
fi

# Security advice
echo
echo -e "${BLUE}🔒 Security Recommendations:${NC}"
echo "1. Store the generated secrets securely (password manager, vault, etc.)"
echo "2. Add $ENV_FILE to .gitignore if not already present"
echo "3. Rotate secrets regularly (recommended every 90 days)"
echo "4. Use Kubernetes External Secrets Operator for production"
echo "5. Enable audit logging for secret access"
echo

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
# Clean up any remaining temp files
rm -f /tmp/tmp.*

echo -e "${GREEN}✨ Secret generation completed successfully!${NC}"
echo
echo -e "${BLUE}Next steps:${NC}"
echo "1. Review the generated secrets"
echo "2. Add your API keys (OpenAI, etc.) to the .env file"
echo "3. Apply the secrets to your Kubernetes cluster"
echo "4. Update your deployment configuration if needed"
echo
echo -e "${YELLOW}⚠️  IMPORTANT: Never commit the actual secrets to version control!${NC}"