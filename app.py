# app.py —— 45岁酱酒老炮专属终极修复版（适配 Railway 部署）
from flask import Flask, request, abort
import requests
import json
from xml.etree import ElementTree as ET
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.enterprise import parse_message
import os

app = Flask(__name__)

# === 配置（请确保环境变量也设置了敏感信息更安全）===
CORP_ID = "wwd466aa54140422a7"
AGENT_ID = "1000002"
CORP_SECRET = "4oZPE0luv8D2nRjv2g-MP_PaN8iiK0ZUayPlLTB-LOc"

TOKEN = "dSw4GAuALapXQn4FhTajzTqKornmJN8X"
AES_KEY = "XiuEuk1bipzf75LPvmIwuBGx4WvLGYp6T4R2QHlQtJI"

QWEN_API_KEY = "sk-b7f0487ed59749ddacb36f0602f4f6b9"

# 初始化解密器
crypto = WeChatCrypto(TOKEN, AES_KEY, CORP_ID)

def get_token():
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORP_ID}&corpsecret={CORP_SECRET}"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get("errcode") == 0:
            return data.get("access_token")
        else:
            print(f"❌ 获取 token 失败: {data}")
            return None
    except Exception as e:
        print(f"❌ 获取 token 异常: {e}")
        return None

def qwen_ai(msg):
    print(f"正在问AI: {msg}")
    prompt = f"你是15年酱酒老炮，客户说：{msg}\n推荐：飞天2690、15年坤沙899、赖茅358、王子138\n用酒友聊天语气回复："
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [{"role": "user", "content": prompt}]
        }
    }
    
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/inference",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        r = response.json()
        if r.get("code") == 200 and "output" in r:
            content = r["output"]["choices"][0]["message"]["content"]
            print("✅ AI回复成功")
            return content.strip()
        else:
            errmsg = r.get("message", "未知错误")
            print(f"❌ DashScope 报错: {json.dumps(r, ensure_ascii=False)}")
            return f"（AI故障）{errmsg}"

    except Exception as e:
        print(f"❌ 请求彻底失败: {e}")
        return "老铁，服务器网线被人拔了，稍等会儿哈。"

@app.route('/', methods=['GET', 'POST'])
def weixin():
    signature = request.args.get('msg_signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')

    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        try:
            decrypted_echo = crypto.check_signature(signature, timestamp, nonce, echostr)
            return decrypted_echo
        except InvalidSignatureException:
            abort(403)

    if request.method == 'POST':
        try:
            decrypted_xml = crypto.decrypt_message(
                request.data,
                signature,
                timestamp,
                nonce
            )
            msg = parse_message(decrypted_xml)

            if msg.type == 'text':
                user_input = msg.content
                if "小样" in user_input or "尝" in user_input:
                    reply_content = "老铁，把姓名+电话+地址发我，免费寄2支50ml小样，喝完再买！"
                else:
                    reply_content = qwen_ai(user_input)

                reply_xml = f"""
<xml>
    <ToUserName><![CDATA[{msg.source}]]></ToUserName>
    <FromUserName><![CDATA[{CORP_ID}]]></FromUserName>
    <CreateTime>{int(__import__('time').time())}</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[{reply_content}]]></Content>
</xml>"""
                
                encrypted_reply = crypto.encrypt_message(reply_xml, nonce, timestamp)
                return encrypted_reply

            return "success"

        except InvalidSignatureException:
            abort(403)
        except Exception as e:
            print(f"❌ 消息处理异常: {e}")
            return "success"

if __name__ == '__main__':
    # ✅ 关键修复：使用环境变量 PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False 更稳定
