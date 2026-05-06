# 客服 FAQ 与标准回复库

> 本模板用在第 11 章《AI 辅助客服和售后回复》。目标是把"每次都临时想怎么回"变成"查一下回复模板 + 轻度个性化"。
>
> 客服场景 AI 的最大风险不是写不出来，而是**语气太像机器、或越权承诺**。模板的价值在于**兜底的语气 + 边界清单**。

---

## 一、使用流程（4 步）

1. 从后台导出最近 30 天的客服对话，分类统计最高频的 15–20 个问题。
2. 按"问题类型 × 语气场景"填入下方 FAQ 表（见第三节示例）。
3. 让 AI 生成初稿后，人工对照**回复原则**与**敏感红线**（第五节）做二次审核。
4. 客服实际使用时，只做"替换姓名 / 订单号 / 产品型号"级别的个性化，**不要**让 AI 每次从零生成。

---

## 二、回复原则（所有回复都要遵守）

1. **先情绪，后事实**：第一句回应用户感受（抱歉 / 理解 / 感谢），再说事实。
2. **说事实不说借口**：是我们的问题就认，不把原因推给物流、系统、工厂。
3. **给下一步**：每一条回复都要让用户知道接下来 TA 要做什么、我们会做什么、什么时候回。
4. **不做超出政策的承诺**：退款金额、时效、赠品这些不能由客服临时加码。
5. **敏感问题必须转人工**：健康伤害、法律纠纷、媒体投诉、群体索赔，一律转人工并通知主管。

---

## 三、填好的示例：宠物自动喂食器 PetEase

| 问题类型 | 用户常问问题 | 标准回复（英文） | 语气 | 人工介入触发条件 |
| --- | --- | --- | --- | --- |
| 售前 | Does it work with wet food? | Thanks for checking with us! PetEase is designed for dry kibble between 2–15mm. Wet or semi-wet food can clog the feeder and isn't covered by warranty. If your cat prefers wet food, we'd recommend our companion product PetEase Fresh. | 温和、解释性 | 客户追问 "are you sure"、要求书面保证 → 转人工 |
| 售前 | Can I schedule multiple meals per day? | Yes — up to 6 meals per day via the PetEase app (iOS 14+ / Android 9+). Each meal can be 1–30 portions. Happy to share a quick setup video if helpful! | 轻快、积极 | — |
| 物流 | My order hasn't shipped yet. | I understand waiting can be stressful — apologies for the delay. I checked order #\_\_\_ and it's currently at the fulfillment center, expected to ship within 24–48 hours. I'll send you the tracking number the moment it moves. | 共情、负责 | 超 72 小时未发 / 用户提到 "cancel" → 转人工 |
| 物流 | Package shows delivered but I didn't receive it. | I'm sorry about this — that's frustrating. Could you please (1) check with neighbors / leasing office, (2) wait 24 hours (carriers sometimes mark early), and (3) send me a photo of your delivery area? Once confirmed lost, we'll file a claim and ship a replacement. | 共情、流程化 | 第二次未到 / 金额 > $150 → 转人工 |
| 退换货 | The feeder is jamming. | I'm really sorry the feeder isn't working well. Two things would help us fix this fast: (1) a short video of the jam, (2) the kibble brand + size you're using. We'll either walk you through a fix or send a replacement right away, depending on what we see. | 共情、诊断式 | 用户提到 "pet got hurt" / "pet didn't eat" → **立即**转人工 + 主管 |
| 差评安抚 | Left a 2-star review about smell. | Thank you for taking the time to share this — a strong smell is not what we want anyone to experience. We've passed your feedback to our product team. If you'd like, I can send a return label or a replacement; whichever is easier for you. No pressure to update the review. | 真诚、不索求 | 用户主动同意改评论 → 按流程留档，**不**主动请求改评 |
| 使用说明 | App can't find the device. | Let's get this fixed. Please try: (1) hold the pair button 5 seconds until the light flashes blue, (2) make sure your phone is on 2.4GHz WiFi (not 5GHz), (3) keep the phone within 10 ft during setup. If it still fails, please share a screenshot of the app error and we'll continue. | 指引、步骤化 | 3 步仍失败 → 转技术客服 |

---

## 四、空白模板（学员复制使用）

| 问题类型 | 用户常问问题 | 标准回复 | 语气 | 人工介入触发条件 |
| --- | --- | --- | --- | --- |
| 售前 |  |  |  |  |
| 售前 |  |  |  |  |
| 物流 |  |  |  |  |
| 物流 |  |  |  |  |
| 退换货 |  |  |  |  |
| 退换货 |  |  |  |  |
| 差评安抚 |  |  |  |  |
| 使用说明 |  |  |  |  |
| 使用说明 |  |  |  |  |

---

## 五、敏感红线（AI 回复必须回避 / 必须转人工）

### 5.1 AI 禁止主动承诺的事

- "We guarantee full refund + gift + expedited shipping"（多重补偿）
- "No need to return the product"（免退货）
- "This will 100% fix it"（绝对化效果）
- 涉及医疗、健康伤害的**任何**确认性回复（"don't worry, it's safe"）

### 5.2 必须立即转人工的关键词

| 类别 | 示例关键词 |
| --- | --- |
| 健康伤害 | hurt / injury / allergic / burned / shocked / bled / pet got sick |
| 法律 | lawsuit / lawyer / sue / FDA / FTC / attorney general |
| 媒体 | news / reporter / tiktok video / viral |
| 群体 | class action / group of us / subreddit |
| 数据 | account hacked / unauthorized charge / chargeback |

建议做成一份独立的 `05a_客服敏感词表.md` 并和后台客服系统的自动转人工规则对齐。

---

## 六、验收标准

一份合格的客服 FAQ 库应满足：

- [ ] 覆盖 7 大类（售前 / 物流 / 退换货 / 差评安抚 / 使用说明 / 账单 / 配件与周边）至少各 2 条。
- [ ] 每条回复包含"情绪回应 + 事实说明 + 下一步 + 签名语"4 段。
- [ ] 每条都有"人工介入触发条件"列，不能为空。
- [ ] 敏感红线单独列出，并和后台自动转人工规则对齐。
- [ ] 每季度复盘一次，更新 30 天内新出现的问题。

---

## 七、常见错误

1. **AI 语气过于热情**："We are SUPER excited to help!!" 用户刚生气，会被激怒。
2. **把退货理由写得太复杂**——让用户读完 5 段话才知道要发什么，体验差。
3. **泛用回复**——所有类目套同一段"thank you for reaching out"，用户一眼看穿是模板。
4. **把"我们会核实"当挡箭牌**——不给时效，用户会反复追问。承诺"24 小时内回"比"ASAP"强十倍。
5. **漏掉"人工介入触发条件"**——AI 模板里没写"遇到 X 就转人工"，一线客服就照抄，出事故。

---

## 八、关联章节与资源

- 源章节：[`02_第2周_AI岗位实战周/Day11_第11章_AI辅助客服和售后回复.md`](../02_第2周_AI岗位实战周/Day11_第11章_AI辅助客服和售后回复.md)
- 实操手册：[`09_章节实操手册/Day11_第11章：AI辅助客服和售后回复_实操手册.md`](../09_章节实操手册/Day11_第11章：AI辅助客服和售后回复_实操手册.md)
- 配套提示词：[`05_提示词库/07_客服回复提示词.md`](../05_提示词库/07_客服回复提示词.md)
- AI 使用边界：[`01_AI使用边界清单.md`](./01_AI使用边界清单.md)
