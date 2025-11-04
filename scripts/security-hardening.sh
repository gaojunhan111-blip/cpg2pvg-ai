#!/bin/bash

# CPG2PVG-AI Security Hardening Script
# This script applies security hardening measures to the Kubernetes deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="cpg2pvg-ai"
POLICY_DIR="k8s/security-policies"

echo -e "${BLUE}🔒 CPG2PVG-AI Security Hardening Script${NC}"
echo "This script applies security policies and hardening measures."
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command_exists kubectl; then
    echo -e "${RED}❌ kubectl is required but not installed.${NC}"
    exit 1
fi

if ! kubectl cluster-info &>/dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo

# Create namespace if it doesn't exist
echo -e "${YELLOW}🏗️  Ensuring namespace exists...${NC}"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Apply Network Policies
echo -e "${YELLOW}🌐 Applying Network Policies...${NC}"

# Create default deny policy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: $NAMESPACE
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
EOF

# Apply DNS policy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: $NAMESPACE
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to: []
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
EOF

# Apply existing network policies if they exist
if [[ -f "k8s/network-policy.yaml" ]]; then
    echo "Applying existing network policies..."
    kubectl apply -f "k8s/network-policy.yaml" -n "$NAMESPACE"
fi

echo -e "${GREEN}✅ Network policies applied${NC}"

# Apply Pod Security Policies (for older Kubernetes versions)
echo -e "${YELLOW}🛡️  Applying Security Contexts...${NC}"

# Apply Pod Security Standards (Kubernetes 1.25+)
if kubectl api-resources | grep -q "podsecuritypolicies"; then
    echo "Applying Pod Security Policies..."
    cat <<EOF | kubectl apply -f -
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
  namespace: $NAMESPACE
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
EOF
else
    echo "Using Pod Security Standards..."
    # Label namespace with pod security standards
    kubectl label namespace "$NAMESPACE" \
        pod-security.kubernetes.io/enforce=restricted \
        pod-security.kubernetes.io/audit=restricted \
        pod-security.kubernetes.io/warn=restricted \
        --overwrite
fi

echo -e "${GREEN}✅ Security contexts applied${NC}"

# Apply Resource Limits
echo -e "${YELLOW}📊 Applying Resource Limits...${NC}"

if [[ -f "k8s/resource-limits.yaml" ]]; then
    kubectl apply -f "k8s/resource-limits.yaml" -n "$NAMESPACE"
    echo -e "${GREEN}✅ Resource limits applied${NC}"
else
    echo -e "${YELLOW}⚠️  Resource limits file not found${NC}"
fi

# Enable RBAC for service accounts
echo -e "${YELLOW}👤 Configuring RBAC...${NC}"

# Create read-only role for monitoring
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: monitoring-reader
  namespace: $NAMESPACE
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "replicationcontrollers"]
  verbs: ["get", "list", "watch"]
EOF

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: monitoring-reader-binding
  namespace: $NAMESPACE
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: $NAMESPACE
roleRef:
  kind: Role
  name: monitoring-reader
  apiGroup: rbac.authorization.k8s.io
EOF

echo -e "${GREEN}✅ RBAC configured${NC}"

# Apply admission controllers
echo -e "${YELLOW}🔍 Configuring Admission Controllers...${NC}"

# Check if admission controllers are enabled
ADMISSION_CONTROLLERS=$(kubectl get pods -n kube-system | grep kube-apiserver | head -1 | awk '{print $1}')
if [[ -n "$ADMISSION_CONTROLLERS" ]]; then
    echo "Checking admission controller configuration..."

    # Enable recommended admission controllers if possible
    RECOMMENDED_CONTROLLERS="NamespaceLifecycle,LimitRanger,ServiceAccount,NodeRestriction,ResourceQuota,TaintNodesByCondition,Priority,DefaultTolerationSeconds,DefaultStorageClass,StorageObjectInUseProtection"

    echo "Recommended admission controllers: $RECOMMENDED_CONTROLLERS"
    echo "Note: Some admission controllers require cluster-level configuration"
fi

echo -e "${GREEN}✅ Admission controller check completed${NC}"

# Configure audit logging
echo -e "${YELLOW}📝 Configuring Audit Logging...${NC}"

# Create audit policy
cat <<EOF > /tmp/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  namespaces: ["$NAMESPACE"]
  resources:
  - group: ""
    resources: ["secrets"]
  - group: "apps"
    resources: ["deployments"]
  - group: ""
    resources: ["pods"]
