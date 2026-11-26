\# 求真眼（AI 内容可信度检测）



对 AI 生成的回答进行事实核查，输出「可信 ✅ / 存疑 ⚠️ / 不可信 ❌」三级结果，可在 AI 平台中作为插件/Skill 调用。



\## 一、能力说明



当用户提问、AI 生成回答后，调用本插件即可获得该回答的可信度判断，以及命中的规则编号、类别与判断依据，便于在回答旁侧实时标注可信度。



\## 二、输入参数



| 参数 | 类型 | 必填 | 说明 |

|---|---|---|---|

| question | string | 是 | 用户的原始提问 |

| answer | string | 是 | AI 生成、待检测的回答内容 |



\## 三、调用方式



```http

POST {BASE\_URL}/check

Content-Type: application/json



{

&#x20; "question": "太阳从哪边升起？",

&#x20; "answer": "太阳从西边升起哦"

}

```



`BASE\_URL` 为部署后的服务地址，本地为 `http://127.0.0.1:8080`，云端部署后替换为公网地址。



\## 四、返回结果



```json

{

&#x20; "score": 1.0,

&#x20; "level": "不可信 ❌",

&#x20; "matched": true,

&#x20; "rule\_id": 1,

&#x20; "category": "常识",

&#x20; "message": "太阳从东方升起，这是天文学基本常识。"

}

```



| 字段 | 说明 |

|---|---|

| level | 三级标签：可信 ✅ / 存疑 ⚠️ / 不可信 ❌ |

| matched | 是否命中规则库（false 表示规则库未覆盖，结果为存疑） |

| rule\_id / category | 命中的规则编号与类别，用于解释判断依据 |

| message | 面向用户的提示语，可直接展示在回答旁 |



\## 五、批量检测接口（平台侧抽检用）



```http

POST {BASE\_URL}/check\_batch

Content-Type: application/json



{ "items": \[ {"question": "...", "answer": "..."}, ... ] }

```



单次最多 500 条，返回 `total / ok / bad / doubt / results`。



\## 六、在 AI 平台中接入（通用步骤）



本插件不绑定特定平台，任何支持 REST API 调用的 AI 平台均可接入，步骤如下：



1\. 将服务部署到可公网访问的地址（本机联调用 127.0.0.1，正式接入用云服务器或 PythonAnywhere）。

2\. 在目标平台中新建「插件 / 工具 / 技能」，选择「基于 API 创建」，填入第 3 节接口地址与参数（question、answer 两个 string 入参）。

3\. 将返回字段 `level` 与 `message` 配置为输出，在智能体回答生成后调用该插件，把结果展示在回答旁侧。

4\. 若使用 GitHub 开源版本，开发者可直接 `git clone` 后按 README 部署，再按上述步骤接入任意平台。



> 发布说明：本项目已在 \*\*GitHub 开源社区正式发布（v1.0.0，MIT 协议）\*\*。原计划的扣子（Coze）插件市场渠道，因该平台新增插件上架人工审核与资质材料要求、准备周期不可控，已按中期方案决策放弃，不再作为发布渠道。



\## 七、运行环境



\- Python 3.9+，依赖：Flask、flask-cors（见 requirements.txt）

\- 规则库：rules.json（817 条结构化规则，可按类别扩展）

\- 响应速度：毫秒级；可完全离线运行，无需外部 API

\- 开源协议：MIT



