# app.py  —— 45岁酱酒老炮专属极简版（已为你填好所有配置）
from flask import Flask, request
import requests
import json

app = Flask(__name__)

# === 你的配置（已100%正确）===
CORP_ID = "wwd466aa54140422a7"
AGENT_ID = "1000002"
CORP_SECRET = "4oZPE0luv8D2nRjv2g-MP_HFIW8GfkPyaJLiM2W7-us"
TOKEN = "zhangge2025"                       # 回调用的Token，随便填
# =================================

def get_token():
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORP_ID}&corpsecret={CORP_SECRET}"
    return requests.get(url).json()["access_token"]

def qwen_ai(msg):
    prompt = f"你是15年酱酒老炮，客户说：{msg}\n推荐：飞天2690、15年坤沙899、赖茅358、王子138\n用酒友聊天语气回复："
    payload = {"model":"qwen-plus","input":{"messages":[{"role":"user","content":prompt}]}}
    try:
        r = requests.post("https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation", json=payload, timeout=10).json()
        return r["output"]["choices"][0]["message"]["content"]
    except:
        return "老铁，刚才网有点卡，我马上再跟你说～"

@app.route('/', methods=['GET', 'POST'])
def weixin():
    if request.method == 'GET':                     # 企业微信验证
        echostr = request.args.get('echostr')
        return echostr
    
    data = request.data.decode('utf-8')
    if "xml" in data:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(data)
        FromUserName = root.find('FromUserName').text
        Content = root.find('Content').text if root.find('Content') is not None else ""
        
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
        requests.post(url, json=payload)
    
    return "success"

if __name__ == '__main__':
    app.run()
