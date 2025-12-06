# -*- coding: utf-8 -*-
import os
import json
import requests
from flask import Flask, request, abort
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.enterprise import parse_message, create_reply

app = Flask(__name__)

# ========= 配置信息 =========
CORP_ID = "wwd466aa54140422a7"
AGENT_ID = "1000002"
CORP_SECRET = "4oZPE0luv8D2nRjv2g-MP_PaN8iiK0ZUayPlLTB-LOc"
TOKEN = "dSw4GAuALapXQn4FhTajzTqKornmJN8X"
EncodingAESKey = "XiuEuk1bipzf75LPvmIwuBGx4WvLGYp6T4R2QHlQtJI"

# !!! 这里的 Key 必须填 !!! 
# 通义千问虽然有免费额度，但必须申请 API KEY 才能调通，否则报错
# 申请地址：https://dashscope.console.aliyun.com/apiKey
DASHSCOPE_API_KEY = "key:sk-b7f0487ed59749ddacb36f0602f4f6b9" 

# 库存与配置
WINES = "飞天茅台2690、15年坤沙899、赖茅传承358、王子酒138"
QWEN_URL = "https://dashscope.aliyuncs.com/api/v1/inference"

# 初始化微信加解密工具
crypto = WeChatCrypto(TOKEN, EncodingAESKey, CORP_ID)

# 缓存 Token (简单实现)
_access_token = None

def get_token():
    global _access_token
    # 实际生产环境建议检查过期时间，这里简化处理，每次都取最新的也没关系（量不大时）
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORP_ID}&corpsecret={CORP_SECRET}"
    try:
        r = requests.get(url).json()
        if "access_token" in r:
            _access_token = r["access_token"]
            return _access_token
        else:
            print(f"获取Token失败: {r}")
            return None
    except Exception as e:
        print(f"网络错误: {e}")
        return None

def qwen_ai(msg):
    if "sk-xxxx" in DASHSCOPE_API_KEY:
        return "老铁，我的AI大脑还没插卡（API Key没填），先聊点别的？"
        
    prompt = f"你是15年贵州酱酒老炮，客户说：{msg}\n推荐酒：{WINES}\n用酒友聊天语气，50字内回复："
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-plus",
        "input": {"messages": [{"role": "user", "content": prompt}]}
    }
    try:
        resp = requests.post(QWEN_URL, headers=headers, json=payload, timeout=10)
        r = resp.json()
        if resp.status_code == 200 and "output" in r:
            return r["output"]["choices"][0]["message"]["content"]
        else:
            print(f"AI报错: {r}")
            return "老铁，刚才信号有点差，我马上再跟你细聊哈~"
    except Exception as e:
        print(f"AI请求异常: {e}")
        return "老铁，刚才信号有点差，我马上再跟你细聊哈~"

def send_custom_msg(to_user, content):
    token = get_token()
    if not token: return
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    data = {
        "touser": to_user,
        "msgtype": "text",
        "agentid": AGENT_ID,
        "text": {"content": content}
    }
    requests.post(url, json=data)

@app.route('/', methods=['GET', 'POST'])
def index():
    # 1. 获取URL参数
    signature = request.args.get('msg_signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')

    # 2. 验证回调 URL (GET 请求)
    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        try:
            echostr = crypto.check_signature(signature, timestamp, nonce, echostr)
            return echostr
        except InvalidSignatureException:
            abort(403)

    # 3. 处理消息 (POST 请求)
    else:
        try:
            # 解密接收到的 XML
            xml_data = request.data
            decrypted_xml = crypto.decrypt_message(xml_data, signature, timestamp, nonce)
            msg = parse_message(decrypted_xml)
            
            reply_content = ""

            # 处理具体逻辑
            if msg.type == 'event' and msg.event == 'subscribe':
                reply_content = """欢迎来到老张酱酒私域！
我是张哥，玩了15年酱酒，货真价实！
你是自己喝、送礼还是收藏？我给你推荐最合适的～"""
            
            elif msg.type == 'text':
                content = msg.content
                if "小样" in content or "尝" in content:
                    reply_content = "老铁，想尝尝底子是吧？把收件人+电话+地址发我，免费寄2支50ml小样，喝完再决定买不买！"
                else:
                    reply_content = qwen_ai(content)

            # 企业微信要求必须返回加密后的 XML，或者直接空串（然后异步发消息）
            # 为了简单，这里我们直接返回加密后的被动响应
            if reply_content:
                reply = create_reply(reply_content, msg)
                xml_response = reply.render()
                encrypted_response = crypto.encrypt_message(xml_response, nonce, timestamp)
                return encrypted_response
            else:
                return "success"

        except (InvalidSignatureException, Exception) as e:
            print(f"处理消息错误: {e}")
            abort(403)

if __name__ == '__main__':
    # 修正：必须监听 0.0.0.0 且读取环境变量 PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

