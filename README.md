# TE to Kindle

[![TE to Kindle](https://github.com/lkcp/te-to-kindle/actions/workflows/te-to-kindle.yml/badge.svg)](https://github.com/lkcp/te-to-kindle/actions/workflows/te-to-kindle.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[English](./README.en.md) | 简体中文

每周日早上自动把最新一期《经济学人》从 [evanbio/The_Economist](https://github.com/evanbio/The_Economist) 推送到你的 Kindle 邮箱。基于 GitHub Actions，无需服务器，免费。

## 特性

- ⏰ **定时推送**：每周日北京时间 09:10 自动运行
- 📚 **格式可选**：mobi / epub / azw3 / pdf（手动触发时可选）
- 🔁 **自动重试**：上游延迟时，每 10 分钟重试一次，最多 6 次
- 🪪 **幂等去重**：通过 `last_sent.txt` 记录已推送的期号，不重复发送
- 🔒 **凭证安全**：所有敏感信息走 GitHub Secrets，仓库内零硬编码

## 快速开始

### 1. Fork 或克隆本仓库

```bash
gh repo create te-to-kindle --private --clone
# 把本仓库的文件拷过去并 push
```

### 2. 准备 Kindle 推送邮箱

1. 登录 [Amazon 管理我的内容和设备](https://www.amazon.cn/hz/mycd)
2. **设备 → 你的 Kindle**，记下推送邮箱（形如 `xxx@kindle.cn` 或 `xxx@kindle.com`）
3. **设置 → 个人文档设置 → 已认可的发件人邮箱列表**，把你的发件邮箱（如 `you@gmail.com`）加进去

> ⚠️ 不加白名单的话，附件会被亚马逊静默丢弃。

### 3. 准备发件邮箱（SMTP）

以 Gmail 为例：

1. 开启两步验证
2. 生成 [应用专用密码](https://myaccount.google.com/apppasswords)（16 位）
3. SMTP 配置：`smtp.gmail.com:587`

也支持 QQ / 163 / Outlook，把对应的 SMTP 地址和授权码填进 Secrets 即可。

### 4. 配置 GitHub Secrets

仓库 **Settings → Secrets and variables → Actions → New repository secret**，添加：

| Secret 名 | 必填 | 示例 | 说明 |
|---|:-:|---|---|
| `KINDLE_EMAIL` | ✅ | `you_abc@kindle.cn` | Kindle 推送邮箱 |
| `SMTP_USER` | ✅ | `you@gmail.com` | 发件邮箱（需在 Amazon 白名单） |
| `SMTP_PASS` | ✅ | `abcd efgh ijkl mnop` | SMTP 授权码（不是登录密码！） |
| `SMTP_HOST` | ⬜ | `smtp.gmail.com` | 默认 Gmail |
| `SMTP_PORT` | ⬜ | `587` | 默认 587 |

### 5. 手动测试

仓库 **Actions → TE to Kindle → Run workflow**，选格式后触发。等 1–2 分钟看日志，出现 `[done] sent` 就成功了，Kindle 联网后会自动收到。

## 配置项

### 修改默认格式

新版 Kindle 推荐用 epub。编辑 `.github/workflows/te-to-kindle.yml`：

```yaml
TE_FORMAT: ${{ inputs.format || 'epub' }}   # 把 'mobi' 改成 'epub'
```

### 修改推送时间

编辑 `.github/workflows/te-to-kindle.yml` 里的 cron。**注意 cron 用 UTC，北京时间减 8 小时**：

```yaml
schedule:
  - cron: "10 1 * * 0"   # 北京时间 周日 09:10
  # - cron: "0 12 * * 0" # 北京时间 周日 20:00
```

GitHub Actions 的 schedule 在高峰期可能延迟数分钟，已通过脚本内重试机制兜底。

## 文件结构

```
.
├── te_to_kindle.py                    # 主脚本
├── requirements.txt                   # Python 依赖
├── last_sent.txt                      # 已推送期号（自动维护）
└── .github/workflows/te-to-kindle.yml # GitHub Actions 工作流
```

## 工作原理

1. **算目标期号**：按北京时间找出本周六的日期，对应上游仓库的 `TE-YYYY-MM-DD/` 文件夹
2. **拉文件列表**：调 GitHub API 检查目标文件夹是否已上传；未上传则等 10 分钟重试
3. **下载 + 发邮件**：从 raw.githubusercontent.com 拉对应格式的文件，用 SMTP 以附件形式发到 Kindle 邮箱，邮件主题写 `convert` 让亚马逊自动转格式
4. **记录状态**：成功后把期号写入 `last_sent.txt` 并 commit 回仓库，下次同一期直接跳过

## 公开仓库安全说明

把本仓库设为 public 是安全的：

- GitHub Secrets 在日志里自动打码，fork 也读不到
- Workflow 仅响应 `schedule` 和 `workflow_dispatch`，外部 PR 触发不到
- 公开仓库的 Actions 免费且不消耗私有配额

唯一的注意点：如果你修改脚本时新增了 `print` 调试，**不要打印邮箱、密码等敏感信息**——公开仓库的日志任何人可见。

## 常见问题

**Q: Kindle 一直没收到？**
- 确认发件邮箱在 Amazon 白名单里
- 确认 Kindle 已联网（Wi-Fi 模式下需连接）
- 看 Actions 日志是否报 SMTP 错（535 通常是授权码错误）

**Q: Actions 日志显示 "not found upstream after 6 attempts"？**
- 上游仓库当周没更新，或文件夹命名规则变了
- 手动检查 [evanbio/The_Economist](https://github.com/evanbio/The_Economist)，确认本周文件夹是否存在

**Q: 想本地手动跑一次？**

```bash
pip install -r requirements.txt
export KINDLE_EMAIL=xxx@kindle.cn
export SMTP_USER=you@gmail.com
export SMTP_PASS='your-app-password'
python te_to_kindle.py
```

**Q: 想跳过本周已推送的限制？**
- 删掉仓库里的 `last_sent.txt` 再触发 workflow

## 致谢

- 数据来源：[evanbio/The_Economist](https://github.com/evanbio/The_Economist)
- 仅供个人学习使用，请支持正版 [The Economist](https://www.economist.com/)

## License

MIT
