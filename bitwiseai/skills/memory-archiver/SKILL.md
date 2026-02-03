---
name: memory-archiver
description: 将当前 CLI 对话历史归档到长期记忆。支持自动生成摘要、保留原始对话、标记短期记忆。适用于保存重要技术讨论、解决方案回顾、决策记录等场景。
license: MIT
metadata:
  author: BitwiseAI
  version: "1.0.0"
---

# 记忆归档工具

## 功能概述

本技能提供对话历史归档功能：
- 自动总结对话内容（保持原意，不篡改原意）
- 存储到长期记忆（MEMORY.md）
- 在短期记忆中添加归档标记
- 清空当前 CLI 对话历史

## 工具说明

### archive_current_conversation

将当前 CLI 会话的对话历史归档到长期记忆。

**参数**:
- `summary_title` (string, 可选): 归档标题，不提供则自动生成
- `include_summary` (boolean, 可选): 是否生成智能摘要，默认为 true

**返回**:
归档结果信息，包含归档标题和消息数量。

**示例**:
```python
# 自动归档当前对话
archive_current_conversation()

# 指定标题归档
archive_current_conversation("PyTorch 量化问题解决方案")

# 仅保存原始对话，不生成摘要
archive_current_conversation("原始记录", include_summary=False)
```

## 使用场景

- 保存重要的技术讨论和解决方案
- 归档决策过程供后续参考
- 记录调试过程和最终解决方法
- 定期整理对话历史，保持上下文清晰

## 注意事项

- 归档后会清空当前 CLI 对话历史
- 归档内容可在 MEMORY.md 中查看
- 可通过记忆搜索功能检索已归档的对话
- 摘要生成会尽量保持原意，不添加不存在的信息
