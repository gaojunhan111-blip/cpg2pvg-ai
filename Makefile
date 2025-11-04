# CPG2PVG-AI Makefile
# 项目管理命令

.PHONY: help install dev build test clean lint format docker-up docker-down logs

# 默认目标
help:
	@echo "CPG2PVG-AI 开发命令:"
	@echo ""
	@echo "  install     - 安装所有依赖"
	@echo "  dev         - 启动开发环境"
	@echo "  build       - 构建项目"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理临时文件"
	@echo "  docker-up   - 启动Docker服务"
	@echo "  docker-down - 停止Docker服务"
	@echo "  logs        - 查看服务日志"
	@echo ""

# 安装依赖
install:
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install
	@echo "下载spaCy模型..."
	python -m spacy download en_core_sci_sm

# 开发环境
dev:
	@echo "启动开发环境..."
	docker-compose up -d postgres redis minio
	@echo "等待数据库启动..."
	sleep 5
	@echo "启动后端开发服务器..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "启动前端开发服务器..."
	cd frontend && npm run dev &
	@echo "启动Celery Worker..."
	cd backend && celery -A celery_worker.celery_app worker --loglevel=info &
	@echo "启动Celery Beat..."
	cd backend && celery -A celery_worker.celery_app beat --loglevel=info &
	@echo "开发环境已启动!"

# 构建项目
build:
	@echo "构建前端..."
	cd frontend && npm run build
	@echo "构建Docker镜像..."
	docker-compose build

# 运行测试
test:
	@echo "运行后端测试..."
	cd backend && pytest
	@echo "运行前端测试..."
	cd frontend && npm run test

# 代码检查
lint:
	@echo "检查Python代码..."
	cd backend && flake8 app/ celery_worker/
	cd backend && mypy app/
	@echo "检查TypeScript代码..."
	cd frontend && npm run lint
	cd frontend && npm run type-check

# 代码格式化
format:
	@echo "格式化Python代码..."
	cd backend && black app/ celery_worker/
	cd backend && isort app/ celery_worker/
	@echo "格式化TypeScript代码..."
	cd frontend && npm run format

# 清理临时文件
clean:
	@echo "清理Python缓存..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "清理前端构建文件..."
	rm -rf frontend/.next
	rm -rf frontend/out
	rm -rf frontend/node_modules/.cache
	@echo "清理Docker资源..."
	docker-compose down -v
	docker system prune -f

# Docker服务管理
docker-up:
	@echo "启动Docker服务..."
	docker-compose up -d

docker-down:
	@echo "停止Docker服务..."
	docker-compose down

docker-rebuild:
	@echo "重新构建并启动Docker服务..."
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# 查看服务日志
logs:
	docker-compose logs -f

# 数据库管理
db-init:
	@echo "初始化数据库..."
	docker-compose exec backend alembic upgrade head

db-migrate:
	@echo "创建数据库迁移..."
	docker-compose exec backend alembic revision --autogenerate -m "$(msg)"

db-reset:
	@echo "重置数据库..."
	docker-compose exec postgres dropdb -U cpg2pvg_user cpg2pvg
	docker-compose exec postgres createdb -U cpg2pvg_user cpg2pvg
	make db-init

# 生产部署
deploy:
	@echo "部署到生产环境..."
	docker-compose -f docker-compose.prod.yml down
	docker-compose -f docker-compose.prod.yml build
	docker-compose -f docker-compose.prod.yml up -d

# 备份数据
backup:
	@echo "备份数据库..."
	docker-compose exec postgres pg_dump -U cpg2pvg_user cpg2pvg > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "备份MinIO数据..."
	docker cp cpg2pvg-minio:/data ./minio_backup_$(shell date +%Y%m%d_%H%M%S)

# 监控
monitor:
	@echo "打开监控面板..."
	@echo "Celery Flower: http://localhost:5555"
	@echo "MinIO Console: http://localhost:9001"
	@echo "API Docs: http://localhost:8000/docs"

# 开发工具
shell-backend:
	docker-compose exec backend python

shell-db:
	docker-compose exec postgres psql -U cpg2pvg_user cpg2pvg

shell-redis:
	docker-compose exec redis redis-cli

# 性能测试
load-test:
	@echo "运行负载测试..."
	cd tests && python load_test.py

# 安全检查
security-scan:
	@echo "运行安全扫描..."
	cd backend && safety check
	cd frontend && npm audit

# 文档生成
docs:
	@echo "生成API文档..."
	cd backend && python docs/generate_docs.py
	@echo "文档生成完成: docs/index.html"