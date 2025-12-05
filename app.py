# app.py  —— 45岁酱酒老炮专属终极修复版（已修复GET返回纯文本 + 添加日志调试）
from flask import Flask, request, Response
import requests
import json
import xml.etree.ElementTree as ET
import logging  # 添加日志，方便调试

app = Flask(__name__)

# 配置日志（打印所有请求，帮你看问题）
logging.basicConfig(level=logging.DEBUG)

# === 你的配置（已100%正确）===
CORP_ID = "wwd466aa54140422a7"
AGENT_ID = "1000002"
CORP_SECRET = "4oZPE0luv8D2nRjv2g-MP_HFIW8GfkPyaJLiM2W7-us"
TOKEN = "zhangge2025"                       # 后台填的Token，必须一样
# EncodingAESKey：用你随机生成的43位串（如果没填，就注释掉下面这行）
EncodingAESKey = "你的43位随机串"  # 替换成你后台生成的那个！
# =================================

def get_token():
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORP_ID}&corpsecret={CORP_SECRET}"
    resp = requests.get(url).json()
    if resp.get("errcode") != 0:
        logging.error(f"Token获取失败: {resp}")
    return resp["access_token"]

def qwen_ai(msg):
    prompt = f"你是15年酱酒老炮，客户说：{msg}\n推荐：飞天2690、15年坤沙899、赖茅358、王子138\n用酒友聊天语气回复："
    payload = {"model":"qwen-plus","input":{"messages":[{"role":"user","content":prompt}]}}
    try:
        r = requests.post("https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation", json=payload, timeout=10).json()
        return r["output"]["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"AI调用失败: {e}")
        return "老铁，刚才网有点卡，我马上再跟你说～"

def verify_signature(msg_signature, timestamp, nonce, echostr):
    """安全模式签名验证（如果后台是安全模式，用这个）"""
    from hashlib import sha1
    raw = TOKEN + timestamp + nonce + echostr
    hash_code = sha1(raw.encode("utf-8")).hexdigest()
    if hash_code == msg_signature:
        return echostr
    return "signature fail"

@app.route('/', methods=['GET', 'POST'])
def weixin():
    logging.info(f"收到请求: {request.method}, Args: {request.args}")  # 调试日志
    
    if request.method == 'GET':
        # 终极修复：返回纯文本 echostr（不带引号，Content-Type: text/plain）
        signature = request.args.get('msg_signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echostr = request.args.get('echostr')
        
        if signature and timestamp and nonce and echostr:  # 安全模式验证
            result = verify_signature(signature, timestamp, nonce, echostr)
            if result != "signature fail":
                return Response(result, content_type='text/plain')
            else:
                logging.error("签名验证失败")
                return "signature fail", 403
        else:  # 明文模式
            if echostr:
                return Response(echostr, content_type='text/plain')
        
        return Response("success", content_type='text/plain')
    
    # POST 处理消息
    try:
        data = request.data
        logging.info(f"收到POST数据: {data[:200]}...")  # 只打印前200字符，避免日志太长
        
        root = ET.fromstring(data)
        FromUserName = root.find('FromUserName').text
        Content = root.find('Content').text if root.find('Content') is not None else ""
        
        logging.info(f"客户消息: {Content} 从: {FromUserName}")
        
        if "小样" in Content or "尝" in Content:
            reply = "老铁，把姓名+电话+地址发我，免费寄2支50ml小样，喝完再买！"
        else:
            reply = qwen_ai(Content)
        
        # 回消息
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={get_token()}"
        payload = {
            "touser": FromUserName,
            "msgtype": "text",
            "agentid": AGENT_ID,
            "text": {"content": reply}
        }
        resp = requests.post(url, json=payload)
        logging.info(f"发送回复: {reply}, 状态: {resp.status_code}")
        
    except Exception as e:
        logging.error(f"POST处理错误: {e}")
    
    return Response("success", content_type='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
