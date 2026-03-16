# 企业版 Skills Hub 测试计划 / Enterprise Skills Hub Test Plan

## 测试概述 / Test Overview

本测试计划涵盖 CoPaw 企业版 Skills Hub 的完整测试，包括：
- 签名生成与验证
- 审批流程
- 存储模块
- API 接口
- CoPaw 客户端集成
- 端到端集成测试

This test plan covers comprehensive testing for CoPaw Enterprise Skills Hub, including:
- Signature generation and verification
- Approval workflow
- Storage modules
- API endpoints
- CoPaw client integration
- End-to-end integration tests

---

## 1. 单元测试 / Unit Tests

### 1.1 签名模块测试 / Signature Module Tests

| 测试用例 / Test Case | 描述 / Description | 预期结果 / Expected Result |
|---------------------|-------------------|---------------------------|
| `test_generate_key_pair` | 生成 RSA-2048 密钥对 / Generate RSA-2048 key pair | 返回有效的 PEM 格式私钥和公钥 / Return valid PEM format private and public keys |
| `test_sign_bundle` | 对技能包进行签名 / Sign a skill bundle | 返回 Base64 编码的签名 / Return Base64-encoded signature |
| `test_verify_valid_signature` | 验证有效签名 / Verify valid signature | 返回 True / Return True |
| `test_verify_tampered_bundle` | 验证被篡改的包 / Verify tampered bundle | 返回 False / Return False |
| `test_verify_wrong_signature` | 验证错误签名 / Verify wrong signature | 返回 False / Return False |

**运行命令 / Run Command:**
```bash
# 使用 uv 环境
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py::TestSignatureModule -v

# 或直接运行
.venv_local/bin/python tests/integration/test_enterprise_hub.py TestSignatureModule
```

### 1.2 存储模块测试 / Storage Module Tests

#### 1.2.1 技能存储 / Skill Storage

| 测试用例 / Test Case | 描述 / Description | 预期结果 / Expected Result |
|---------------------|-------------------|---------------------------|
| `test_create_pending_skill` | 创建待审批技能 / Create pending skill | 技能状态为 pending / Skill status is pending |
| `test_get_skill` | 获取技能信息 / Get skill info | 返回正确的技能数据 / Return correct skill data |
| `test_approve_skill` | 审批通过技能 / Approve skill | 状态变为 approved，包含签名 / Status changes to approved with signature |
| `test_search_approved_skills` | 搜索已审批技能 / Search approved skills | 返回已审批的技能列表 / Return list of approved skills |
| `test_reject_skill` | 拒绝技能 / Reject skill | 状态变为 rejected / Status changes to rejected |

#### 1.2.2 审批存储 / Approval Storage

| 测试用例 / Test Case | 描述 / Description | 预期结果 / Expected Result |
|---------------------|-------------------|---------------------------|
| `test_create_approval` | 创建审批请求 / Create approval request | 返回审批 ID / Return approval ID |
| `test_list_pending` | 列出待审批请求 / List pending requests | 返回待审批列表 / Return pending list |
| `test_update_status` | 更新审批状态 / Update approval status | 状态成功更新 / Status updated successfully |
| `test_get_approval` | 获取审批详情 / Get approval details | 返回完整审批信息 / Return complete approval info |

#### 1.2.3 审计日志存储 / Audit Log Storage

| 测试用例 / Test Case | 描述 / Description | 预期结果 / Expected Result |
|---------------------|-------------------|---------------------------|
| `test_create_log` | 创建审计日志 / Create audit log | 返回日志 ID / Return log ID |
| `test_list_logs` | 查询审计日志 / Query audit logs | 返回匹配的日志列表 / Return matching log list |
| `test_filter_by_employee` | 按员工 ID 过滤 / Filter by employee ID | 只返回该员工的日志 / Only return logs for that employee |
| `test_filter_by_action` | 按操作类型过滤 / Filter by action type | 只返回指定操作的日志 / Only return logs for specified action |

**运行命令 / Run Command:**
```bash
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py::TestSkillStorage -v
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py::TestApprovalStorage -v
```

---

## 2. CoPaw 客户端测试 / CoPaw Client Tests

### 2.1 企业模式检测 / Enterprise Mode Detection

