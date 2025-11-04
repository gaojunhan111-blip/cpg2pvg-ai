-- CPG2PVG-AI 云部署数据库初始化脚本
-- 适用于 Supabase/PostgreSQL

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 指南表
CREATE TABLE IF NOT EXISTS guidelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    original_content TEXT,
    file_name VARCHAR(255),
    file_url VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    processing_progress INTEGER DEFAULT 0 CHECK (processing_progress >= 0 AND processing_progress <= 100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PVG结果表
CREATE TABLE IF NOT EXISTS pvg_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    guideline_id UUID REFERENCES guidelines(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    key_recommendations JSONB DEFAULT '[]',
    safety_warnings JSONB DEFAULT '[]',
    target_audience VARCHAR(100),
    readability_score DECIMAL(3,2),
    quality_score DECIMAL(3,2),
    processing_time_seconds INTEGER,
    llm_model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_estimate DECIMAL(10,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 任务处理表
CREATE TABLE IF NOT EXISTS processing_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    guideline_id UUID REFERENCES guidelines(id) ON DELETE CASCADE,
    task_type VARCHAR(100) NOT NULL CHECK (task_type IN ('document_parsing', 'content_processing', 'quality_check', 'final_generation')),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 使用统计表
CREATE TABLE IF NOT EXISTS usage_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    guideline_id UUID REFERENCES guidelines(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_guidelines_user_id ON guidelines(user_id);
CREATE INDEX IF NOT EXISTS idx_guidelines_status ON guidelines(status);
CREATE INDEX IF NOT EXISTS idx_guidelines_created_at ON guidelines(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pvg_results_guideline_id ON pvg_results(guideline_id);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_guideline_id ON processing_tasks(guideline_id);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_status ON processing_tasks(status);
CREATE INDEX IF NOT EXISTS idx_usage_stats_user_id ON usage_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_stats_created_at ON usage_stats(created_at DESC);

-- 创建更新时间的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建更新时间触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_guidelines_updated_at BEFORE UPDATE ON guidelines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pvg_results_updated_at BEFORE UPDATE ON pvg_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入默认系统配置
INSERT INTO system_config (key, value, description) VALUES
('max_file_size', '52428800', '最大文件上传大小（字节）'),
('supported_formats', '["pdf", "docx", "txt"]', '支持的文件格式'),
('default_llm_model', '"gpt-4"', '默认使用的LLM模型'),
('processing_timeout', '3600', '处理超时时间（秒）'),
('max_concurrent_tasks', '5', '最大并发任务数')
ON CONFLICT (key) DO NOTHING;

-- Row Level Security (RLS) 配置
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE guidelines ENABLE ROW LEVEL SECURITY;
ALTER TABLE pvg_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_stats ENABLE ROW LEVEL SECURITY;

-- 用户只能访问自己的数据
CREATE POLICY "Users can view own data" ON users
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "Users can view own guidelines" ON guidelines
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own pvg_results" ON pvg_results
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM guidelines
            WHERE guidelines.id = pvg_results.guideline_id
            AND guidelines.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view own usage_stats" ON usage_stats
    FOR ALL USING (auth.uid() = user_id);

-- 创建API服务用户（用于后端服务访问）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'api_service') THEN
        CREATE ROLE api_service LOGIN PASSWORD 'secure_api_password';
    END IF;
END
$$;

-- 授予API服务用户必要的权限
GRANT CONNECT ON DATABASE postgres TO api_service;
GRANT USAGE ON SCHEMA public TO api_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO api_service;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api_service;

-- 为API服务用户创建RLS策略例外
ALTER TABLE users DISABLE ROW LEVEL SECURITY TO api_service;
ALTER TABLE guidelines DISABLE ROW LEVEL SECURITY TO api_service;
ALTER TABLE pvg_results DISABLE ROW LEVEL SECURITY TO api_service;
ALTER TABLE processing_tasks DISABLE ROW LEVEL SECURITY TO api_service;
ALTER TABLE system_config DISABLE ROW LEVEL SECURITY TO api_service;

-- 创建健康检查函数
CREATE OR REPLACE FUNCTION health_check()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'status', 'healthy',
        'timestamp', NOW(),
        'database', 'connected',
        'version', version()
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMIT;