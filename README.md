# 龙湖天街自动化任务脚本

这是一个用于龙湖天街（Longfor）会员系统的自动化任务脚本，支持多账号管理和互助助力功能。

## 项目功能

### 基础任务
- ✅ 每日签到获取积分
- ✅ 抽奖签到获取抽奖机会
- ✅ 自动抽奖
- ✅ 查询用户成长值和等级
- ✅ 查询珑珠余额

### 助力任务
- ✅ 动态获取当前有效的助力任务
- ✅ 主账号发起助力任务
- ✅ 从账号参与助力
- ✅ 周级别的助力记录管理
- ✅ 防止重复助力

### 通知功能
- ✅ 钉钉机器人消息推送
- ✅ 任务执行结果汇总通知

## 项目结构

```
longfor/
├── main.py          # 主程序文件
├── lhtj_data.json   # 账户配置文件
├── assist_status.json  # 助力状态记录文件（自动生成）
└── README.md        # 项目说明文档
```

## 配置文件说明

### lhtj_data.json 结构

```json
{
  "accounts": [
    {
      "account_id": "手机号",
      "userName": "账号名称",
      "x-lf-dxrisk-token": "安全令牌",
      "x-lf-channel": "C2",
      "token": "用户令牌",
      "x-lf-usertoken": "用户令牌",
      "cookie": "会话Cookie",
      "x-lf-bu-code": "C20400",
      "x-lf-dxrisk-source": "5"
    }
  ],
  "assist_groups": [
    {
      "group_name": "组名",
      "master": "主账号ID",
      "followers": ["从账号ID1", "从账号ID2"]
    }
  ]
}
```

## 安装依赖

```bash
pip install requests dingtalkchatbot
```

## 使用方法

### 1. 配置账户信息
编辑 `lhtj_data.json` 文件，添加你的账户信息和助力组配置。

### 2. 运行脚本

```bash
# 执行所有任务（签到 + 助力）
python main.py

# 只执行基础任务（签到、抽奖等）
python main.py --basic-only

# 只执行助力任务
python main.py --assist-only
```

### 3. 配置钉钉通知（可选）
在 `main.py` 中的 `send_notification` 函数配置你的钉钉机器人 webhook 和 secret。

## 功能特点

- **多账号管理**: 支持多个账号同时运行
- **智能助力**: 自动检测有效的助力任务，避免重复助力
- **随机延迟**: 模拟真人操作，避免被检测为机器人
- **状态持久化**: 记录助力状态，支持断点续做
- **详细日志**: 完整的执行日志和错误处理
- **灵活配置**: 支持只执行特定类型的任务

## 注意事项

1. 确保账户信息的准确性和有效性
2. 助力任务基于周级别记录，每周可助力一次
3. 脚本会生成 `assist_status.json` 文件记录助力状态
4. 建议定期检查账户令牌和Cookie的有效性
5. 使用前请确认龙湖天街的相关规则和政策

## 技术支持

如有问题或需要帮助，请检查日志输出或联系开发者。