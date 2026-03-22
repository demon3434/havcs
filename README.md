# 项目说明
感谢原作者的代码 [https://github.com/cnk700i/havcs](https://github.com/cnk700i/havcs)  
请先看原作者的说明。  

本人使用自建技能的方案，由于原版代码许久不更新，本人根据自身需要做了一些修改，以适配较新版本的HA。  

## 2026-03-22 修复说明
- 适配 Home Assistant `2026.3` 的配置流模式，修复旧代码只从 YAML 读取 `http.clients`，导致授权校验和 token 校验失败的问题。
- 修复小度 OAuth 授权流程，兼容 `https://xiaodu.baidu.com` 和 `https://xiaodu-dbp.baidu.com` 两种回调来源。
- 修复 HAVCS 授权页重复复用旧 `login_flow` 的问题，改为每次授权时向 HA 重新申请新的 `flow_id`。
- 修复 `access_token` 过期时间更新逻辑，兼容新版本 HA 的内部对象结构。
- 修复小度语音控制阶段携带旧 `access token` 时直接返回 `InvalidAccessTokenError` 的问题。

## 2026-03-22 当前方案说明
- 当前仓库保留的是已经在现网验证可用的“方案2增强版”。
- 正常情况下，HAVCS 会先使用 HA 原生逻辑校验 `access_token`。
- 当小度侧仍然发送旧 `access_token` 且校验失败时，HAVCS 会先尝试从该 token 的 `iss` 找回对应的 `refresh_token`。
- 如果旧 `refresh_token` 已经被删除，且请求来源是 `dueros`，HAVCS 会进一步回退到“当前最新的小度 refresh token”来继续执行控制请求。

## 2026-03-22 风险提示
- 该方案会放宽 DuerOS 控制请求的鉴权严格性，不再完全等同于标准 OAuth 的“仅接受当前有效 access token”。
- 如果旧的小度 `access_token` 曾经泄露，在对应 refresh token 仍存在，或系统中仍有可匹配的小度最新 refresh token 时，攻击面会比严格校验更大。
- 这个兼容逻辑目前只对 `dueros` 生效，没有扩展到天猫精灵、京东小鲸等其它平台，目的是把风险控制在最小范围。
- 更安全的长期方案仍然是让小度平台在重新授权后真正切换到新的 `access_token`，然后删除这里的兼容回退逻辑。


