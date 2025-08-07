import re
import json
from flask import Blueprint, request, jsonify
from app.models.face_expression_records import FaceExpressionRecord
from app.models.voice_record import VoiceRecord
from app import db
from datetime import datetime
from app.spark_ai import ask_spark_model, ask_spark_model_emotion_analysis
voice_record_bp = Blueprint('voice_record', __name__, url_prefix='/voice_record')
import logging
import time
import hashlib
import base64
import requests
# === 科大讯飞人脸识别配置 ===
XFYUN_APPID = "79283087"
XFYUN_API_KEY = "9b2947f843debc182b2dc455921b4cbd"
XFYUN_URL = "http://tupapi.xfyun.cn/v1/expression"
def make_xfyun_headers():
    image_name = f"img_{int(time.time())}.jpg"
    param_json = f'{{"image_name":"{image_name}","image_url":""}}'
    param_base64 = base64.b64encode(param_json.encode('utf-8')).decode('utf-8')
    cur_time = str(int(time.time()))
    check_sum = hashlib.md5((XFYUN_API_KEY + cur_time + param_base64).encode('utf-8')).hexdigest()
    return {
        "X-Appid": XFYUN_APPID,
        "X-CurTime": cur_time,
        "X-Param": param_base64,
        "X-CheckSum": check_sum,
        "Content-Type": "application/octet-stream"
    }
# Flask接口示例：保存语音并做情绪分析
@voice_record_bp.route('/save', methods=['POST'])
def save_and_analyse():
    data = request.get_json(silent=True) or {}
    transcription = data.get('transcription')
    user_id = data.get('user_id')
    print('收到请求数据:', data)
    print('user_id:', user_id, 'transcription:', transcription)
    logging.info(f'Received save request for user_id={user_id}, transcription={transcription}')
    if not user_id:
        return jsonify({'msg': '缺少用户ID'}), 400
    if not transcription:
        return jsonify({'msg': 'transcription为必填项'}), 400
    record = VoiceRecord(
        user_id=user_id,
        transcription=transcription,
        created_at=datetime.utcnow()
    )
    db.session.add(record)
    db.session.commit()
    logging.info(f'VoiceRecord created with id={record.id}')
    try:
        raw_sentiment = ask_spark_model_emotion_analysis(transcription)
        logging.info(f'Raw sentiment response: {raw_sentiment}')

        clean_str = re.sub(r'```json|```', '', raw_sentiment).strip()
        logging.info(f'Cleaned sentiment string: "{clean_str}"')

        if not clean_str:
            raise ValueError('情绪分析返回内容为空，无法解析JSON')

        try:
            sentiment_obj = json.loads(clean_str)
        except json.JSONDecodeError as e:
            logging.error(f'JSON解析失败: {e}, 内容: "{clean_str}"')
            sentiment_obj = {}

        record.sentiment = json.dumps(sentiment_obj, ensure_ascii=False)
        db.session.commit()
        logging.info(f'Sentiment saved for record id={record.id}')

        return jsonify({
            'msg': '保存并分析成功',
            'id': record.id,
            'sentiment': sentiment_obj
        }), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f'情绪分析失败: {e}')
        return jsonify({
            'msg': '情绪分析失败',
            'id': record.id,
            'error': str(e)
        }), 500
# 获取最新情绪数据接口示例
@voice_record_bp.route('/latest_sentiment', methods=['GET'])
def get_latest_sentiment():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'msg': '缺少用户ID'}), 400

    latest_record = (
        VoiceRecord.query
        .filter_by(user_id=user_id)
        .filter(VoiceRecord.sentiment != None)
        .order_by(VoiceRecord.created_at.desc())
        .first()
    )

    if not latest_record:
        return jsonify({
            'msg': '没有找到情绪分析数据',
            'sentiment': {},
            'record_id': None,
            'created_at': None
        }), 200

    try:
        sentiment_obj = json.loads(latest_record.sentiment)
        # 兼容旧数据，确保有emotion和skills字段
        if 'emotion' not in sentiment_obj:
            sentiment_obj['emotion'] = {'positive': 0, 'neutral': 0, 'negative': 0}
        if 'skills' not in sentiment_obj:
            sentiment_obj['skills'] = {}
    except Exception:
        sentiment_obj = {
            'emotion': {'positive': 0, 'neutral': 0, 'negative': 0},
            'skills': {}
        }
    return jsonify({
        'msg': '获取成功',
        'sentiment': sentiment_obj,
        'record_id': latest_record.id,
        'created_at': latest_record.created_at.isoformat()
    }), 200
