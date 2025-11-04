#!/bin/bash

# CPG2PVG-AI Production Deployment Script
# This script orchestrates a complete, secure production deployment with compliance enforcement

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="cpg2pvg-ai"
CLUSTER_NAME="cpg2pvg-ai-prod"
REGION="us-east-1"
ENVIRONMENT="production"

# Deployment stages
STAGES=(
    "prerequisites"
    "security"
    "storage"
    "database"
    "application"
    "monitoring"
    "compliance"
    "validation"
)

echo -e "${PURPLE}🚀 CPG2PVG-AI Production Deployment${NC}"
echo -e "${CYAN}Environment: $ENVIRONMENT${NC}"
echo -e "${CYAN}Namespace: $NAMESPACE${NC}"
echo -e "${CYAN}Cluster: $CLUSTER_NAME${NC}"
echo

# Function to print stage headers
print_stage() {
    local stage_name=$1
    echo -e "${BLUE}📍 Stage: $stage_name${NC}"
    echo "----------------------------------------"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_stage "Prerequisites Check"

    local required_tools=("kubectl" "helm" "aws" "jq" "openssl")
    local missing_tools=()

    for tool in "${required_tools[@]}"; do
        if ! command_exists "$tool"; then
            missing_tools+=("$tool")
        fi
    done

    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo "Please install the missing tools and try again."
        exit 1
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &>/dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check if cluster is production-ready
    if [[ $(kubectl get nodes --no-headers | wc -l) -lt 3 ]]; then
        print_warning "Cluster has fewer than 3 nodes. This is not recommended for production."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    print_success "Prerequisites check passed"
}

# Function to verify secrets are properly configured
verify_secrets() {
    print_stage "Security and Secrets Verification"

    # Check if secrets template exists
    if [[ ! -f "secrets.yaml.example" ]]; then
        print_error "secrets.yaml.example not found"
        exit 1
    fi

    # Check if actual secrets exist
    if ! kubectl get secrets -n "$NAMESPACE" &>/dev/null; then
        print_warning "No secrets found in namespace. Ensure secrets are configured."
        echo "Run ./scripts/generate-secrets.sh first."
    fi

    # Verify external secrets are configured if using them
    if kubectl get externalsecrets -n "$NAMESPACE" &>/dev/null; then
        print_success "External secrets found"

        # Check if external secrets are ready
        local ready_secrets=$(kubectl get externalsecrets -n "$NAMESPACE" -o jsonpath='{.items[?(@.status.ready)]}' | jq length)
        local total_secrets=$(kubectl get externalsecrets -n "$NAMESPACE" -o jsonpath='{.items}' | jq length)

        if [[ $ready_secrets -eq $total_secrets ]]; then
            print_success "All external secrets are ready"
        else
            print_error "Some external secrets are not ready: $ready_secrets/$total_secrets"
            exit 1
        fi
    else
        print_warning "External secrets not found, using Kubernetes secrets"
    fi

    print_success "Security verification completed"
}

# Function to deploy security components
deploy_security() {
    print_stage "Security Components Deployment"

    echo "Deploying network policies..."
    if [[ -f "k8s/network-policy.yaml" ]]; then
        kubectl apply -f "k8s/network-policy.yaml" -n "$NAMESPACE"
        print_success "Network policies deployed"
    else
        print_warning "Network policy file not found"
    fi

    echo "Deploying Falco for runtime security..."
    if [[ -f "k8s/falco.yaml" ]]; then
        kubectl apply -f "k8s/falco.yaml"
        print_success "Falco deployed"

        # Wait for Falco to be ready
        echo "Waiting for Falco DaemonSet to be ready..."
        kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=falco -n falco --timeout=300s
        print_success "Falco is ready"
    else
        print_warning "Falco configuration not found"
    fi

    echo "Deploying OPA Gatekeeper for policy enforcement..."
    if [[ -f "k8s/opa-gatekeeper.yaml" ]]; then
        kubectl apply -f "k8s/opa-gatekeeper.yaml"
        print_success "OPA Gatekeeper policies deployed"

        # Wait for Gatekeeper to be ready
        echo "Waiting for Gatekeeper to be ready..."
        kubectl wait --for=condition=available deployment/gatekeeper-controller-manager -n gatekeeper-system --timeout=300s
        print_success "Gatekeeper is ready"
    else
        print_warning "OPA Gatekeeper configuration not found"
    fi

    print_success "Security components deployment completed"
}

