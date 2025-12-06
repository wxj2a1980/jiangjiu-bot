# -*- coding: utf-8 -*-
import os
import json
import requests
from flask import Flask, request, abort
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.enterprise import parse_message, create_reply

app = Flask(__name__)

# ==========================================
# 🔴 必填配置区 (一定要反复核对！)
# ==========================================

# 1. 企业微信的信息 (去后台复制)
CORP_ID = "wwd466aa54140422a7"  # 你的企业ID
AGENT_ID = "1000002"            # 你的应用ID
CORP_SECRET = "4oZPE0luv8D2nRjv2g-MP_PaN8iiK0ZUayPlLTB-LOc" # 替换真的Secret

# 2. 消息加密信息 (去后台“API接收消息”里复制)
TOKEN = "dSw4GAuALapXQn4FhTajzTqKornmJN8X"           # 替换真的Token
AES_KEY = "XiuEuk1bipzf75LPvmIwuBGx4WvLGYp6T4R2QHlQtJI" # 替换真的AESKey

# 3. 阿里云通义千问 API KEY (关键！)
# 没有Key，AI就是哑巴。申请地址: https://dashscope.console.aliyun.com/apiKey
QWEN_API_KEY = "key:sk-b7f0487ed59749ddacb36f0602f4f6b9" 

# ==========================================

# 初始化加密器
try:
    crypto = WeChatCrypto(TOKEN, AES_KEY, CORP_ID)
except Exception as e:
    print(f"❌ 加密配置错误: {e}")

# 通义千问 AI 逻辑
def qwen_ai(msg):
    print(f"💬 收到提问: {msg}")
    
    # 检查 Key 是否填写
    if "sk-" not in QWEN_API_KEY:
        return "老铁，我的 API Key 还没填，快去代码里把 QWEN_API_KEY 填上！"

    # 阿里云官方接口
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 设定人设
    prompt = f"你是15年酱酒老炮，客户说：{msg}\n推荐：飞天2690、15年坤沙899、赖茅358、王子138\n要求：用酒友聊天语气，50字内回复，不要废话。"
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [{"role": "user", "content": prompt}]
        },
        "parameters": {
            "result_format": "message"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5) # 5秒超时防止微信断连
        r = response.json()
        
        if response.status_code == 200 and "output" in r:
            ai_msg = r["output"]["choices"][0]["message"]["content"]
            print(f"✅ AI回复: {ai_msg}")
            return ai_msg
        else:
            print(f"❌ API 报错: {r}")
            return "老铁，AI 大脑刚才有点卡，你再说一遍？"
            
    except Exception as e:
        print(f"❌ 网络请求挂了: {e}")
        return "老铁，刚才信号不好，没听清你说啥。"

# 微信消息主入口
@app.route('/', methods=['GET', 'POST'])
def wechat():
    signature = request.args.get('msg_signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')

    # 1. 验证回调 (GET)
    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        try:
            return crypto.check_signature(signature, timestamp, nonce, echostr)
        except InvalidSignatureException:
            abort(403)

    # 2. 接收消息 (POST)
    else:
        try:
            # 解密
            decrypted_xml = crypto.decrypt_message(request.data, signature, timestamp, nonce)
            msg = parse_message(decrypted_xml)
            
            reply_content = ""

            # 只有文本消息才回复
            if msg.type == 'text':
                content = msg.content.strip()
                # 关键词拦截
                if "小样" in content or "尝" in content:
                    reply_content = "老铁，把姓名+电话+地址发我，免费寄2支50ml小样，喝完再买！"
                else:
                    # 只有没有关键词时，才调用 AI
                    reply_content = qwen_ai(content)
            
            elif msg.type == 'event' and msg.event == 'subscribe':
                reply_content = "欢迎加入老张酱酒私域！我是玩了15年酱酒的老炮，想喝什么酒？"

            if reply_content:
                # 加密回复
                reply = create_reply(reply_content, msg)
                xml_data = reply.render()
                return crypto.encrypt_message(xml_data, nonce, timestamp)
            else:
                return "success"

        except InvalidSignatureException:
            abort(403)
        except Exception as e:
            print(f"❌ 处理流程异常: {e}")
            return "success"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
