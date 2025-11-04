# CPG2PVG-AI 完整部署指南

## 🎯 概述

CPG2PVG-AI 是一个企业级医疗AI系统，采用微服务架构，具备完整的安全性、合规性和可观测性。本指南提供从开发到生产的完整部署流程。

## 🏗️ 架构概览

### 核心组件
- **后端服务**: FastAPI + Python 3.11
- **前端应用**: Next.js 14 + React 18 + TypeScript
- **数据库**: PostgreSQL 15 (主数据库)
- **缓存**: Redis 7 (缓存和消息队列)
- **对象存储**: MinIO (文件存储)
- **任务队列**: Celery + Celery Beat
- **监控系统**: Prometheus + Grafana
- **日志系统**: ELK Stack + Fluent Bit
- **安全监控**: Falco + OPA Gatekeeper

### 安全和合规
- **外部密钥管理**: HashiCorp Vault / AWS Secrets Manager
- **运行时安全**: Falco 实时威胁检测
- **策略即代码**: OPA Gatekeeper 准入控制
- **合规框架**: HIPAA、GDPR、SOC 2
- **网络安全**: 零信任网络架构

## 📋 部署前检查清单

### 环境要求
- [ ] Kubernetes 集群 1.25+ (至少3个节点用于生产)
- [ ] kubectl 配置完成
- [ ] Helm 3.0+ (可选)
- [ ] Docker 20.10+
- [ ] OpenSSL 用于密钥生成
- [ ] 域名和SSL证书

### 安全准备
- [ ] 运行 `./scripts/generate-secrets.sh` 生成安全密钥
- [ ] 配置外部密钥管理 (Vault/AWS)
- [ ] 设置网络访问控制
- [ ] 配置监控和告警
- [ ] 准备备份策略

## 🚀 部署流程

### 1. 本地开发环境

```bash
# 克隆项目
git clone <repository-url>
cd cpg2pvg-ai

# 生成开发密钥
cp secrets.yaml.example .env
./scripts/generate-secrets.sh

# 启动开发环境
docker-compose up -d

# 验证服务状态
curl http://localhost:8000/health
curl http://localhost:3000
```

### 2. 生产环境部署

#### 方法一：自动部署脚本
```bash
# 运行完整生产部署
./scripts/deploy-production.sh
```

#### 方法二：分步部署
```bash
# 1. 部署基础架构
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# 2. 部署安全组件
kubectl apply -f k8s/network-policy.yaml
kubectl apply -f k8s/falco.yaml
kubectl apply -f k8s/opa-gatekeeper.yaml

# 3. 部署存储和数据库
kubectl apply -f k8s/storage.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml

# 4. 部署应用服务
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/celery-worker.yaml
kubectl apply -f k8s/minio.yaml

# 5. 部署监控
kubectl apply -f k8s/monitoring.yaml
kubectl apply -f k8s/monitoring-configs.yaml

# 6. 部署合规配置
kubectl apply -f k8s/compliance.yaml

# 7. 配置Ingress
kubectl apply -f k8s/ingress.yaml
```

### 3. 使用 Kustomize 部署

```bash
# 使用 Kustomize 管理环境配置
kubectl apply -k k8s/

# 针对不同环境
kubectl apply -k k8s/overlays/staging/
kubectl apply -k k8s/overlays/production/
```

## 🔧 外部服务配置

### HashiCorp Vault 集成
```bash
# 安装 External Secrets Operator
kubectl apply -f k8s/external-secrets.yaml

# 配置 Vault 后端
# 参考 k8s/external-secrets.yaml 中的配置
```

### SSL/TLS 配置
```bash
# 使用 cert-manager 管理证书
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# 配置 Let's Encrypt
cat > cluster-issuer.yaml << EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@cpg2pvg-ai.local
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
kubectl apply -f cluster-issuer.yaml
```

## 📊 监控和可观测性

### 访问监控界面
- **Grafana**: https://grafana.cpg2pvg-ai.local
- **Prometheus**: https://prometheus.cpg2pvg-ai.local
- **Flower (Celery)**: https://flower.cpg2pvg-ai.local
- **MinIO Console**: https://minio.cpg2pvg-ai.local

### 关键监控指标
- 应用性能指标 (APM)
- 系统资源使用率
- 安全事件和违规
- 合规状态检查
- 业务指标和KPI

## 🔒 安全最佳实践

### 密钥管理
- 使用外部密钥管理服务 (Vault/AWS)
- 定期轮换密钥 (每90天)
- 实施最小权限原则
- 启用审计日志

### 网络安全
- 实施零信任网络架构
- 使用网络策略限制流量
- 启用TLS 1.3加密
- 配置防火墙规则