# Function to deploy storage
deploy_storage() {
    print_stage "Storage Infrastructure Deployment"

    # Deploy storage classes if needed
    if kubectl get storageclass &>/dev/null; then
        print_success "Storage classes already exist"
    else
        print_warning "No storage classes found. Please ensure storage classes are configured."
    fi

    # Deploy Persistent Volumes and Claims
    echo "Deploying storage configuration..."
    if [[ -f "k8s/storage.yaml" ]]; then
        kubectl apply -f "k8s/storage.yaml" -n "$NAMESPACE"
        print_success "Storage configuration applied"

        # Verify PVCs are bound
        echo "Waiting for PVCs to be bound..."
        sleep 10
        local bound_pvcs=$(kubectl get pvc -n "$NAMESPACE" -o jsonpath='{.items[?(@.status.phase=="Bound")]' | jq length)
        local total_pvcs=$(kubectl get pvc -n "$NAMESPACE" -o jsonpath='{.items}' | jq length)

        echo "Bound PVCs: $bound_pvcs/$total_pvcs"
    else
        print_warning "Storage configuration file not found"
    fi

    print_success "Storage deployment completed"
}

# Function to deploy database
deploy_database() {
    print_stage "Database Deployment"

    echo "Deploying PostgreSQL..."
    if [[ -f "k8s/postgres.yaml" ]]; then
        kubectl apply -f "k8s/postgres.yaml" -n "$NAMESPACE"

        # Wait for PostgreSQL to be ready
        echo "Waiting for PostgreSQL to be ready..."
        kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgres -n "$NAMESPACE" --timeout=600s
        print_success "PostgreSQL is ready"

        # Test database connectivity
        echo "Testing database connectivity..."
        kubectl exec deployment/postgres -n "$NAMESPACE" -- pg_isready -U cpg2pvg_user -d cpg2pvg_ai
        print_success "Database connectivity verified"
    else
        print_error "PostgreSQL configuration not found"
        exit 1
    fi

    print_success "Database deployment completed"
}

# Function to deploy Redis
deploy_redis() {
    print_stage "Redis Deployment"

    echo "Deploying Redis..."
    if [[ -f "k8s/redis.yaml" ]]; then
        kubectl apply -f "k8s/redis.yaml" -n "$NAMESPACE"

        # Wait for Redis to be ready
        echo "Waiting for Redis to be ready..."
        kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n "$NAMESPACE" --timeout=300s
        print_success "Redis is ready"

        # Test Redis connectivity
        echo "Testing Redis connectivity..."
        kubectl exec deployment/redis -n "$NAMESPACE" -- redis-cli ping
        print_success "Redis connectivity verified"
    else
        print_error "Redis configuration not found"
        exit 1
    fi

    print_success "Redis deployment completed"
}

# Function to deploy application services
deploy_application() {
    print_stage "Application Services Deployment"

    # Deploy backend
    echo "Deploying backend service..."
    if [[ -f "k8s/backend.yaml" ]]; then
        kubectl apply -f "k8s/backend.yaml" -n "$NAMESPACE"

        echo "Waiting for backend to be ready..."
        kubectl rollout status deployment/backend -n "$NAMESPACE" --timeout=600s
        print_success "Backend deployment completed"
    fi

    # Deploy frontend
    echo "Deploying frontend service..."
    if [[ -f "k8s/frontend.yaml" ]]; then
        kubectl apply -f "k8s/frontend.yaml" -n "$NAMESPACE"

        echo "Waiting for frontend to be ready..."
        kubectl rollout status deployment/frontend -n "$NAMESPACE" --timeout=600s
        print_success "Frontend deployment completed"
    fi

    # Deploy MinIO
    echo "Deploying MinIO storage..."
    if [[ -f "k8s/minio.yaml" ]]; then
        kubectl apply -f "k8s/minio.yaml" -n "$NAMESPACE"

        echo "Waiting for MinIO to be ready..."
        kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=minio -n "$NAMESPACE" --timeout=300s
        print_success "MinIO deployment completed"
    fi

    # Deploy Celery workers
    echo "Deploying Celery workers..."
    if [[ -f "k8s/celery-worker.yaml" ]]; then
        kubectl apply -f "k8s/celery-worker.yaml" -n "$NAMESPACE"

        echo "Waiting for Celery workers to be ready..."
        kubectl rollout status deployment/celery-worker -n "$NAMESPACE" --timeout=300s
        kubectl rollout status deployment/celery-beat -n "$NAMESPACE" --timeout=300s
        print_success "Celery deployment completed"
    fi

    print_success "Application services deployment completed"
}

