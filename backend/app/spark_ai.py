import websocket, _thread as thread, json, ssl, time, hmac, hashlib, base64, re
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from flask import request, jsonify
APPID      = "79283087"
API_KEY    = "55085dd1eb4bc85992ad445b6aa0a077"
API_SECRET = "OWY2YjYwMDU3ZDAwZmFkODdmY2M3ODE2"
DOMAIN     = "x1"
SPARK_URL  = "wss://spark-api.xf-yun.com/v1/x1"
def ask_spark_model(prompt: str) -> str:
    """
    核心调用函数，接收完整 prompt，自定义内容，返回模型文本回答
    """
    result = {"answer": "", "done": False}
    class WsParam:
        def create_url(self):
            host, path = urlparse(SPARK_URL).netloc, urlparse(SPARK_URL).path
            date = format_date_time(mktime(datetime.now().timetuple()))
            sig = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
            sig_h = hmac.new(API_SECRET.encode(), sig.encode(), hashlib.sha256).digest()
            sig_b = base64.b64encode(sig_h).decode()
            auth = base64.b64encode(
                f'api_key="{API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{sig_b}"'.encode()
            ).decode()
            url = SPARK_URL + "?" + urlencode({"authorization": auth, "date": date, "host": host})
            return url

    def on_open(ws):
        def run(*_):
            data = {
                "header": {"app_id": APPID, "uid": "1"},
                "parameter": {"chat": {"domain": DOMAIN, "temperature": 0.9, "max_tokens": 2048}},
                "payload": {"message": {"text": [{"role": "user", "content": prompt}]}}
            }
            ws.send(json.dumps(data))
        thread.start_new_thread(run, ())

    def on_msg(ws, msg):
        data = json.loads(msg)
        if data["header"]["code"] != 0:
            result["done"] = True
            ws.close()
            return
        txt = data["payload"]["choices"]["text"][0].get("content", "")
        result["answer"] += txt
        if data["payload"]["choices"]["status"] == 2:
            result["done"] = True
            ws.close()

    ws = websocket.WebSocketApp(WsParam().create_url(),
                                on_open=on_open,
                                on_message=on_msg,
                                on_error=lambda *_: None,
                                on_close=lambda *_: None)
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    timeout = time.time() + 20
    while not result["done"] and time.time() < timeout:
        time.sleep(0.1)
    return result["answer"]
def ask_spark_model_emotion_analysis(text: str) -> str:
    """
    情绪分析 + 能力评估接口，构造提示词并调用核心函数
    """
    prompt = (
        "请对以下文本进行多维度分析，并只返回 JSON 格式数据：\n"
        "1. 情绪分析（返回数字百分比，不带%）：字段为 positive, neutral, negative。\n"
        "2. 能力评估（0~100 分）：语言表达能力、逻辑思维能力、创新能力、应变抗压能力，每个能力附一段简评文字（不超过30字）。\n"
        "输出格式示例如下（只返回 JSON，不需要其他解释）：\n\n"
        "{\n"
        "  \"emotion\": {\n"
        "    \"positive\": 45,\n"
        "    \"neutral\": 30,\n"
        "    \"negative\": 25\n"
        "  },\n"
        "  \"skills\": {\n"
        "    \"language_expression\": {\n"
        "      \"score\": 85,\n"
        "      \"comment\": \"语言清晰，表达流畅\"\n"
        "    },\n"
        "    \"logical_thinking\": {\n"
        "      \"score\": 78,\n"
        "      \"comment\": \"思路较清晰，结构合理\"\n"
        "    },\n"
        "    \"creativity\": {\n"
        "      \"score\": 70,\n"
        "      \"comment\": \"有一定创新意识\"\n"
        "    },\n"
        "    \"stress_response\": {\n"
        "      \"score\": 82,\n"
        "      \"comment\": \"应变能力较强\"\n"
        "    }\n"
        "  }\n"
        "}\n\n"
        f"以下是需要分析的文本：{text}"
    )
    return ask_spark_model(prompt)


def ask_spark_model_quiz_analysis(answers: list) -> str:
    """
    答题能力分析专用接口，构造答题内容提示词并调用核心函数
    """
    lines = []
    for idx, item in enumerate(answers, 1):
        q = item.get("question_content", "无题目内容")
        a = item.get("user_answer_text") or item.get("user_answer", "未回答")
        lines.append(f"{idx}. 题目内容：{q} 答案：{a}")
    prompt = (
            "请根据以下答题结果，从技术能力、专业知识水平、技能匹配度、逻辑思维能力、岗位匹配度、存在的问题六个方面做分析，"
            "并且只返回JSON格式，字段包括：技术能力、专业知识水平、技能匹配度、逻辑思维能力、岗位匹配度、存在的问题。"
            "每个字段下除了文字描述，还请返回一个数字评分（0-100的整数），用于后续图表展示。\n"
            "答题内容如下：\n" + "\n".join(lines) +
            "\n请确保返回的JSON格式合法，示例格式如下：\n"
            "{\n"
            "  \"技术能力\": {\"description\": \"技术能力较强\", \"score\": 85},\n"
            "  \"专业知识水平\": {\"description\": \"专业知识扎实\", \"score\": 90},\n"
            "  \"技能匹配度\": {\"description\": \"技能较为匹配\", \"score\": 80},\n"
            "  \"逻辑思维能力\": {\"description\": \"逻辑思维清晰\", \"score\": 88},\n"
            "  \"岗位匹配度\": {\"description\": \"岗位匹配度高\", \"score\": 82},\n"
            "  \"存在的问题\": {\"description\": \"需要加强沟通\", \"score\": 40}\n"
            "}"
    )

    return ask_spark_model(prompt)