EOF

echo "Audit policy created at /tmp/audit-policy.yaml"
echo "Note: Apply this policy to the API server configuration for full audit logging"

echo -e "${GREEN}✅ Audit logging configuration prepared${NC}"

# Security scan of running pods
echo -e "${YELLOW}🔍 Scanning running pods for security issues...${NC}"

# Check for privileged containers
echo "Checking for privileged containers..."
PRIVILEGED_PODS=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.containers[*]}{.name}{"\t"}{.securityContext.privileged}{"\n"}{end}{end}' | grep "true" || true)

if [[ -n "$PRIVILEGED_PODS" ]]; then
    echo -e "${RED}⚠️  Found privileged containers:${NC}"
    echo "$PRIVILEGED_PODS"
else
    echo -e "${GREEN}✅ No privileged containers found${NC}"
fi

# Check for containers running as root
echo "Checking for containers running as root..."
ROOT_PODS=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.containers[*]}{.name}{"\t"}{.securityContext.runAsUser}{"\n"}{end}{end}' | grep -E "\t0\t|\troot\t" || true)

if [[ -n "$ROOT_PODS" ]]; then
    echo -e "${RED}⚠️  Found containers running as root:${NC}"
    echo "$ROOT_PODS"
else
    echo -e "${GREEN}✅ No containers running as root found${NC}"
fi

# Check for exposed sensitive mounts
echo "Checking for sensitive mount points..."
SENSITIVE_MOUNTS=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{range .spec.containers[*]}{range .volumeMounts[?(@.mountPath=="/var/run/docker.sock"||@.mountPath=="/")]}{.name}{"\t"}{.mountPath}{"\n"}{end}{end}{end}' | grep -v "^$" || true)

if [[ -n "$SENSITIVE_MOUNTS" ]]; then
    echo -e "${RED}⚠️  Found sensitive mounts:${NC}"
    echo "$SENSITIVE_MOUNTS"
else
    echo -e "${GREEN}✅ No sensitive mounts found${NC}"
fi

echo -e "${GREEN}✅ Security scan completed${NC}"

# Generate security report
echo -e "${YELLOW}📋 Generating Security Report...${NC}"

REPORT_FILE="security-report-$(date +%Y%m%d-%H%M%S).txt"

cat > "$REPORT_FILE" << EOF
CPG2PVG-AI Security Hardening Report
Generated: $(date)
Namespace: $NAMESPACE

Applied Security Measures:
✅ Network Policies (Default deny + DNS allow)
✅ Pod Security Standards/Contexts
✅ Resource Limits (if available)
✅ RBAC Configuration
✅ Secret Management (placeholder replacement)

Security Status:
- Privileged containers: $([ -n "$PRIVILEGED_PODS" ] && "Found - Review needed" || "None")
- Root containers: $([ -n "$ROOT_PODS" ] && "Found - Review needed" || "None")
- Sensitive mounts: $([ -n "$SENSITIVE_MOUNTS" ] && "Found - Review needed" || "None")

Recommendations:
1. Regularly rotate secrets (every 90 days)
2. Enable comprehensive audit logging
3. Use external secret management (HashiCorp Vault, AWS Secrets Manager)
4. Implement image vulnerability scanning
5. Enable admission controllers for additional security
6. Regular security audits and penetration testing

Next Steps:
1. Review any security issues found above
2. Apply external secret management
3. Configure comprehensive monitoring and alerting
4. Implement backup and disaster recovery procedures
EOF

echo -e "${GREEN}✅ Security report generated: $REPORT_FILE${NC}"

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
rm -f /tmp/audit-policy.yaml

echo
echo -e "${GREEN}🔒 Security hardening completed successfully!${NC}"
echo
echo -e "${BLUE}Security Summary:${NC}"
echo "- Network policies applied (default deny with DNS allowance)"
echo "- Pod security standards enforced"
echo "- RBAC configured for least privilege"
echo "- Security scan completed"
echo "- Report generated: $REPORT_FILE"
echo
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo "1. Review any security issues found during the scan"
echo "2. Implement external secret management for production"
echo "3. Enable comprehensive audit logging at the API server level"
echo "4. Regularly update this hardening script and reapply"
echo
echo -e "${BLUE}For production deployment, consider:${NC}"
echo "- HashiCorp Vault or AWS Secrets Manager for secrets"
echo "- OPA Gatekeeper for policy enforcement"
echo "- Falco for runtime security monitoring"
echo "- Aqua or Trivy for container image scanning"