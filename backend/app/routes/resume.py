from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import uuid
from ..models.resume import Resume
from ..utils.auth import candidate_required
from .. import db
resume_bp = Blueprint('resume', __name__)
@resume_bp.route('/', methods=['GET'])
@candidate_required
def get_resumes():
    """获取当前用户的所有简历"""
    user_id = get_jwt_identity()
    resumes = Resume.query.filter_by(user_id=user_id).all()
    return jsonify({
        'success': True,
        'data': [resume.to_dict() for resume in resumes]
    })

@resume_bp.route('/', methods=['POST'])
@candidate_required
def create_resume():
    """创建新简历"""
    user_id = get_jwt_identity()
    data = request.json

    try:
        resume = Resume(
            user_id=user_id,
            name=data.get('name', '未命名简历'),
            content=data.get('content', {}),
        )
        db.session.add(resume)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '创建成功',
            'data': resume.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@resume_bp.route('/<int:resume_id>', methods=['PUT'])
@candidate_required
def update_resume(resume_id):
    """更新简历"""
    user_id = get_jwt_identity()
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()

    if not resume:
        return jsonify({
            'success': False,
            'message': '简历不存在或无权访问'
        }), 404

    data = request.json
    try:
        if 'name' in data:
            resume.name = data['name']
        if 'content' in data:
            resume.content = data['content']
        resume.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '更新成功',
            'data': resume.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@resume_bp.route('/<int:resume_id>', methods=['DELETE'])
@candidate_required
def delete_resume(resume_id):
    """删除简历"""
    user_id = get_jwt_identity()
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()

    if not resume:
        return jsonify({
            'success': False,
            'message': '简历不存在或无权访问'
        }), 404

    try:
        db.session.delete(resume)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@resume_bp.route('/<int:resume_id>/duplicate', methods=['POST'])
@candidate_required
def duplicate_resume(resume_id):
    """复制简历"""
    user_id = get_jwt_identity()
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()

    if not resume:
        return jsonify({
            'success': False,
            'message': '简历不存在或无权访问'
        }), 404

    try:
        new_resume = Resume(
            user_id=user_id,
            name=f"{resume.name} (副本)",
            content=resume.content.copy() if resume.content else {},
        )
        db.session.add(new_resume)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '复制成功',
            'data': new_resume.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@resume_bp.route('/<int:resume_id>/share', methods=['POST'])
@candidate_required
def share_resume(resume_id):
    """生成简历分享链接"""
    user_id = get_jwt_identity()
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()

    if not resume:
        return jsonify({
            'success': False,
            'message': '简历不存在或无权访问'
        }), 404

    try:
        share_code = str(uuid.uuid4())[:8]
        resume.share_code = share_code
        resume.share_expire_time = datetime.utcnow().timestamp() + 7 * 24 * 3600  # 7天后过期
        db.session.commit()

        share_url = f"{request.host_url}resume/share/{share_code}"
        return jsonify({
            'success': True,
            'message': '分享链接生成成功',
            'data': {
                'share_code': share_code,
                'share_url': share_url,
                'expire_time': resume.share_expire_time
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@resume_bp.route('/share/<share_code>', methods=['GET'])
def view_shared_resume(share_code):
    """查看分享的简历"""
    resume = Resume.query.filter_by(share_code=share_code).first()

    if not resume or not resume.is_share_valid():
        return jsonify({
            'success': False,
            'message': '分享链接无效或已过期'
        }), 404

    return jsonify({
        'success': True,
        'data': resume.to_dict()
    })



###智能生成简历
from flask import Flask, request, jsonify
import json
import base64
import requests
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import hmac
from urllib.parse import urlencode

app = Flask(__name__)

# 讯飞API配置
APPID = 'e5850021'
APIKEY = 'dda0f69489a3db1e0d495f40a5fd40eb'
APISECRET = 'OTNlMGI0OWUxM2JlMWRhM2EzNDVhZjAw'

# 工具类
class Url:
    def __init__(self, host, path, schema):
        self.host = host
        self.path = path
        self.schema = schema

def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    path = host[edidx:]
    host = host[:edidx]
    return Url(host, path, schema)

def assemble_ws_auth_url(requset_url, method="GET", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    date = format_date_time(mktime(datetime.now().timetuple()))
    signature_origin = f"host: {host}\ndate: {date}\n{method} {path} HTTP/1.1"
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode('utf-8')
    authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
    return requset_url + "?" + urlencode({
        "host": host,
        "date": date,
        "authorization": authorization
    })

def getBody(appid, text):
    return {
        "header": {
            "app_id": appid,
            "status": 3,
        },
        "parameter": {
            "ai_resume": {
                "resData": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
        "payload": {
            "reqData": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain",
                "status": 3,
                "text": base64.b64encode(text.encode("utf-8")).decode('utf-8')
            }
        }
    }

def call_xunfei_api(text):
    host = 'https://cn-huadong-1.xf-yun.com/v1/private/s73f4add9'
    url = assemble_ws_auth_url(host, method='POST', api_key=APIKEY, api_secret=APISECRET)
    body = getBody(APPID, text)
    response = requests.post(url, json=body, headers={'content-type': "application/json"}).text
    return json.loads(response)

# ================= 接口部分 =================
@app.route('/generate-resume-image', methods=['POST'])
def generate_resume_image():
    try:
        req_data = request.get_json()
        user_text = req_data.get("content", "")

        if not user_text.strip():
            return jsonify({"code": 400, "message": "简历内容不能为空"}), 400

        result = call_xunfei_api(user_text)

        if result["header"]["code"] != 0:
            return jsonify({
                "code": result["header"]["code"],
                "message": result["header"].get("message", "生成失败")
            }), 500

        # 解析结果
        payload_base64 = result["payload"]["resData"]["text"]
        decoded_str = base64.b64decode(payload_base64).decode("utf-8")
        final_data = json.loads(decoded_str)

        # 提取 img_url 列表
        image_urls = [item["img_url"] for item in final_data.get("links", [])]

        return jsonify({
            "code": 200,
            "message": "简历图片生成成功",
            "images": image_urls
        })

    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器错误: {str(e)}"}), 500


