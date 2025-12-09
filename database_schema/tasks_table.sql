-- ============================================
-- Formy 任务表 (tasks)
-- ============================================
-- 存储用户创建的编辑任务、状态、进度等

CREATE TABLE IF NOT EXISTS tasks (
    -- ========== 主键 ==========
    task_id VARCHAR(50) PRIMARY KEY,
    
    -- ========== 关联用户 ==========
    user_id UUID NOT NULL,
    -- 任务所属用户（关联 users.user_id）
    
    -- ========== 任务状态和模式 ==========
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- 任务状态: pending/processing/done/failed/cancelled
    
    mode VARCHAR(50) NOT NULL,
    -- 编辑模式: HEAD_SWAP/BACKGROUND_CHANGE/POSE_CHANGE
    
    progress INTEGER NOT NULL DEFAULT 0,
    -- 处理进度: 0-100
    
    current_step VARCHAR(100),
    -- 当前处理步骤
    
    -- ========== 图片和配置 ==========
    source_image TEXT NOT NULL,
    -- 源图片 file_id（用户上传的原始图片）
    
    reference_image TEXT,
    -- 参考图片 file_id（可选，部分模式需要）
    
    config JSONB,
    -- 配置参数（质量、大小等）
    
    -- ========== 处理结果 ==========
    result JSONB,
    -- 处理结果（输出文件 URL、face_image_url、target_image_url 等）
    
    error JSONB,
    -- 错误信息（error_code、error_message、error_details）
    
    -- ========== 积分相关 ==========
    credits_consumed INTEGER,
    -- 消耗的算力（如果为 NULL，表示还未计费）
    
    -- ========== 时间戳 ==========
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    -- 任务创建时间
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- 最后更新时间
    
    completed_at TIMESTAMP WITH TIME ZONE,
    -- 任务完成时间（成功）
    
    failed_at TIMESTAMP WITH TIME ZONE,
    -- 任务失败时间（失败）
    
    -- ========== 约束 ==========
    CONSTRAINT fk_tasks_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES users(user_id) 
        ON DELETE CASCADE
);

-- ========== 索引 ==========
-- 按用户 ID 查询（最常用）
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);

-- 按用户和状态查询（任务列表筛选）
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);

-- 按用户和创建时间排序（历史记录）
CREATE INDEX IF NOT EXISTS idx_tasks_user_created ON tasks(user_id, created_at DESC);

-- 按状态查询（后台统计用）
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- ========== 注释 ==========
COMMENT ON TABLE tasks IS '任务表';
COMMENT ON COLUMN tasks.task_id IS '任务ID';
COMMENT ON COLUMN tasks.user_id IS '任务所属用户ID（UUID 格式）';
COMMENT ON COLUMN tasks.status IS '任务状态: pending/processing/done/failed/cancelled';
COMMENT ON COLUMN tasks.mode IS '编辑模式: HEAD_SWAP/BACKGROUND_CHANGE/POSE_CHANGE';
COMMENT ON COLUMN tasks.progress IS '处理进度: 0-100';
COMMENT ON COLUMN tasks.current_step IS '当前处理步骤';
COMMENT ON COLUMN tasks.source_image IS '源图片 file_id';
COMMENT ON COLUMN tasks.reference_image IS '参考图片 file_id（可选）';
COMMENT ON COLUMN tasks.config IS '配置参数（JSON）';
COMMENT ON COLUMN tasks.result IS '处理结果（JSON）';
COMMENT ON COLUMN tasks.error IS '错误信息（JSON）';
COMMENT ON COLUMN tasks.credits_consumed IS '消耗的算力';
COMMENT ON COLUMN tasks.created_at IS '任务创建时间';
COMMENT ON COLUMN tasks.updated_at IS '最后更新时间';
COMMENT ON COLUMN tasks.completed_at IS '任务完成时间';
COMMENT ON COLUMN tasks.failed_at IS '任务失败时间';

-- ========== 自动更新 updated_at 触发器 ==========
CREATE OR REPLACE FUNCTION update_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_tasks_updated_at_trigger ON tasks;
CREATE TRIGGER update_tasks_updated_at_trigger BEFORE UPDATE ON tasks
FOR EACH ROW EXECUTE FUNCTION update_tasks_updated_at();
