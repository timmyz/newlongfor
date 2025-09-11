import requests
import random
import json

BASE_URL = "https://gw2c-hw-open.longfor.com"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]

def _fetch(url: str, headers: dict, method: str = 'POST', data: dict = None, timeout: int = 10) -> dict:
    """通用 HTTP 请求"""
    try:
        if method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        else:
            response = requests.get(url, headers=headers, params=data, timeout=timeout)
        
        response.raise_for_status()
        res = response.json()
        
        if 'message' in res and ('登录已过期' in res['message'] or '用户未登录' in res['message']):
            raise Exception("Token/Cookie已过期")
        
        return res
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Token/Cookie已过期 (401)")
        raise Exception(f"HTTP错误: {e.response.status_code}")
    except Exception as e:
        raise e

def execute_signin(user_auth_data: dict) -> str:
    """为单个用户执行签到任务"""
    try:
        url = f"{BASE_URL}/lmarketing-task-api-mvc-prod/openapi/task/v1/signature/clock"
        headers = {
            'Host': 'gw2c-hw-open.longfor.com',
            'Accept': 'application/json, text/plain, */*',
            'X-LF-DXRISK-SOURCE': user_auth_data.get('x-lf-dxrisk-source', '2'),
            'X-LF-BU-CODE': user_auth_data.get('x-lf-bu-code', 'L00602'),
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-LF-CHANNEL': user_auth_data.get('x-lf-channel', 'L0'),
            'Content-Type': 'application/json;charset=utf-8',
            'Origin': 'https://longzhu.longfor.com',
            'X-LF-USERTOKEN': user_auth_data.get('token'),
            'token': user_auth_data.get('token'),
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': 'https://longzhu.longfor.com/',
            'X-GAIA-API-KEY': 'c06753f1-3e68-437d-b592-b94656ea5517',
            'Cookie': user_auth_data.get('cookie'),
            'X-LF-DXRISK-TOKEN': user_auth_data.get('x-lf-dxrisk-token'),
            'X-LF-DXRisk-Captcha-Token': 'undefined'
        }
        data = {"activity_no": "11111111111736501868255956070000"}
        res = _fetch(url, headers, 'POST', data)
        
        if res and res.get('code') == '0000':
            res_data = res.get('data', {})
            if res_data.get('is_popup') == 1:
                reward_info_list = res_data.get('reward_info', [])
                total_reward = sum(item.get('reward_num', 0) for item in reward_info_list)
                return f"签到成功, 获得总积分: {total_reward}"
            elif res_data.get('is_popup') == 0:
                return "今日已签到"
            else:
                return f"请求成功但状态未知: {res.get('message')}"
        else:
            message = res.get('message', '未知错误') if res else '请求失败'
            return f"签到失败: {message}"

    except Exception as e:
        return f"签到异常: {e}"
