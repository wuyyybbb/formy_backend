-- ============================================
-- Formy 用户表 (users)
-- ============================================
-- 存储用户基本信息、积分、套餐等

CREATE TABLE IF NOT EXISTS users (
    -- ========== 主键 ==========
    user_id VARCHAR(50) PRIMARY KEY,
    
    -- ========== 基本信息 ==========
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100),
    avatar TEXT,
    
    -- ========== 认证信息 ==========
    password_hash TEXT,
    -- 密码哈希值（bcrypt）
    
    has_password BOOLEAN NOT NULL DEFAULT FALSE,
    -- 是否设置了密码
    
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    -- 账户是否激活
    
    -- ========== 套餐和积分 ==========
    current_plan_id VARCHAR(50),
    -- 当前套餐ID（starter/basic/pro/ultimate/null 表示免费用户）
    
    current_credits INTEGER NOT NULL DEFAULT 0,
    -- 当前剩余算力
    
    total_credits_used INTEGER NOT NULL DEFAULT 0,
    -- 累计使用的算力
    
    plan_renew_at TIMESTAMP WITH TIME ZONE,
    -- 套餐下次续费时间（算力重置时间）
    
    signup_bonus_granted BOOLEAN NOT NULL DEFAULT FALSE,
    -- 注册奖励是否已发放（用于防止重复发放）
    
    -- ========== 时间戳 ==========
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    -- 账户创建时间
    
    last_login TIMESTAMP WITH TIME ZONE,
    -- 最后登录时间
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    -- 最后更新时间
);

-- ========== 索引 ==========
-- 邮箱索引（已由 UNIQUE 约束自动创建）
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 套餐索引（用于按套餐查询用户）
CREATE INDEX IF NOT EXISTS idx_users_plan ON users(current_plan_id);

-- 创建时间索引（用于统计）
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- ========== 注释 ==========
COMMENT ON TABLE users IS '用户信息表';
COMMENT ON COLUMN users.user_id IS '用户ID（格式: usr_xxxxxxxx）';
COMMENT ON COLUMN users.email IS '用户邮箱（唯一）';
COMMENT ON COLUMN users.username IS '用户名（显示名称）';
COMMENT ON COLUMN users.avatar IS '头像URL';
COMMENT ON COLUMN users.password_hash IS '密码哈希值（bcrypt）';
COMMENT ON COLUMN users.has_password IS '是否设置了密码';
COMMENT ON COLUMN users.is_active IS '账户是否激活';
COMMENT ON COLUMN users.current_plan_id IS '当前套餐ID';
COMMENT ON COLUMN users.current_credits IS '当前剩余算力';
COMMENT ON COLUMN users.total_credits_used IS '累计使用算力';
COMMENT ON COLUMN users.plan_renew_at IS '套餐续费时间';
COMMENT ON COLUMN users.signup_bonus_granted IS '注册奖励是否已发放';
COMMENT ON COLUMN users.created_at IS '创建时间';
COMMENT ON COLUMN users.last_login IS '最后登录时间';
COMMENT ON COLUMN users.updated_at IS '最后更新时间';

-- ========== 更新 updated_at 触发器 ==========
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
