# Listing 修改案例包

本案例包用于第 5 章和第 6 章，展示 Listing 从 v1 到 v2 的修改过程。

## 1. 业务背景

产品是一款露营灯。AI 根据产品资料生成了一版 Listing 初稿，但里面有夸大表达和待确认信息。

## 2. 产品事实

| 项目 | 事实 |
| --- | --- |
| 续航 | 最长约 8 小时 |
| 防水 | IPX4 防泼水 |
| 使用场景 | 露营、庭院、停电备用 |
| 重量 | 约 320g |

## 3. AI 初稿 v1

```text
This ultimate camping lantern offers ultra-long battery life for all weather conditions. It is a must-have outdoor light for every adventure and keeps your campsite bright all night.
```

## 4. 问题标注

| 原文 | 问题类型 | 问题 |
| --- | --- | --- |
| ultimate | 规则审 | 绝对化表达 |
| ultra-long battery life | 事实审 | 没有写真实小时数 |
| all weather conditions | 事实审 / 规则审 | IPX4 不能支持所有天气 |
| must-have | 品牌审 | 语气夸张 |
| all night | 事实审 | 可能超过 8 小时事实 |

## 5. 人工修改后 v2

```text
Designed for camping, patio use, and power outage backup, this lantern provides up to about 8 hours of light in everyday outdoor settings. The IPX4 splash-resistant design helps handle light splashes, while the compact 320g body is easy to carry and hang.
```

## 6. 修改理由

- 把 “ultra-long” 改成 “up to about 8 hours”，回到真实参数。
- 把 “all weather conditions” 改成 “light splashes”，避免超出 IPX4。
- 删除 “ultimate” 和 “must-have”，语气更克制。

## 7. 课堂讨论点

- 哪个修改是事实审？
- 哪个修改是规则审？
- 哪个修改让用户更容易理解？

