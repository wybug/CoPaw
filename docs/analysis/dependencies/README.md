# CoPaw 依赖版本分析

本目录包含 CoPaw 各版本的依赖分析文档，用于追踪软件依赖变化和进行版本对比。

---

## 版本历史

| 版本 | 分析文档 | 发布日期 | 主要变更 |
|------|----------|----------|----------|
| v0.0.6 | [v0.0.6-dependencies.md](./v0.0.6-dependencies.md) | 2026-03-11 | 初始文档 |

---

## 快速对比

### Python 核心依赖版本

| 依赖包 | v0.0.6 |
|--------|--------|
| agentscope | ==1.0.16.dev0 |
| agentscope-runtime | ==1.1.0 |
| reme-ai | ==0.3.0.6b3 |
| httpx | >=0.27.0 |
| uvicorn | >=0.40.0 |

### 前端核心依赖版本

| 依赖包 | v0.0.6 |
|--------|--------|
| react | ^18 |
| antd | ^5.29.1 |
| vite | ^6.3.5 |
| typescript | ~5.8.3 |
| @agentscope-ai/chat | ^1.1.51 |

---

## 支持的通道版本对比

| 通道 | v0.0.6 |
|------|--------|
| DingTalk | ✅ dingtalk-stream >=0.24.3 |
| Feishu | ✅ lark-oapi >=1.5.3 |
| QQ | ✅ NapCat/LLOneBot |
| Discord | ✅ discord-py >=2.3 |
| iMessage | ✅ (仅 macOS) |
| Telegram | ✅ python-telegram-bot >=20.0 |
| Matrix | ✅ matrix-nio >=0.24.0 |
| MQTT | ✅ paho-mqtt >=2.0.0 |

---

## 文档说明

### 文件命名规范

- 格式: `v{VERSION}-dependencies.md`
- 示例: `v0.0.6-dependencies.md`

### 文档内容结构

每个版本的分析文档包含：

1. **概述** - 版本信息和 Python 要求
2. **Python 后端依赖** - 按功能分类
   - 核心框架
   - 通道 SDK (按平台)
   - AI/ML 相关
   - 自动化与调度
   - 可选依赖
3. **前端依赖** - React/TypeScript 依赖
4. **依赖架构图** - 可视化依赖关系
5. **支持的平台通道** - 通道状态和 SDK
6. **版本兼容性说明** - Python/系统要求
7. **安全注意事项**

---

## 如何使用

### 查看特定版本依赖

```bash
# 查看当前版本
cat docs/analysis/dependencies/v0.0.6-dependencies.md

# 比较两个版本的差异
diff docs/analysis/dependencies/v0.0.5-dependencies.md \
     docs/analysis/dependencies/v0.0.6-dependencies.md
```

### 生成新版本文档

当发布新版本时，基于 `pyproject.toml` 和 `console/package.json` 生成新的依赖分析文档。

---

## 维护说明

- 新版本发布时，需同步更新本目录
- 重大依赖变更应在文档中标注
- 保持文档格式一致性，便于版本对比