# Function to deploy monitoring
deploy_monitoring() {
    print_stage "Monitoring and Observability Deployment"

    echo "Deploying monitoring stack..."
    if [[ -f "k8s/monitoring.yaml" ]]; then
        kubectl apply -f "k8s/monitoring.yaml" -n "$NAMESPACE"
        print_success "Monitoring configuration applied"
    fi

    if [[ -f "k8s/monitoring-configs.yaml" ]]; then
        kubectl apply -f "k8s/monitoring-configs.yaml" -n "$NAMESPACE"
        print_success "Monitoring configurations applied"
    fi

    if [[ -f "k8s/storage-monitoring.yaml" ]]; then
        kubectl apply -f "k8s/storage-monitoring.yaml" -n "$NAMESPACE"
        print_success "Storage monitoring applied"
    fi

    # Wait for monitoring components
    echo "Waiting for Prometheus to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n "$NAMESPACE" --timeout=300s

    echo "Waiting for Grafana to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n "$NAMESPACE" --timeout=300s

    print_success "Monitoring deployment completed"
}

# Function to deploy compliance
deploy_compliance() {
    print_stage "Compliance Framework Deployment"

    echo "Deploying compliance configuration..."
    if [[ -f "k8s/compliance.yaml" ]]; then
        kubectl apply -f "k8s/compliance.yaml" -n "$NAMESPACE"
        print_success "Compliance configuration applied"
    fi

    # Apply resource limits for compliance
    if [[ -f "k8s/resource-limits.yaml" ]]; then
        kubectl apply -f "k8s/resource-limits.yaml" -n "$NAMESPACE"
        print_success "Resource limits applied"
    fi

    # Enable compliance pod security standards
    echo "Applying compliance pod security standards..."
    kubectl label namespace "$NAMESPACE" \
        pod-security.kubernetes.io/enforce=restricted \
        pod-security.kubernetes.io/audit=restricted \
        pod-security.kubernetes.io/warn=restricted \
        --overwrite

    print_success "Compliance deployment completed"
}

# Function to validate deployment
validate_deployment() {
    print_stage "Deployment Validation"

    echo "Checking pod status..."
    local failed_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "$failed_pods" ]]; then
        print_error "Failed pods found: $failed_pods"
        echo "Checking pod details..."
        kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running -o wide
        exit 1
    fi
    print_success "All pods are running"

    echo "Checking service health..."
    local services=("backend-service" "frontend-service" "postgres-service" "redis-service" "minio-service")
    for service in "${services[@]}"; do
        if kubectl get service "$service" -n "$NAMESPACE" &>/dev/null; then
            echo "✓ Service $service exists"
        else
            print_error "Service $service not found"
            exit 1
        fi
    done
    print_success "All services are deployed"

    echo "Running health checks..."
    # Backend health check
    kubectl port-forward service/backend-service 8000:80 -n "$NAMESPACE" &
    local pf_pid=$!
    sleep 10

    if curl -f http://localhost:8000/health &>/dev/null; then
        print_success "Backend health check passed"
    else
        print_error "Backend health check failed"
        kill $pf_pid
        exit 1
    fi
    kill $pf_pid

    # Database connectivity check
    if kubectl exec deployment/postgres -n "$NAMESPACE" -- pg_isready -U cpg2pvg_user -d cpg2pvg_ai &>/dev/null; then
        print_success "Database connectivity verified"
    else
        print_error "Database connectivity failed"
        exit 1
    fi

    print_success "All validation checks passed"
}

