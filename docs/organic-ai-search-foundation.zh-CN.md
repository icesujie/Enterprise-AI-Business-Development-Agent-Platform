# 自然搜索与 AI 搜索技术基础

**阶段：** 3.2.4A  
**状态：** 技术基础已实现  
**主要工程基线：** 英文  
**英文原文：** `organic-ai-search-foundation.en.md`

## 1. 目的和边界

Phase 3.2.4A 让现有 Sari Arta 公开网站在技术上能够被传统搜索系统和 AI 搜索系统理解。本阶段不生成、审批或发布营销内容。Phase 3.2 业务验收仍处于延期状态，营销内容智能体的生产激活仍然禁用。

本技术基础包括：

- 明确的公开/私有爬取边界；
- Canonical URL、服务端渲染 Metadata 和公开结构化数据；
- 可维护的 Sitemap 策略；
- 不绑定特定供应商的爬虫就绪能力；
- 默认禁用的 IndexNow 适配器；
- 保留现有 CRM 询盘流程的轻量搜索获客归因。

## 2. 搜索信任边界

| 路由类别 | 示例 | 搜索行为 |
|---|---|---|
| 标准公开页面 | `/`、`/solutions`、`/industries`、`/projects`、`/about`、`/contact` | `index, follow`；Canonical URL；进入 Sitemap |
| 未来已批准公开页面 | `/solutions/*`、`/industries/*`、`/projects/*`、`/guides/*` | 只有明确公开且状态为 `published` 时才符合条件 |
| 内部工作区 | `/dashboard`、`/leads`、`/opportunities`、`/knowledge`、`/marketing-content` | Robots 和 Sitemap 排除；使用 `noindex` Metadata 和 `X-Robots-Tag` |
| 认证和私有录入 | `/login`、`/inquiry` | 排除并设置 `noindex` |
| API 和未知路由 | `/api/*`、不存在的页面 | 按适用规则排除；不存在的页面返回正常非成功状态 |

`robots.txt` 只是爬虫指导，不是授权控制。认证、租户隔离、RBAC、PostgreSQL RLS 以及知识/内容治理仍然是安全控制。

## 3. 可爬取性和可索引性

### 3.1 Robots 策略

`/robots.txt` 对以下爬虫提供明确的通用策略：

- 通用爬虫（`*`）；
- Googlebot；
- Bingbot；
- OAI-SearchBot。

当前命名爬虫使用相同的公开/私有边界。这让审核规则保持明确，但不会让任何爬虫访问已认证数据。如果未来业务或法律政策需要按爬虫区分，可以集中修改该策略。

### 3.2 私有路由纵深防护

内部路由同时返回：

```text
robots meta: noindex, nofollow, noarchive, nosnippet
X-Robots-Tag: noindex, nofollow, noarchive, nosnippet
```

这些路由也不会出现在 Sitemap 中。响应头由 Next.js Proxy 边界设置，因此也能覆盖重定向以及未渲染工作区 Layout 的响应。

### 3.3 服务端渲染公开页面

公开页面继续使用 Next.js 服务端渲染输出，Metadata 会出现在初始 HTML 中。实现不依赖仅在浏览器运行的 SEO 覆盖层，也不会提供爬虫专用隐藏内容。

## 4. Sitemap 策略

`/sitemap.xml` 当前只列出六个标准公开页面，并且不会伪造 `lastModified` 时间。

共享 Sitemap 构建器支持未来发布记录，但只有满足全部条件才会加入：

1. 记录被明确标记为公开；
2. 状态为 `published`；
3. 路径位于批准的公开前缀下；
4. URL 不包含 Query 或 Fragment；
5. 不是内部路由。

未来公开内容只有在受治理内容的准确版本经过人工审批并发布后，才能连接到该构建器。Draft、Review、Archived、私有或内部记录绝不能进入 Sitemap。

## 5. Metadata 架构

每个标准公开页面都有与可见页面用途一致的英文和中文 Metadata：

- 简洁的页面标题；
- 原创页面描述；
- 一个绝对 Canonical URL；
- Open Graph 标题、描述、URL、站点身份和 Locale；
- 语言 Metadata；
- Index/Follow 指令。

根 Metadata 把站点名称定义为 **Sari Arta**，定位定义为 **Indonesia Commercial Kitchen Engineering Partner**。站点验证 Token 是配置值，不是写入源码的凭据：

```text
GOOGLE_SITE_VERIFICATION
BING_SITE_VERIFICATION
NEXT_PUBLIC_SITE_URL
```

当前网站通过偏好 Cookie 在同一个 Canonical URL 下显示英文或中文，因此不会输出具有误导性的语言替代 URL。如果以后公开路由策略改成独立语言 URL，可以再增加 `hreflang`。

## 6. 结构化数据

公开营销 Layout 输出可复用的 JSON-LD：

- `Organization`；
- `WebSite`。

公开栏目页面输出 `BreadcrumbList`。系统还为未来受治理发布流程准备了可复用的 `Article`、基于 Article 的案例和 `Service` 构建器。

结构化数据只包含已在批准网站内容中出现的事实。系统不会虚构地址、评分、奖项、认证、客户名称、价格、交付承诺或绩效指标。

