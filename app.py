# app.py —— 45岁酱酒老炮专属终极修复版（已加入官方解密库 + 全面修复）
from flask import Flask, request, abort
import requests
import json
from xml.etree import ElementTree as ET

# 引入微信官方解密库（必须要有这个才能通过验证）
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.enterprise import parse_message

app = Flask(__name__)

# === 1. 你的配置（已填好）===
CORP_ID = "wwd466aa54140422a7"
AGENT_ID = "1000002"
CORP_SECRET = "4oZPE0luv8D2nRjv2g-MP_PaN8iiK0ZUayPlLTB-LOc"

# 必须和企业微信后台完全一致（已填入你提供的）
TOKEN = "dSw4GAuALapXQn4FhTajzTqKornmJN8X"
AES_KEY = "XiuEuk1bipzf75LPvmIwuBGx4WvLGYp6T4R2QHlQtJI"

# !!! 这里的 key 需要你自己填一下通义千问的 key，否则AI不回话 !!!
QWEN_API_KEY = "sk-b7f0487ed59749ddacb36f0602f4f6b9"
# =================================

# 初始化“开锁师傅”（解密器）
crypto = WeChatCrypto(TOKEN, AES_KEY, CORP_ID)

def get_token():
    """获取企业微信发送权限"""
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
    print(f"正在问AI: {msg}")  # 打印日志：确认在问什么
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
            "https://dashscope.aliyuncs.com/api/v1/inference",  # ✅ 使用新版 endpoint
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

    # === 处理验证 (GET请求) ===
    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        try:
            decrypted_echo = crypto.check_signature(signature, timestamp, nonce, echostr)
            return decrypted_echo
        except InvalidSignatureException:
            abort(403)

    # === 处理消息 (POST请求) ===
    if request.method == 'POST':
        try:
            # 解密消息
            decrypted_xml = crypto.decrypt_message(
                request.data,
                signature,
                timestamp,
                nonce
            )
            msg = parse_message(decrypted_xml)
            
            reply_content = "收到！"

            # 只处理文本消息
            if msg.type == 'text':
                user_input = msg.content
                if "小样" in user