def save_expression_summary(user_id, record_id, summary_data,job_title, question_set_id=None):
    print(f'保存统计数据：user_id={user_id}, record_id={record_id}, summary_data={summary_data},job_title={job_title}, question_set_id={question_set_id}')
    if not user_id or not record_id or not summary_data:
        return jsonify({"code": -1, "desc": "缺少必要参数"}), 400
    try:
        expression_json = json.dumps(summary_data, ensure_ascii=False)
        record = FaceExpressionRecord(
            user_id=user_id,
            record_id=record_id,
            job_title=job_title,
            expression_data=expression_json,
            question_set_id=question_set_id,  # 新增字段,
            created_at=datetime.utcnow(),
            is_summary=True
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({"code": 0, "desc": "统计数据已保存"})
    except Exception as e:
        return jsonify({
            "code": -1,
            "desc": "保存统计数据失败",
            "error": str(e)
        }), 500

@voice_record_bp.route('/face_expression', methods=['POST'])
def analyze_face_expression():
    data = request.get_json()
    img_base64 = data.get('image_base64')
    user_id = data.get('user_id')
    record_id = data.get('record_id')
    summary = data.get('summary')  # 是否为统计数据提交
    summary_data = data.get('summary_data')  # 表情统计字典
    job_title = data.get('job_title')  # 新增岗位字段
    question_set_id = data.get('question_set_id')  # 新增问题集ID字段

    if summary:
        return save_expression_summary(user_id, record_id, summary_data,job_title, question_set_id)

    # 正常每帧分析逻辑
    if not img_base64:
        return jsonify({"code": -1, "desc": "缺少图片数据"}), 400

    try:
        img_binary = base64.b64decode(img_base64)
    except Exception:
        return jsonify({"code": -1, "desc": "图片Base64解码失败"}), 400

    try:
        headers = make_xfyun_headers()
        resp = requests.post(XFYUN_URL, headers=headers, data=img_binary)
        result = resp.json()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "code": -1,
            "desc": "讯飞接口请求失败",
            "error": str(e)
        }), 500

###联表查询
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import aliased
import json

face_expression_bp = Blueprint('face_expression', __name__)

@voice_record_bp.route('/expression_records', methods=['GET'])
def get_expression_records():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({"code": -1, "desc": "缺少 user_id"}), 400

    voice_alias = aliased(VoiceRecord)

    results = db.session.query(
        FaceExpressionRecord,
        voice_alias.transcription,
        voice_alias.sentiment,
        voice_alias.created_at.label("voice_created_at")
    ).outerjoin(
        voice_alias,
        FaceExpressionRecord.record_id == voice_alias.id
    ).filter(
        FaceExpressionRecord.user_id == user_id,
        FaceExpressionRecord.is_summary == True
    ).order_by(FaceExpressionRecord.created_at.desc()).all()

    response = []
    for fer, transcription, sentiment_json, voice_created_at in results:
        try:
            expression_data = json.loads(fer.expression_data or "{}")
        except:
            expression_data = {}

        try:
            sentiment_data = json.loads(sentiment_json or "{}")
            emotion = sentiment_data.get("emotion", {})
            skills = sentiment_data.get("skills", {})
        except:
            emotion, skills = {}, {}

        response.append({
            "record_id": fer.record_id,
            "face_created_at": fer.created_at.isoformat(),
            "expression_data": expression_data,
            "transcription": transcription,
            "voice_created_at": voice_created_at.isoformat() if voice_created_at else None,
            "emotion": emotion,
            "job_title": fer.job_title,
            "skills": skills,
            "question_set_id": fer.question_set_id
        })

    return jsonify({
        "code": 0,
        "desc": "success",
        "data": response
    })
