-- CPG2PVG-AI 数据库初始化脚本
-- PostgreSQL Database Initialization

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建索引优化搜索
-- 这些索引将在应用启动时通过SQLAlchemy自动创建
-- 这里只是作为参考

-- 用户表
-- CREATE TABLE IF NOT EXISTS users (
--     id SERIAL PRIMARY KEY,
--     username VARCHAR(50) UNIQUE NOT NULL,
--     email VARCHAR(100) UNIQUE NOT NULL,
--     hashed_password VARCHAR(255) NOT NULL,
--     full_name VARCHAR(100),
--     is_active BOOLEAN DEFAULT TRUE,
--     is_verified BOOLEAN DEFAULT FALSE,
--     is_superuser BOOLEAN DEFAULT FALSE,
--     is_premium BOOLEAN DEFAULT FALSE,
--     api_quota INTEGER DEFAULT 100,
--     api_usage INTEGER DEFAULT 0,
--     last_login_at TIMESTAMP,
--     reset_token VARCHAR(100) UNIQUE,
--     reset_token_expires_at TIMESTAMP,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 指南表
-- CREATE TABLE IF NOT EXISTS guidelines (
--     id SERIAL PRIMARY KEY,
--     title VARCHAR(500) NOT NULL,
--     description TEXT,
--     original_filename VARCHAR(255) NOT NULL,
--     file_path VARCHAR(500) NOT NULL,
--     file_size INTEGER NOT NULL,
--     file_type VARCHAR(50) NOT NULL,
--     file_hash VARCHAR(64) UNIQUE NOT NULL,
--     status VARCHAR(20) DEFAULT 'uploaded',
--     processed_content TEXT,
--     processing_metadata JSONB,
--     quality_score INTEGER,
--     accuracy_score INTEGER,
--     uploaded_by VARCHAR(100) NOT NULL,
--     processing_mode VARCHAR(20) DEFAULT 'slow',
--     is_public BOOLEAN DEFAULT FALSE,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 任务表
-- CREATE TABLE IF NOT EXISTS tasks (
--     id SERIAL PRIMARY KEY,
--     task_id VARCHAR(100) UNIQUE NOT NULL,
--     task_type VARCHAR(50) NOT NULL,
--     status VARCHAR(20) DEFAULT 'pending',
--     guideline_id INTEGER REFERENCES guidelines(id) ON DELETE CASCADE,
--     input_data JSONB,
--     result_data JSONB,
--     error_message TEXT,
--     started_at VARCHAR(50),
--     completed_at VARCHAR(50),
--     execution_time REAL,
--     total_tokens_used INTEGER DEFAULT 0,
--     total_cost REAL DEFAULT 0.0,
--     quality_score REAL,
--     accuracy_score REAL,
--     retry_count INTEGER DEFAULT 0,
--     max_retries INTEGER DEFAULT 3,
--     priority INTEGER DEFAULT 0,
--     notify_on_completion BOOLEAN DEFAULT TRUE,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 任务进度表
-- CREATE TABLE IF NOT EXISTS task_progress (
--     id SERIAL PRIMARY KEY,
--     task_id VARCHAR(100) NOT NULL,
--     step_name VARCHAR(100) NOT NULL,
--     status VARCHAR(20) NOT NULL,
--     progress_percentage INTEGER DEFAULT 0,
--     message TEXT,
--     metadata JSONB,
--     execution_time REAL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 创建搜索索引
-- CREATE INDEX IF NOT EXISTS idx_guidelines_title_gin ON guidelines USING gin(title gin_trgm_ops);
-- CREATE INDEX IF NOT EXISTS idx_guidelines_description_gin ON guidelines USING gin(description gin_trgm_ops);
-- CREATE INDEX IF NOT EXISTS idx_guidelines_status ON guidelines(status);
-- CREATE INDEX IF NOT EXISTS idx_guidelines_uploaded_by ON guidelines(uploaded_by);
-- CREATE INDEX IF NOT EXISTS idx_guidelines_created_at ON guidelines(created_at);

-- CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id);
-- CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
-- CREATE INDEX IF NOT EXISTS idx_tasks_guideline_id ON tasks(guideline_id);
-- CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

-- CREATE INDEX IF NOT EXISTS idx_task_progress_task_id ON task_progress(task_id);
-- CREATE INDEX IF NOT EXISTS idx_task_progress_step_name ON task_progress(step_name);

-- 创建默认管理员用户（密码：admin123，生产环境中请修改）
-- INSERT INTO users (username, email, hashed_password, full_name, is_active, is_verified, is_superuser, is_premium)
-- VALUES ('admin', 'admin@cpg2pvg.ai', '$2b$12$X5WFBTrL9Z9X8kQKxZhcFeM8rK8vA6Lz9L0OvP2N3M4qQ7R8S9T0U1V2W3X4Y5Z6', '系统管理员', TRUE, TRUE, TRUE, TRUE)
-- ON CONFLICT (username) DO NOTHING;

-- 插入示例数据（可选）
-- 这里可以添加一些测试数据

-- 创建触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为表创建触发器（这些将在SQLAlchemy模型创建后应用）
-- CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- CREATE TRIGGER update_guidelines_updated_at BEFORE UPDATE ON guidelines FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- CREATE TRIGGER update_task_progress_updated_at BEFORE UPDATE ON task_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON DATABASE cpg2pvg IS 'CPG2PVG-AI 临床指南转化系统数据库';

-- 设置数据库配置
ALTER DATABASE cpg2pvg SET timezone TO 'Asia/Shanghai';
ALTER DATABASE cpg2pvg SET statement_timeout = '300s';
ALTER DATABASE cpg2pvg SET lock_timeout = '60s';

-- 创建性能监控视图
CREATE OR REPLACE VIEW task_performance_stats AS
SELECT
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
    AVG(execution_time) FILTER (WHERE execution_time IS NOT NULL) as avg_execution_time,
    AVG(quality_score) FILTER (WHERE quality_score IS NOT NULL) as avg_quality_score,
    SUM(total_cost) as total_cost
FROM tasks
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- 创建用户使用统计视图
CREATE OR REPLACE VIEW user_usage_stats AS
SELECT
    u.id,
    u.username,
    u.email,
    u.api_quota,
    u.api_usage,
    COUNT(g.id) as total_guidelines,
    COUNT(g.id) FILTER (WHERE g.status = 'completed') as completed_guidelines,
    SUM(t.total_cost) as total_cost,
    u.created_at as user_created_at
FROM users u
LEFT JOIN guidelines g ON u.username = g.uploaded_by
LEFT JOIN tasks t ON g.id = t.guideline_id
GROUP BY u.id, u.username, u.email, u.api_quota, u.api_usage, u.created_at;