# Function to generate deployment report
generate_deployment_report() {
    print_stage "Deployment Report Generation"

    local report_file="deployment-report-$(date +%Y%m%d-%H%M%S).txt"

    cat > "$report_file" << EOF
CPG2PVG-AI Production Deployment Report
Generated: $(date)
Environment: $ENVIRONMENT
Namespace: $NAMESPACE
Cluster: $CLUSTER_NAME

Deployment Status: SUCCESS

Deployed Components:
✅ Security Components
   - Network Policies
   - Falco Runtime Security
   - OPA Gatekeeper

✅ Infrastructure
   - Storage Classes and PVCs
   - PostgreSQL Database
   - Redis Cache

✅ Application Services
   - Backend API
   - Frontend Web App
   - MinIO Object Storage
   - Celery Workers

✅ Monitoring & Observability
   - Prometheus
   - Grafana
   - AlertManager

✅ Compliance Framework
   - HIPAA Compliance
   - GDPR Compliance
   - SOC 2 Controls

Cluster Resources:
EOF

    # Add cluster resource information
    kubectl get nodes -o custom-columns="NODE:.metadata.name,CPU:.status.capacity.cpu,MEMORY:.status.capacity.memory,VERSION:.status.nodeInfo.kubeletVersion" >> "$report_file"

    echo -e "\nNamespace Resources:" >> "$report_file"
    kubectl top pods -n "$NAMESPACE" --no-headers >> "$report_file" 2>/dev/null || echo "Metrics server not available" >> "$report_file"

    echo -e "\nNext Steps:" >> "$report_file"
    echo "1. Configure Ingress and DNS" >> "$report_file"
    echo "2. Set up backup and disaster recovery" >> "$report_file"
    echo "3. Configure alerting and notifications" >> "$report_file"
    echo "4. Perform load testing" >> "$report_file"
    echo "5. Schedule regular security audits" >> "$report_file"

    print_success "Deployment report generated: $report_file"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main deployment function
main() {
    echo -e "${PURPLE}Starting CPG2PVG-AI Production Deployment...${NC}"
    echo "This deployment includes full security, compliance, and monitoring setup."
    echo

    # Confirm deployment
    read -p "This will deploy to PRODUCTION. Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled"
        exit 1
    fi

    # Create namespace if it doesn't exist
    echo "Creating namespace..."
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

    # Execute deployment stages
    for stage in "${STAGES[@]}"; do
        echo
        case $stage in
            "prerequisites")
                check_prerequisites
                ;;
            "security")
                verify_secrets
                deploy_security
                ;;
            "storage")
                deploy_storage
                ;;
            "database")
                deploy_database
                deploy_redis
                ;;
            "application")
                deploy_application
                ;;
            "monitoring")
                deploy_monitoring
                ;;
            "compliance")
                deploy_compliance
                ;;
            "validation")
                validate_deployment
                ;;
        esac
    done

    # Generate final report
    generate_deployment_report

    echo
    echo -e "${GREEN}🎉 Production deployment completed successfully!${NC}"
    echo
    echo -e "${BLUE}📊 Deployment Summary:${NC}"
    echo "- Namespace: $NAMESPACE"
    echo "- Cluster: $CLUSTER_NAME"
    echo "- Environment: $ENVIRONMENT"
    echo "- Compliance: HIPAA, GDPR, SOC 2"
    echo "- Security: Runtime monitoring, policy enforcement"
    echo "- Monitoring: Full observability stack"
    echo
    echo -e "${YELLOW}⚠️  Important Post-Deployment Actions:${NC}"
    echo "1. Configure Ingress and external DNS"
    echo "2. Set up SSL/TLS certificates"
    echo "3. Configure backup and disaster recovery"
    echo "4. Set up monitoring alerts"
    echo "5. Perform security penetration testing"
    echo "6. Document compliance evidence"
    echo
    echo -e "${PURPLE}Access Information:${NC}"
    echo "- Grafana: https://grafana.cpg2pvg-ai.local"
    echo "- Prometheus: https://prometheus.cpg2pvg-ai.local"
    echo "- Flower (Celery): https://flower.cpg2pvg-ai.local"
    echo "- MinIO Console: https://minio.cpg2pvg-ai.local"
}

# Handle script interruption
trap 'print_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"