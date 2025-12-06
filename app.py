# app.py - 极简测试版
import os
from flask import Flask, request, abort
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.enterprise import parse_message, create_reply

app = Flask(__name__)

# === 只需要改这三个，必须和企业微信后台一模一样 ===
CORP_ID = "wwd466aa54140422a7"
AGENT_ID = "1000002"
CORP_SECRET = "4oZPE0luv8D2nRjv2g-MP_PaN8iiK0ZUayPlLTB-LOc"
TOKEN = "dSw4GAuALapXQn4FhTajzTqKornmJN8X"
AES_KEY = "XiuEuk1bipzf75LPvmIwuBGx4WvLGYp6T4R2QHlQtJI"
QWEN_API_KEY = "key:sk-b7f0487ed59749ddacb36f0602f4f6b9"

crypto = WeChatCrypto(TOKEN, AES_KEY, CORP_ID)

@app.route('/', methods=['GET', 'POST'])
def index():
    signature = request.args.get('msg_signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    echostr = request.args.get('echostr', '')

    # 1. 验证回调 (点击保存时)
    if request.method == 'GET':
        try:
            return crypto.check_signature(signature, timestamp, nonce, echostr)
        except InvalidSignatureException:
            abort(403)

    # 2. 接收消息
    else:
        try:
            decrypted_xml = crypto.decrypt_message(request.data, signature, timestamp, nonce)
            msg = parse_message(decrypted_xml)
            
            # 无论发什么，都回复 "测试成功"
            reply = create_reply("测试成功！连接已打通！", msg)
            xml = reply.render()
            return crypto.encrypt_message(xml, nonce, timestamp)
        except InvalidSignatureException:
            abort(403)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