当相应公开内容模型存在后，未来还可以增加 FAQ 和更具体的公开实体构建器。系统评估过 `Product`，但当前网站定位是工程服务网站，而且没有受治理的公开 Product Entity 或 Offer 模型，因此有意延期。结构化数据必须描述页面可见内容，不能成为另一套无依据主张的来源。

## 7. AI 搜索就绪

本设计不绑定特定供应商。所有搜索系统获得相同的可见事实、服务端渲染内容和机器可读身份信号。就绪能力依赖：

- 一致的企业和服务命名；
- 清晰的 Solution、Industry 和 Project 页面用途；
- 事实性公开证据和来源；
- Canonical URL 和稳定页面身份；
- 可爬取内容，不使用爬虫专用隐藏文本；
- 未来阶段继续执行人工治理发布。

系统不承诺任何供应商一定会索引、排名、引用或纳入回答。

## 8. IndexNow 就绪

服务端专用 IndexNow 适配器当前处于休眠状态，普通页面渲染、内容生成或 CRM 询盘不会调用它。只有设置以下配置才会启用：

```text
INDEXNOW_ENABLED=true
```

适配器还要求有效 Key、同源 HTTPS Key 地址、非本地生产站点 URL 和 HTTPS Endpoint。候选 URL 必须通过与 Sitemap 相同的公开/已发布策略。

生产启用前，运维人员必须：

1. 生成并安全保存生产 Key；
2. 在配置的公开 HTTPS 地址提供所需 Key 文件；
3. 验证生产 Canonical 主机；
4. 只把提交动作连接到准确且已人工批准的发布事件；
5. 监控失败，同时不让通知失败阻塞发布；
6. 记录 Key 轮换和禁用方法。

IndexNow 通知不保证一定被爬取或索引。

## 9. 搜索管理平台就绪

项目已经为未来的人工接入流程做好准备：

1. 配置生产 HTTPS `NEXT_PUBLIC_SITE_URL`；
2. 在生产 Secret 中设置 Google Search Console 和 Bing Webmaster 验证 Token；
3. 部署并检查渲染后的验证 Metadata；
4. 在各供应商控制台验证域名/站点所有权；
5. 提交生产 `/sitemap.xml`；
6. 检查索引覆盖范围和爬虫响应；
7. 把供应商账户凭据保留在应用之外。

本阶段没有创建搜索供应商账户、凭据或生产站点 Property。

## 10. 获客归因

浏览器记录最小化、Session 级的首次触点分类：

| 分类 | 示例信号 |
|---|---|
| `organic_google` | Google Referrer 或明确的 Organic Google UTM |
| `organic_bing` | Bing Referrer 或明确的 Organic Bing UTM |
| `ai_search` | 可识别的 AI 搜索 Referrer，例如 ChatGPT、Perplexity、Copilot 或 Gemini |
| `social` | 可识别的社交 Referrer 或 Social UTM |
| `referral` | 其他外部 Referrer |
| `direct` | 没有符合条件的外部信号 |

系统只保留分类、Landing Path 和 Referrer Domain，不保存完整 Referrer URL、Query String 或搜索关键词。

现有业务来源仍然是正式来源：

- 标准联系表单：`website`；
- 公开助手线索：`website_ai_assistant`。

搜索归因作为补充的 Lead Requirements Metadata 保存，不会改变线索状态、负责人、资格评估、去重、审计或 CRM 流程。这是归因基础，不是分析平台。

## 11. 安全与治理

- 公开搜索可见性永远不能绕过租户、RBAC、RLS、智能体、知识或内容权限。
- 未来可索引动态内容只能来自公开、已批准、已发布的内容。
- 内部价格、供应商数据、私有客户数据、CRM 记录、内部 SOP、工程笔记和机密商业条款始终禁止公开。
- IndexNow 默认禁用，没有自动触发器。
- 验证 Token 和 IndexNow Key 继续由环境配置/Secret 管理。
- 任何爬虫都不能访问 API、CRM、私有知识、营销工作区或 Agent Playground。
- Phase 3.2 业务验收阻塞条件仍然禁止生产生成内容激活和自动发布。

## 12. 验证与回归覆盖

自动化测试验证：

- 六个标准 Sitemap URL 和内部路径排除；
- 未来 Sitemap 发布过滤；
- 通用、Googlebot、Bingbot 和 OAI-SearchBot 策略；
- 私有路由 `noindex` 指令；
- 中英文 Canonical 与 Open Graph Metadata；
- Organization、WebSite、Breadcrumb 和未来 Article、案例、Service JSON-LD 构建；
- 安全 JSON-LD 序列化；
- 归因分类和公开助手来源保留；
- IndexNow 禁用状态和合格 URL 过滤。

## 13. 生产剩余工作

生产搜索上线前还需要：

- 选择并配置最终 HTTPS Canonical 域名；
- 验证 Google Search Console 和 Bing Webmaster Tools；
- 提交并监控生产 Sitemap；
- 测试 CDN/WAF 对已审核爬虫的行为；
- 决定是否需要独立语言 URL 和 `hreflang`；
- 批准第一批真实公开内容和结构化事实；
- 完成 Referrer 归因隐私审核；
- 决定是否启用 IndexNow，并实现其受批准发布事件触发器；
- 只有在单独批准的测量范围内才能增加 Analytics。

以上事项不会授权营销内容智能体生产激活或自动发布。
