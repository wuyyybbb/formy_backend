-- ============================================
-- Formy 任务表 (tasks)
-- ============================================
-- 存储用户的AI图片处理任务记录
-- 包含任务状态、输入输出、结果等完整信息

CREATE TABLE IF NOT EXISTS tasks (
    -- ========== 主键 ==========
    task_id VARCHAR(50) PRIMARY KEY,
    
    -- ========== 用户关联 ==========
    user_id VARCHAR(50) NOT NULL,
    -- 外键约束（关联到 users 表）
    -- FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- ========== 任务基本信息 ==========
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- 状态值: 'pending', 'processing', 'done', 'failed', 'cancelled'
    
    mode VARCHAR(30) NOT NULL,
    -- 编辑模式: 'HEAD_SWAP', 'BACKGROUND_CHANGE', 'POSE_CHANGE'
    
    progress INTEGER NOT NULL DEFAULT 0,
    -- 进度百分比 (0-100)
    
    current_step TEXT,
    -- 当前步骤描述
    
    -- ========== 输入信息 ==========
    source_image VARCHAR(255) NOT NULL,
    -- 源图片 file_id
    
    reference_image VARCHAR(255),
    -- 参考图片 file_id (可选，用于换头/换背景/换姿势)
    
    config JSONB,
    -- 配置参数（JSON格式）
    -- 示例: {"quality": "high", "size": "1024x1024", "style": "natural"}
    
    -- ========== 输出信息 ==========
    result JSONB,
    -- 任务结果（JSON格式）
    -- 示例: {
    --   "output_image": "path/to/output.png",
    --   "thumbnail": "path/to/thumb.png",
    --   "metadata": {...}
    -- }
    
    error JSONB,
    -- 错误信息（JSON格式）
    -- 示例: {
    --   "code": "PROCESSING_FAILED",
    --   "message": "图片处理失败",
    --   "details": "..."
    -- }
    
    -- ========== 算力信息 ==========
    credits_consumed INTEGER,
    -- 消耗的算力值
    
    -- ========== 时间信息 ==========
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    -- 任务创建时间
    
    updated_at TIMESTAMP WITH TIME ZONE,
    -- 最后更新时间
    
    completed_at TIMESTAMP WITH TIME ZONE,
    -- 任务完成时间
    
    failed_at TIMESTAMP WITH TIME ZONE,
    -- 任务失败时间
    
    processing_time REAL
    -- 处理耗时（秒）
);

-- ========== 索引 ==========
-- 按用户查询任务（最常用）
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);

-- 按用户和状态查询
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);

-- 按用户和模式查询
CREATE INDEX IF NOT EXISTS idx_tasks_user_mode ON tasks(user_id, mode);

-- 按创建时间排序（用于历史记录）
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- 按用户和创建时间（组合索引，性能最优）
CREATE INDEX IF NOT EXISTS idx_tasks_user_created ON tasks(user_id, created_at DESC);

-- ========== 注释 ==========
COMMENT ON TABLE tasks IS '用户AI图片处理任务表';
COMMENT ON COLUMN tasks.task_id IS '任务ID（格式: task_xxxxxxxx）';
COMMENT ON COLUMN tasks.user_id IS '用户ID（关联 users 表）';
COMMENT ON COLUMN tasks.status IS '任务状态: pending/processing/done/failed/cancelled';
COMMENT ON COLUMN tasks.mode IS '编辑模式: HEAD_SWAP/BACKGROUND_CHANGE/POSE_CHANGE';
COMMENT ON COLUMN tasks.progress IS '任务进度 (0-100)';
COMMENT ON COLUMN tasks.source_image IS '源图片 file_id';
COMMENT ON COLUMN tasks.reference_image IS '参考图片 file_id（可选）';
COMMENT ON COLUMN tasks.config IS '任务配置参数（JSON）';
COMMENT ON COLUMN tasks.result IS '任务结果（JSON）';
COMMENT ON COLUMN tasks.error IS '错误信息（JSON）';
COMMENT ON COLUMN tasks.credits_consumed IS '消耗的算力值';
COMMENT ON COLUMN tasks.created_at IS '任务创建时间';
COMMENT ON COLUMN tasks.updated_at IS '最后更新时间';
COMMENT ON COLUMN tasks.completed_at IS '任务完成时间';
COMMENT ON COLUMN tasks.failed_at IS '任务失败时间';
COMMENT ON COLUMN tasks.processing_time IS '处理耗时（秒）';