### 运行时安全
- Falco 实时威胁检测
- OPA Gatekeeper 准入控制
- 容器镜像安全扫描
- 定期安全评估

## 📋 合规性管理

### HIPAA 合规
- [ ] 启用审计日志 (7年保留期)
- [ ] 实施数据加密 (AES-256)
- [ ] 配置访问控制和MFA
- [ ] 建立事件响应程序

### GDPR 合规
- [ ] 实施同意管理
- [ ] 支持数据主体权利
- [ ] 数据最小化原则
- [ ] 隐私设计架构

### SOC 2 合规
- [ ] 建立安全控制措施
- [ ] 实施监控和告警
- [ ] 定期渗透测试
- [ ] 文档化安全流程

## 🔧 故障排除

### 常见问题

#### Pod 启动失败
```bash
# 检查Pod状态
kubectl get pods -n cpg2pvg-ai
kubectl describe pod <pod-name> -n cpg2pvg-ai
kubectl logs <pod-name> -n cpg2pvg-ai

# 检查资源限制
kubectl top nodes
kubectl top pods -n cpg2pvg-ai
```

#### 服务连接问题
```bash
# 检查服务状态
kubectl get svc -n cpg2pvg-ai
kubectl describe svc <service-name> -n cpg2pvg-ai

# 端口转发测试
kubectl port-forward service/<service-name> 8080:80 -n cpg2pvg-ai
```

#### 存储问题
```bash
# 检查PVC状态
kubectl get pvc -n cpg2pvg-ai
kubectl describe pvc <pvc-name> -n cpg2pvg-ai

# 检查存储类
kubectl get storageclass
```

### 安全问题排查
```bash
# 检查安全违规
kubectl get constraints.gatekeeper.sh -n cpg2pvg-ai
kubectl describe constraint <constraint-name> -n cpg2pvg-ai

# 检查Falco事件
kubectl logs -n falco -l app.kubernetes.io/name=falco
```

## 📈 性能优化

### 应用层优化
- 数据库连接池调优
- Redis缓存策略
- 异步任务优化
- 前端代码分割

### 基础设施优化
- HPA自动扩缩容
- 节点亲和性配置
- 资源限制调优
- 网络策略优化

### 监控优化
- Prometheus数据保留策略
- Grafana仪表板优化
- 告警规则调优
- 日志聚合优化

## 🔄 升级和维护

### 应用升级
```bash
# 更新镜像版本
kubectl set image deployment/backend backend=cpg2pvg-ai/backend:v1.1.0 -n cpg2pvg-ai

# 滚动更新
kubectl rollout status deployment/backend -n cpg2pvg-ai

# 回滚
kubectl rollout undo deployment/backend -n cpg2pvg-ai
```

### 数据库维护
```bash
# 备份数据库
kubectl create job --from=cronjob/postgres-backup postgres-backup-$(date +%Y%m%d) -n cpg2pvg-ai

# 查看备份
kubectl get jobs -n cpg2pvg-ai | grep postgres-backup
```

### 证书更新
```bash
# 更新证书
kubectl annotate cert <cert-name> cert-manager.io/renew-before="2024-01-01T00:00:00Z" -n cpg2pvg-ai
```

## 📞 支持和联系

### 技术支持
- **GitHub Issues**: 报告Bug和功能请求
- **文档**: [在线文档](https://docs.cpg2pvg-ai.com)
- **社区**: [Slack频道](https://cpg2pvg-ai.slack.com)

### 安全支持
- **安全团队**: security@cpg2pvg-ai.com
- **漏洞报告**: security@cpg2pvg-ai.com
- **紧急响应**: +1-xxx-xxx-xxxx

## 📚 参考资源

### 官方文档
- [Kubernetes文档](https://kubernetes.io/docs/)
- [Docker文档](https://docs.docker.com/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Next.js文档](https://nextjs.org/docs)

### 安全指南
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST网络安全框架](https://www.nist.gov/cyberframework)
- [HIPAA安全规则](https://www.hhs.gov/hipaa/for-professionals/security/)

### 最佳实践
- [Kubernetes安全最佳实践](https://kubernetes.io/docs/concepts/security/)
- [容器安全最佳实践](https://snyk.io/blog/10-docker-image-security-best-practices/)
- [云原生安全](https://github.com/cncf/tag-security)

---

## 📄 版本历史

- **v2.0.0** (2024-01): 完整的安全和合规框架
- **v1.5.0** (2023-12): 添加运行时安全和策略即代码
- **v1.2.0** (2023-11): 集成外部密钥管理
- **v1.0.0** (2023-10): 初始生产就绪版本

---

**注意**: 本指南会随着系统更新而持续改进。请定期查看最新版本。

**免责声明**: 本系统处理医疗数据，请确保遵守当地法律法规和行业标准。