| 测试用例 / Test Case | 描述 / Description | 预期结果 / Expected Result |
|---------------------|-------------------|---------------------------|
| `test_is_enterprise_mode_false` | 未配置公钥时 / No public key configured | 返回 False / Return False |
| `test_is_enterprise_mode_true` | 配置公钥后 / With public key configured | 返回 True / Return True |
| `test_get_employee_id` | 获取员工 ID / Get employee ID | 返回环境变量中的 ID 或 "unknown" / Return ID from env or "unknown" |

### 2.2 企业模式强制执行 / Enterprise Mode Enforcement

| 测试用例 / Test Case | 描述 / Description | 预期结果 / Expected Result |
|---------------------|-------------------|---------------------------|
| `test_enforce_enterprise_mode_blocks_clawhub` | 尝试访问 clawhub.ai / Try to access clawhub.ai | 抛出 ValueError 异常 / Raise ValueError exception |
| `test_enforce_enterprise_mode_allows_custom_hub` | 访问企业 Hub / Access enterprise hub | 正常执行，不抛出异常 / Execute normally, no exception |

### 2.3 签名验证 / Signature Verification

| 测试用例 / Test Case | 描述 / Description | 预期结果 / Expected Result |
|---------------------|-------------------|---------------------------|
| `test_verify_signature` | 验证有效签名 / Verify valid signature | 返回 True / Return True |
| `test_verify_tampered_fails` | 验证被篡改的签名 / Verify tampered signature | 返回 False / Return False |
| `test_verify_missing_signature` | 缺少签名时 / When signature missing | 抛出 ValueError 异常 / Raise ValueError exception |

**运行命令 / Run Command:**
```bash
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py::TestCopawEnterpriseMode -v
```

---

## 3. API 接口测试 / API Endpoint Tests

### 3.1 健康检查 / Health Check

```bash
curl http://localhost:9998/health
# 预期输出 / Expected: {"status": "healthy", "service": "copaw-enterprise-hub"}
```

### 3.2 技能搜索 / Skill Search

```bash
curl "http://localhost:9998/api/v1/search?q=test&limit=10"
# 预期输出 / Expected: {"items": [...]}
```

### 3.3 提交技能 / Submit Skill

```bash
curl -X POST http://localhost:9998/api/v1/skills/submit \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "test-skill",
    "name": "Test Skill",
    "description": "A test skill",
    "content": "# Test Skill\n\nTest content",
    "version": "1.0.0"
  }'
# 预期输出 / Expected: {"slug": "test-skill", "status": "pending", "approval_id": "..."}
```

### 3.4 获取技能详情 / Get Skill Details

```bash
curl http://localhost:9998/api/v1/skills/test-skill
# 预期输出 / Expected: 包含 signature 字段 / Contains signature field
```

### 3.5 审批技能 / Approve Skill

```bash
curl -X POST http://localhost:9998/api/v1/approvals/{approval_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"comment": "Approved for testing"}'
# 预期输出 / Expected: {"status": "approved", "skill": "test-skill"}
```

---

## 4. 集成测试 / Integration Tests

### 4.1 完整技能生命周期 / Complete Skill Lifecycle

1. **提交技能 / Submit Skill**
   ```bash
   # 提交新技能
   curl -X POST http://localhost:9998/api/v1/skills/submit ...
   ```

2. **审批通过 / Approve**
   ```bash
   # 获取待审批列表
   curl http://localhost:9998/api/v1/approvals/pending
   # 审批通过
   curl -X POST http://localhost:9998/api/v1/approvals/{id}/approve ...
   ```

3. **搜索并安装 / Search and Install**
   ```bash
   # CoPaw 客户端搜索
   export COPAW_SKILLS_HUB_BASE_URL="http://localhost:9998"
   export COPAW_SKILLS_HUB_PUBLIC_KEY="..."
   python -c "from copaw.agents.skills_hub import search_hub_skills; print(search_hub_skills('test'))"
   ```

### 4.2 签名验证流程 / Signature Verification Flow

1. 服务器生成签名 ✅
2. 返回签名给客户端 ✅
3. 客户端验证签名 ✅
4. 篡改检测 ❌（应失败）

### 4.3 审计日志上报 / Audit Log Reporting

1. 配置员工 ID ✅
2. 执行操作（搜索/安装/启用/禁用）✅
3. 验证日志上报 ✅
4. 查询审计日志 ✅

