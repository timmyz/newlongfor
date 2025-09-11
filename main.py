# -*- coding: utf-8 -*-
import json
import requests
import logging
import random
import asyncio
import time
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 常量
BASE_URL = "https://gw2c-hw-open.longfor.com"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2540615) XWEB/16041"
]

# 通知消息
notify_msg: List[str] = []

def double_log(msg: str):
    """同时记录日志和通知消息"""
    logger.info(msg)
    notify_msg.append(msg)

async def fetch(url: str, headers: Dict, method: str = 'POST', data: Optional[Dict] = None, timeout: int = 10) -> Dict:
    """通用 HTTP 请求"""
    try:
        headers = {k.lower(): v for k, v in headers.items()}  # 统一小写键名
        if method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        else:
            response = requests.get(url, headers=headers, params=data, timeout=timeout)
        
        response.raise_for_status()
        res = response.json()
        
        if 'message' in res and '登录已过期' in res['message'] or '用户未登录' in res['message']:
            raise Exception("用户需要去登录")
        
        return res
    except Exception as e:
        logger.error(f"请求失败: {e}")
        return {}

async def signin(user: Dict) -> int:
    """每日签到"""
    res: Optional[Dict] = None
    try:
        url = f"{BASE_URL}/lmarketing-task-api-mvc-prod/openapi/task/v1/signature/clock"
        headers = {
            'Host': 'gw2c-hw-open.longfor.com',
            'Accept': 'application/json, text/plain, */*',
            'X-LF-DXRISK-SOURCE': user.get('x-lf-dxrisk-source', '2'),
            'X-LF-BU-CODE': user.get('x-lf-bu-code', 'L00602'),
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-LF-CHANNEL': user.get('x-lf-channel', 'L0'),
            'Content-Type': 'application/json;charset=utf-8',
            'Origin': 'https://longzhu.longfor.com',
            'X-LF-USERTOKEN': user.get('token'),
            'token': user.get('token'),
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': 'https://longzhu.longfor.com/',
            'X-GAIA-API-KEY': 'c06753f1-3e68-437d-b592-b94656ea5517',
            'Cookie': user.get('cookie'),
            'X-LF-DXRISK-TOKEN': user.get('x-lf-dxrisk-token'),
            'X-LF-DXRisk-Captcha-Token': 'undefined'
        }
        data = {"activity_no": "11111111111736501868255956070000"}
        res = await fetch(url, headers, 'POST', data)
        
        if res and res.get('code') == '0000':
            data = res.get('data', {})
            if data.get('is_popup') == 1:
                reward_info_list = data.get('reward_info', [])
                total_reward = sum(item.get('reward_num', 0) for item in reward_info_list)
                double_log(f"✅ 每日签到: 成功, 获得总积分: {total_reward}")
                return total_reward
            elif data.get('is_popup') == 0:
                double_log("✅ 每日签到: 今日已签到")
                return 0
            else:
                # is_popup 值不符合预期，但 code 仍为 '0000'
                double_log(f"🤔 每日签到: 请求成功但状态未知，服务器响应：{json.dumps(res, ensure_ascii=False)}")
                return 0
        else:
            message = res.get('message', '未知错误') if res else '请求失败, 未收到响应'
            double_log(f"⛔️ 每日签到: {message}，服务器响应：{json.dumps(res, ensure_ascii=False)}")
            return 0

    except Exception as e:
        response_info = f"服务器响应：{json.dumps(res, ensure_ascii=False)}" if res else "无服务器响应"
        double_log(f"⛔️ 每日签到失败: {e}，{response_info}")
        return 0



async def main():
    """
    主函数，读取配置文件并执行所有账户的签到任务。
    """
    try:
        with open('app_signin_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            app_accounts = data.get('app_accounts', [])

        if not app_accounts:
            logger.info("在 app_signin_data.json 中未找到有效的账户信息。")
            return

        for index, account in enumerate(app_accounts):
            global notify_msg
            notify_msg = []
            
            user_name = account.get('userName', f'未知用户{index+1}')
            logger.info(f"====== 开始为用户【{user_name}】执行任务 ======")
            
            delay = random.randint(30, 60)
            logger.info(f"随机等待 {delay} 秒...")
            await asyncio.sleep(delay)

            await signin(account)
            
            # 打印当前用户的通知消息
            print(f"\n--- 用户【{user_name}】任务结果 ---")
            for msg in notify_msg:
                print(msg)
            print(f"====== 用户【{user_name}】任务结束 ======\n")


    except FileNotFoundError:
        logger.error("错误：未找到 app_signin_data.json 文件。请确保该文件与脚本在同一目录下。")
    except json.JSONDecodeError:
        logger.error("错误：app_signin_data.json 文件格式不正确。")
    except Exception as e:
        logger.error(f"发生未知错误: {e}")


if __name__ == '__main__':
    asyncio.run(main())
