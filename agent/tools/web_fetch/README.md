# WebFetch Tool

免费的网页抓取工具，无需 API Key，可直接抓取网页内容并提取可读文本。

## 功能特性

- ✅ **完全免费** - 无需任何 API Key
- 🌐 **智能提取** - 自动提取网页主要内容
- 📝 **格式转换** - 支持 HTML → Markdown/Text
- 🚀 **高性能** - 内置请求重试和超时控制
- 🎯 **智能降级** - 优先使用 Readability，可降级到基础提取

## 安装依赖

### 基础功能（必需）
```bash
pip install requests
```

### 增强功能（推荐）
```bash
# 安装 readability-lxml 以获得更好的内容提取效果
pip install readability-lxml

# 安装 html2text 以获得更好的 Markdown 转换
pip install html2text
```

## 使用方法

### 1. 在代码中使用

```python
from agent.tools.web_fetch import WebFetch

# 创建工具实例
tool = WebFetch()

# 抓取网页（默认返回 Markdown 格式）
result = tool.execute({
    "url": "https://example.com"
})

# 抓取并转换为纯文本
result = tool.execute({
    "url": "https://example.com",
    "extract_mode": "text",
    "max_chars": 5000
})

if result.status == "success":
    data = result.result
    print(f"标题: {data['title']}")
    print(f"内容: {data['text']}")
```

### 2. 在 Agent 中使用

工具会自动加载到 Agent 的工具列表中：

```python
from agent.tools import WebFetch

tools = [
    WebFetch(),
    # ... 其他工具
]

agent = create_agent(tools=tools)
```

### 3. 通过 Skills 使用

创建一个 skill 文件 `skills/web-fetch/SKILL.md`：

```markdown
---
name: web-fetch
emoji: 🌐
always: true
---

# 网页内容获取

使用 web_fetch 工具获取网页内容。

## 使用场景

- 需要读取某个网页的内容
- 需要提取文章正文
- 需要获取网页信息

## 示例

<example>
用户: 帮我看看 https://example.com 这个网页讲了什么
助手: <tool_use name="web_fetch">
  <url>https://example.com</url>
  <extract_mode>markdown</extract_mode>
</tool_use>
</example>
```

## 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `url` | string | ✅ | - | 要抓取的 URL（http/https） |
| `extract_mode` | string | ❌ | `markdown` | 提取模式：`markdown` 或 `text` |
| `max_chars` | integer | ❌ | `50000` | 最大返回字符数（最小 100） |

## 返回结果

```python
{
    "url": "https://example.com",           # 最终 URL（处理重定向后）
    "status": 200,                          # HTTP 状态码
    "content_type": "text/html",            # 内容类型
    "title": "Example Domain",              # 页面标题
    "extractor": "readability",             # 提取器：readability/basic/raw
    "extract_mode": "markdown",             # 提取模式
    "text": "# Example Domain\n\n...",      # 提取的文本内容
    "length": 1234,                         # 文本长度
    "truncated": false,                     # 是否被截断
    "warning": "..."                        # 警告信息（如果有）
}
```

## 与其他搜索工具的对比

| 工具 | 需要 API Key | 功能 | 成本 |
|------|-------------|------|------|
| `web_fetch` | ❌ 不需要 | 抓取指定 URL 的内容 | 免费 |
| `web_search` (Brave) | ✅ 需要 | 搜索引擎查询 | 有免费额度 |
| `web_search` (Perplexity) | ✅ 需要 | AI 搜索 + 引用 | 付费 |
| `browser` | ❌ 不需要 | 完整浏览器自动化 | 免费但资源占用大 |
| `google_search` | ✅ 需要 | Google 搜索 API | 付费 |

## 技术细节

### 内容提取策略

1. **Readability 模式**（推荐）
   - 使用 Mozilla 的 Readability 算法
   - 自动识别文章主体内容
   - 过滤广告、导航栏等噪音

2. **Basic 模式**（降级）
   - 简单的 HTML 标签清理
   - 正则表达式提取文本
   - 适用于简单页面

3. **Raw 模式**
   - 用于非 HTML 内容
   - 直接返回原始内容

### 错误处理

工具会自动处理以下情况：
- ✅ HTTP 重定向（最多 3 次）
- ✅ 请求超时（默认 30 秒）
- ✅ 网络错误自动重试
- ✅ 内容提取失败降级

## 测试

运行测试脚本：

```bash
cd agent/tools/web_fetch
python test_web_fetch.py
```

## 配置选项

在创建工具时可以传入配置：

```python
tool = WebFetch(config={
    "timeout": 30,              # 请求超时时间（秒）
    "max_redirects": 3,         # 最大重定向次数
    "user_agent": "..."         # 自定义 User-Agent
})
```

## 常见问题

### Q: 为什么推荐安装 readability-lxml？

A: readability-lxml 提供更好的内容提取质量，能够：
- 自动识别文章主体
- 过滤广告和导航栏
- 保留文章结构

没有它也能工作，但提取质量会下降。

### Q: 与 clawdbot 的 web_fetch 有什么区别？

A: 本实现参考了 clawdbot 的设计，主要区别：
- Python 实现（clawdbot 是 TypeScript）
- 简化了一些高级特性（如 Firecrawl 集成）
- 保留了核心的免费功能
- 更容易集成到现有项目

### Q: 可以抓取需要登录的页面吗？

A: 当前版本不支持。如需抓取需要登录的页面，请使用 `browser` 工具。

## 参考

- [Mozilla Readability](https://github.com/mozilla/readability)
- [Clawdbot Web Tools](https://github.com/moltbot/moltbot)