**运行完整集成测试 / Run Full Integration Test:**
```bash
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py::TestIntegration -v
```

---

## 5. 性能测试 / Performance Tests

| 测试项 / Test Item | 指标 / Metric | 目标 / Target |
|-------------------|--------------|--------------|
| 签名生成时间 / Signature generation | < 100ms | 签名 1KB bundle / Sign 1KB bundle |
| 签名验证时间 / Signature verification | < 50ms | 验证 1KB bundle / Verify 1KB bundle |
| 技能搜索响应 / Skill search response | < 200ms | 查询 20 条结果 / Query 20 results |
| 技能详情获取 / Get skill details | < 100ms | 包含文件内容 / With file content |

---

## 6. 安全测试 / Security Tests

| 测试项 / Test Item | 描述 / Description |
|-------------------|-------------------|
| **签名篡改检测** / Signature Tamper Detection | 修改 bundle 内容后验证应失败 / Verification should fail after modifying bundle |
| **私钥保护** / Private Key Protection | 私钥不应出现在日志中 / Private key should not appear in logs |
| **路径遍历防护** / Path Traversal Protection | 文件路径应阻止 `..` / File paths should block `..` |
| **SQL 注入防护** / SQL Injection Protection | 查询参数应安全处理 / Query parameters should be safely handled |
| **公钥认证** / Public Key Validation | 无效公钥应被拒绝 / Invalid public key should be rejected |

---

## 7. 运行所有测试 / Run All Tests

### 快速测试 / Quick Test
```bash
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py -v
```

### 详细输出 / Verbose Output
```bash
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py -vv --tb=short
```

### 生成覆盖率报告 / Generate Coverage Report
```bash
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py --cov=hub_enterprise --cov-report=html
```

### 只运行特定测试类 / Run Specific Test Class
```bash
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py::TestSignatureModule -v
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py::TestSkillStorage -v
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py::TestCopawEnterpriseMode -v
.venv_local/bin/python -m pytest tests/integration/test_enterprise_hub.py::TestIntegration -v
```

---

## 8. 测试检查清单 / Test Checklist

### 部署前检查 / Pre-Deployment Checklist

- [ ] 所有单元测试通过 / All unit tests pass
- [ ] 所有集成测试通过 / All integration tests pass
- [ ] 签名验证功能正常 / Signature verification works correctly
- [ ] 审批流程正常 / Approval workflow works correctly
- [ ] 审计日志正常记录 / Audit logs are recorded correctly
- [ ] 企业模式强制执行有效 / Enterprise mode enforcement works
- [ ] API 文档可访问 / API documentation is accessible
- [ ] 性能指标达标 / Performance metrics meet targets

### 安全检查 / Security Checklist

- [ ] 私钥安全存储 / Private key is securely stored
- [ ] 公钥分发渠道安全 / Public key distribution is secure
- [ ] 篡改检测有效 / Tamper detection is effective
- [ ] 路径遍历防护有效 / Path traversal protection is effective
- [ ] SQL 注入防护有效 / SQL injection protection is effective

---

## 9. 故障排查 / Troubleshooting

### 常见问题 / Common Issues

| 问题 / Issue | 解决方案 / Solution |
|-------------|-------------------|
| 导入错误 cryptography / Import error cryptography | 安装依赖: `pip install cryptography` / Install dependency |
| 服务器无法启动 / Server fails to start | 检查端口占用 / Check port usage |
| 签名验证失败 / Signature verification fails | 检查公钥配置 / Check public key configuration |
| 审计日志上报失败 / Audit log reporting fails | 检查网络连接 / Check network connection |

---

## 10. 测试报告模板 / Test Report Template

```
测试执行报告 / Test Execution Report
=====================================

日期 / Date: _______________
测试人员 / Tester: _______________
环境 / Environment: _______________

测试结果汇总 / Test Results Summary:
-----------------------------------
单元测试 / Unit Tests:          ___ / ___ 通过 / passed
集成测试 / Integration Tests:    ___ / ___ 通过 / passed
API 测试 / API Tests:           ___ / ___ 通过 / passed
安全测试 / Security Tests:      ___ / ___ 通过 / passed

问题记录 / Issues Found:
---------------------
1.
2.

建议 / Recommendations:
-----------------------
1.
2.

签名 / Signature: _______________
```
