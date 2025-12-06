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
# 🔴 配置区 (部署前一定要检查这几个填对了没)
# ==========================================
CORP_ID = "wwd466aa54140422a7"
AGENT_ID = "1000002"
CORP_SECRET = "4oZPE0luv8D2nRjv2g-MP_PaN8iiK0ZUayPlLTB-LOc" # 替换真的
TOKEN = "dSw4GAuALapXQn4FhTajzTqKornmJN8X"           # 替换真的
AES_KEY = "XiuEuk1bipzf75LPvmIwuBGx4WvLGYp6T4R2QHlQtJI" # 替换真的

# 🔴 必须填写真实的阿里云 Key，否则 AI 不会回话
# 申请地址: https://dashscope.console.aliyun.com/apiKey
QWEN_API_KEY = "sk-b7f0487ed59749ddacb36f0602f4f6b9" 

# ==========================================

# 初始化加密器
try:
    crypto = WeChatCrypto(TOKEN, AES_KEY, CORP_ID)
except Exception as e:
    print(f"❌ 加密配置错误，请检查 EncodingAESKey 是否是43位: {e}")

# 通义千问 AI (修复版)
def qwen_ai(msg):
    print(f"💬 收到提问: {msg}")
    
    # 1. 检查 Key 是否填写
    if "sk-" not in QWEN_API_KEY:
        return "老铁，我的 API Key 还没填，让老板去阿里云申请一个吧！"

    # 2. 准备请求数据 (这是阿里云官方标准格式)
    url = "https://dashscope.aliyuncs.com/api/v1/inference"
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"你是15年酱酒老炮，客户说：{msg}\n推荐：飞天2690、15年坤沙899、赖茅358、王子138\n要求：用酒友聊天语气，50字内回复，不要废话。"
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [{"role": "user", "content": prompt}]
        },
        "parameters": {
            "result_format": "message"  # 关键：加上这个参数，返回格式才对
        }
    }

    # 3. 发送请求
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        r = response.json()
        
        # 4. 解析结果 (兼容性处理)
        if response.status_code == 200 and "output" in r:
            # 成功拿到回复
            ai_msg = r["output"]["choices"][0]["message"]["content"]
            print(f"✅ AI回复: {ai_msg}")
            return ai_msg
        else:
            # 阿里云报错
            print(f"❌ API 报错: {r}")
            err_msg = r.get('message', '未知错误')
            return f"哥们，AI大脑短路了({err_msg})，待会再聊。"
            
    except Exception as e:
        print(f"❌ 网络请求挂了: {e}")
        return "老铁，刚才信号不好，没听清你说啥。"

# 微信消息处理
@app.route('/', methods=['GET', 'POST'])
def wechat():
    # 获取 URL 参数
    signature = request.args.get('msg_signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')

    # --- 1. 验证 (GET) ---
    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        try:
            return crypto.check_signature(signature, timestamp, nonce, echostr)
        except InvalidSignatureException:
            abort(403)

    # --- 2. 接收消息 (POST) ---
    else:
        try:
            # A. 解密 XML
            decrypted_xml = crypto.decrypt_message(
                request.data,
                signature,
                timestamp,
                nonce
            )
            
            # B. 解析消息对象
            msg = parse_message(decrypted_xml)
            
            reply_content = "收到" # 默认回复

            # C. 业务逻辑
            if msg.type == 'text':
                content = msg.content.strip()
                if "小样" in content or "尝" in content:
                    reply_content = "老铁，把姓名+电话+地址发我，免费寄2支50ml小样，喝完再买！"
                else:
                    reply_content = qwen_ai(content)
            
            elif msg.type == 'event' and msg.event == 'subscribe':
                reply_content = "欢迎加入老张酱酒私域！我是玩了15年酱酒的老炮，想喝什么酒？直接跟我说！"

            # D. 加密回复 (使用 create_reply 自动生成 XML，防止手动拼接出错)
            reply = create_reply(reply_content, msg)
            xml_data = reply.render()
            encrypted_response = crypto.encrypt_message(xml_data, nonce, timestamp)
            
            return encrypted_response

        except InvalidSignatureException:
            abort(403)
        except Exception as e:
            print(f"❌ 处理流程异常: {e}")
            return "success" # 出错也返回 success 避免微信重试

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
