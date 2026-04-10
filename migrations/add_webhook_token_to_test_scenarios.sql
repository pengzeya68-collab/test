-- 添加 webhook_token 字段到 test_scenarios 表（用于 CI/CD 外部触发）
ALTER TABLE test_scenarios ADD COLUMN webhook_token VARCHAR(64);
CREATE UNIQUE INDEX ix_test_scenarios_webhook_token ON test_scenarios(webhook_token);
