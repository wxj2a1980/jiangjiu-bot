# app.py —— 45岁酱酒老炮专属终极修复版（已加入官方解密库）
from flask import Flask, request, abort
import requests
import json
# 引入微信官方解密库（必须要有这个才能通过验证）
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.enterprise import parse_message

app = Flask(__name__)

# === 1. 你的配置（已填好）===
CORP_ID = "wwd466aa54140422a7"
AGENT_ID = "1000002"
CORP_SECRET = "4oZPE0luv8D2nRjv2g-MP_HFIW8GfkPyaJLiM2W7-us"

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
        return requests.get(url).json().get("access_token")
    except:
        return None

def qwen_ai(msg):
    """通义千问AI逻辑"""
    prompt = f"你是15年酱酒老炮，客户说：{msg}\n推荐：飞天2690、15年坤沙899、赖茅358、王子138\n用酒友聊天语气回复："
    
    # ⚠️ 注意：你原来的代码少了这个 headers 鉴权，AI是不会理你的
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-plus",
        "input": {"messages": [{"role": "user", "content": prompt}]}
    }
    
    try:
        # 这里加了 headers
        r = requests.post("https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation", headers=headers, json=payload, timeout=10).json()
        if "output" in r:
            return r["output"]["choices"][0]["message"]["content"]
        else:
            print(f"AI报错: {r}") # 在日志里看错误
            return "老铁，刚才信号闪了一下，你刚说啥来着？"
    except Exception as e:
        print(f"请求错误: {e}")
        return "老铁，我这会儿在酒库忙，稍后回你哈！"

@app.route('/', methods=['GET', 'POST'])
def weixin():
    # 1. 拿到微信传过来的加密参数
    signature = request.args.get('msg_signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')

    # === 处理验证 (GET请求) ===
    # 这里就是你之前报错的地方，现在用 crypto.check_signature 自动解密
    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        try:
            decrypted_echo = crypto.check_signature(signature, timestamp, nonce, echostr)
            return decrypted_echo # 返回解密后的明文，微信才会通过！
        except InvalidSignatureException:
            abort(403)

    # === 处理消息 (POST请求) ===
    if request.method == 'POST':
        try:
            # 2. 解密客户发来的消息（不开锁读不到内容）
            decrypted_xml = crypto.decrypt_message(
                request.data,
                signature,
                timestamp,
                nonce
            )
        except InvalidSignatureException:
            abort(403)

        # 3. 解析消息
        msg = parse_message(decrypted_xml)
        
        # 只回复文本消息
        if msg.type == 'text':
            user_input = msg.content
            user_id = msg.source # 客户ID
            
            # 4. 你的业务逻辑
            if "小样" in user_input or "尝" in user_input:
                reply_content = "老铁，把姓名+电话+地址发我，免费寄2支50ml小样，喝完再买！"
            else:
                reply_content = qwen_ai(user_input)

            # 5. 主动把回复发给客户
            send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={get_token()}"
            payload = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": AGENT_ID,
                "text": {"content": reply_content}
            }
            requests.post(send_url, json=payload)
        
        return "success"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
