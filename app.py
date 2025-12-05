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
        return requests.get(url).json().get("access_token")
    except:
        return None

def qwen_ai(msg):
    print(f"正在问AI: {msg}") # 打印日志：确认在问什么
    prompt = f"你是15年酱酒老炮，客户说：{msg}\n推荐：飞天2690、15年坤沙899、赖茅358、王子138\n用酒友聊天语气回复："
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # ⚠️ 这里把模型改回 turbo 先测试，因为 plus 有时候免费号不能用
    payload = {
        "model": "qwen-turbo", 
        "input": {"messages": [{"role": "user", "content": prompt}]}
    }
    
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation", 
            headers=headers, 
            json=payload, 
            timeout=10
        )
        
        # === 关键调试代码 ===
        r = response.json()
        if "output" in r and "choices" in r["output"]:
            # 成功拿到回复
            print("✅ AI回复成功")
            return r["output"]["choices"][0]["message"]["content"]
        else:
            # 拿到错误信息，打印出来！
            print(f"❌ 阿里云报错: {json.dumps(r, ensure_ascii=False)}")
            return f"（系统调试）AI连接失败，错误代码：{r.get('code', '未知')}"
            
    except Exception as e:
        print(f"❌ 请求彻底失败: {e}")
        return "老铁，服务器网线被人拔了，稍等会儿哈。"

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
            # ... 上面的代码不变 ...
    
    # 回消息
    send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={get_token()}"
    payload = {
        "touser": FromUserName,
        "msgtype": "text",
        "agentid": AGENT_ID,
        "text": {"content": reply}
    }
    
    # === 修改这里，看看微信那边接收成功没 ===
    res = requests.post(send_url, json=payload).json()
    print(f"📨 发送给微信的结果: {res}")
    
    return "success"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

