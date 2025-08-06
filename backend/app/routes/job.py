# app/routes/job.py
import os
import oss2
from flask import current_app
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
from app.models.job import Job
from app import db
from datetime import datetime
from app.models.jobApplication import JobApplication
job_bp = Blueprint('job', __name__, url_prefix='/job')
jobApplication_bp = Blueprint('jobApplication', __name__, url_prefix='/apply')
from app.xunfei_face import gen_face_verify_payload
import requests
from app.ise_eval import ise_eval
from app.models.voice_record import VoiceRecord
import time
import json
# 修改岗位信息
@job_bp.route('/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'error': '岗位不存在'}), 404

    data = request.json or {}
    try:
        for column in Job.__table__.columns.keys():
            if column == 'id':
                continue
            if column in data:
                value = data[column]
                # 日期字段处理
                if column in ['publish_date', 'expire_date'] and isinstance(value, str) and value:
                    try:
                        value = datetime.strptime(value, '%Y-%m-%d')
                    except ValueError:
                        continue  # 如果格式不对则跳过
                setattr(job, column, value)

        db.session.commit()
        return jsonify({'message': '岗位信息更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


# 添加岗位
@job_bp.route('/add', methods=['POST'])
def add_job():
    """
    添加岗位，同时支持上传公司 Logo（可选）
    前端需用 multipart/form-data 传递：
    - logo: 图片文件（可选）
    - 其他字段通过 form-data 一并传
    """
    # 取字段
    company_id = request.form.get('company_id', type=int) or 1
    company_name = request.form.get('company_name')
    job_title = request.form.get('job_title')
    job_category = request.form.get('job_category')
    salary_min = request.form.get('salary_min', type=int)
    salary_max = request.form.get('salary_max', type=int)
    salary_type = request.form.get('salary_type')
    experience_req = request.form.get('experience_req')
    education_req = request.form.get('education_req')
    location = request.form.get('location')
    job_nature = request.form.get('job_nature')
    description = request.form.get('description')
    requirements = request.form.get('requirements')
    benefits = request.form.get('benefits')
    expire_date_str = request.form.get('expire_date')
    contact_email = request.form.get('contact_email')
    contact_phone = request.form.get('contact_phone')
    address_detail = request.form.get('address_detail')

    # 处理过期时间
    expire_date = None
    if expire_date_str:
        try:
            expire_date = datetime.strptime(expire_date_str, '%Y-%m-%d')
        except ValueError:
            expire_date = None

    # 处理公司 Logo 上传
    company_logo_url = None
    file = request.files.get('logo')
    if file:
        import base64, requests
        photo_base64 = base64.b64encode(file.read()).decode()
        api_url = 'https://freeimage.host/api/1/upload'
        api_key = '6d207e02198a847aa98d0a2a901485a5'
        payload = {
            'key': api_key,
            'action': 'upload',
            'source': photo_base64,
            'format': 'json'
        }
        try:
            res = requests.post(api_url, data=payload)
            res_json = res.json()
            if res_json.get('status_code') == 200:
                company_logo_url = res_json['image']['url']
        except Exception as e:
            return jsonify({'error': f'Logo 上传失败: {str(e)}'}), 500

    # 创建 Job 实例
    job = Job(
        company_id=company_id,
        company_name=company_name,
        company_logo=company_logo_url,
        job_title=job_title,
        job_category=job_category,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_type=salary_type,
        experience_req=experience_req,
        education_req=education_req,
        location=location,
        job_nature=job_nature,
        description=description,
        requirements=requirements,
        benefits=benefits,
        expire_date=expire_date,
        contact_email=contact_email,
        contact_phone=contact_phone,
        address_detail=address_detail
    )

    try:
        db.session.add(job)
        db.session.commit()
        return jsonify({'msg': '岗位添加成功', 'job_id': job.id, 'logo_url': company_logo_url})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'添加失败: {str(e)}'}), 500

# ✅ 查询所有岗位
@job_bp.route('/list', methods=['GET'])
def list_jobs():
    jobs = Job.query.all()
    result = []
    for j in jobs:
        result.append({
            'id': j.id,
            'company_id': j.company_id,
            'job_title': j.job_title,
            'job_category': j.job_category,
            'salary_min': j.salary_min,
            'salary_max': j.salary_max,
            'salary_type': j.salary_type,
            'experience_req': j.experience_req,
            'education_req': j.education_req,
            'location': j.location,
            'job_nature': j.job_nature,
            'description': j.description,
            'requirements': j.requirements,
            'benefits': j.benefits,
            'publish_date': j.publish_date.strftime('%Y-%m-%d') if j.publish_date else None,
            'expire_date': j.expire_date.strftime('%Y-%m-%d') if j.expire_date else None,
            'view_count': j.view_count,
            'apply_count': j.apply_count,
            'status': j.status,
            'contact_email': j.contact_email,
            'contact_phone': j.contact_phone,
            'address_detail': j.address_detail
        })
    return jsonify(result)


# ✅ 根据ID获取岗位详情
@job_bp.route('/<int:job_id>', methods=['GET'])
def get_job(job_id):
    job = Job.query.get_or_404(job_id)
    return jsonify({
        'id': job.id,
        'job_title': job.job_title,
        'job_category': job.job_category,
        'salary_min': job.salary_min,
        'salary_max': job.salary_max,
        'salary_type': job.salary_type,
        'experience_req': job.experience_req,
        'education_req': job.education_req,
        'location': job.location,
        'job_nature': job.job_nature,
        'description': job.description,
        'requirements': job.requirements,
        'benefits': job.benefits,
        'publish_date': job.publish_date.strftime('%Y-%m-%d'),
        'expire_date': job.expire_date.strftime('%Y-%m-%d') if job.expire_date else None,
        'contact_email': job.contact_email,
        'contact_phone': job.contact_phone,
        'address_detail': job.address_detail,
        'view_count': job.view_count,
        'apply_count': job.apply_count,
        'status': job.status
    })

# 删除岗位
@job_bp.route('/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'error': '岗位不存在'}), 404

    try:
        db.session.delete(job)
        db.session.commit()
        return jsonify({'message': '岗位删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


#申请岗位
@job_bp.route('/apply', methods=['POST'])
def apply_job():
    data = request.get_json()

    # ✅ 固定用户ID为 1
    user_id = 1
    job_id = data.get('job_id')

    if not job_id:
        return jsonify({'msg': 'job_id 必填'}), 400
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'msg': '岗位不存在'}), 404

    # ✅ 如果你有 User 模型校验可以暂时注释掉
    # if not User.query.get(user_id):
    #     return jsonify({'msg': '用户不存在'}), 404

    existed = JobApplication.query.filter_by(user_id=user_id, job_id=job_id).first()
    if existed:
        return jsonify({'msg': '你已经申请过该岗位'}), 400

    application = JobApplication(
        user_id=user_id,
        job_id=job_id,
        apply_time=datetime.utcnow(),
        status='待审核'
    )
    db.session.add(application)
    job.apply_count = (job.apply_count or 0) + 1
    db.session.commit()

    return jsonify({'msg': '申请成功'}), 200
###申请岗位
from flask import request, jsonify
@job_bp.route('/applied', methods=['GET'])
def get_applied_jobs():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    applications = JobApplication.query.filter_by(user_id=user_id).all()
    result = []
    for app in applications:
        job = app.job
        result.append({
            'id': job.id,
            'job_title': job.job_title,
            'location': job.location,
            'salary': f"{job.salary_min} - {job.salary_max}元/{job.salary_type}",
            'experience_req': job.experience_req,
            'education_req': job.education_req,
            'publish_date': job.publish_date.strftime('%Y-%m-%d'),
            'status': job.status,
            'application_status': app.status,
            'apply_time': app.apply_time.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return jsonify(result)

# 查看所有岗位申请记录（包含岗位信息和用户信息）
from flask import request, jsonify
@jobApplication_bp.route('/all', methods=['GET'])
def get_all_applications():
    applications = JobApplication.query.order_by(JobApplication.apply_time.desc()).all()
    result = []
    for app in applications:
        result.append({
            'application_id': app.id,
            'user_id': app.user_id,
            'username': app.user.username,
            'job_id': app.job_id,
            'job_title': app.job.job_title,
            'job_location': app.job.location,
            'apply_time': app.apply_time.strftime('%Y-%m-%d %H:%M'),
            'status': app.status,
            'resume_path': app.resume_path,
            'interview_time': app.interview_time.strftime('%Y-%m-%d %H:%M') if app.interview_time else None,
            'interview_link': app.interview_link,
            'photo_path': app.photo_path
        })
    return jsonify(result)

#审核申请
@jobApplication_bp.route('/admin/review', methods=['POST'])
def review_application():
    data = request.get_json()
    app_id = data.get('application_id')
    new_status = data.get('status')  # '已通过' 或 '已拒绝'

    application = JobApplication.query.get_or_404(app_id)
    if new_status not in ['已通过', '已拒绝']:
        return jsonify({'msg': '状态不合法'}), 400
    application.status = new_status
    db.session.commit()
    return jsonify({'msg': f'审核完成，状态为 {new_status}'})


@jobApplication_bp.route('/admin/interview', methods=['POST'])
def set_interview_info():
    data = request.get_json()
    app_id = data.get('application_id')
    time_str = data.get('interview_time')
    link = data.get('interview_link')
    application = JobApplication.query.get_or_404(app_id)
    try:
        # 支持格式 "2025-07-12T14:30"
        interview_time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M')
    except Exception as e:
        return jsonify({'msg': '时间格式应为 YYYY-MM-DDTHH:mm', 'error': str(e)}), 400
    application.interview_time = interview_time
    application.interview_link = link
    db.session.commit()
    return jsonify({'msg': '面试信息已保存'})
from flask import request, jsonify


###查看已经申请的岗位
@jobApplication_bp.route('/applied', methods=['GET'])
def get_approved_applied_jobs():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    approved_apps = JobApplication.query.filter_by(user_id=user_id, status='已通过').all()
    result = []
    for app in approved_apps:
        job = app.job
        result.append({
            'id': job.id,
            'job_title': job.job_title,
            'location': job.location,
            'salary': f"{job.salary_min}-{job.salary_max}",
            'experience_req': job.experience_req,
            'education_req': job.education_req,
            'apply_time': app.apply_time.strftime('%Y-%m-%d %H:%M:%S') if app.apply_time else '',
            'application_status': app.status,
            'interview_time': app.interview_time.strftime('%Y-%m-%d %H:%M:%S') if app.interview_time else '',
            'interview_link': app.interview_link or '',
        })
    return jsonify(result)

# 阿里云 OSS 配置
# 简历上传接口
OSS_ENDPOINT = 'oss-cn-guangzhou.aliyuncs.com'
OSS_BUCKET_NAME = 'vimi-save'
OSS_ACCESS_KEY_ID = 'LTAI5tMYdh1oB63TbHanBcEk'
OSS_ACCESS_KEY_SECRET = 'qgniObrISa8W9IQv4vuaOQWJHWxyxh'
auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
@jobApplication_bp.route('/upload_resume', methods=['POST'])
def upload_resume():
    file = request.files.get('resume')
    job_id = request.form.get('job_id')
    user_id = request.form.get('user_id')

    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少用户ID'}), 400
    if not file or not job_id:
        return jsonify({'code': 400, 'msg': '缺少必要参数'}), 400

    # 校验 user_id 类型
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'code': 400, 'msg': '用户ID无效'}), 400

    # 校验文件类型
    allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if file.content_type not in allowed_types:
        return jsonify({'code': 400, 'msg': '文件类型不支持'}), 400

    # 生成唯一文件名
    filename = secure_filename(file.filename)
    oss_path = f'resumes/{datetime.utcnow().strftime("%Y%m%d%H%M%S")}_{filename}'

    try:
        bucket.put_object(oss_path, file.stream)
        resume_url = f'https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{oss_path}'

        application = JobApplication.query.filter_by(user_id=user_id, job_id=job_id).first()
        if not application:
            application = JobApplication(user_id=user_id, job_id=job_id)
        application.resume_path = resume_url
        db.session.add(application)
        db.session.commit()

        return jsonify({'code': 200, 'msg': '上传成功', 'resume_url': resume_url})

    except Exception as e:
        print('上传失败:', str(e))
        return jsonify({'code': 500, 'msg': '上传失败，请稍后再试'}), 500

#上传音频
@jobApplication_bp.route('/upload_audio', methods=['POST'])
def upload_audio():
    file = request.files.get('file')
    job_id = request.form.get('job_id')
    user_id = request.form.get('user_id')

    if not user_id:
        return jsonify({'code': 400, 'msg': '缺少用户ID'}), 400
    if not file or not job_id:
        return jsonify({'code': 400, 'msg': '缺少必要参数'}), 400

    allowed_types = {'audio/mpeg', 'audio/wav', 'audio/webm', 'audio/x-wav', 'audio/mp4'}
    if file.content_type not in allowed_types:
        return jsonify({'code': 400, 'msg': '不支持的音频格式'}), 400

    try:
        print("\n=== 开始处理音频上传和评测 ===")

        # 上传音频到 OSS
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        oss_key = f'audios/{timestamp}_{filename}'
        bucket.put_object(oss_key, file.stream)
        audio_url = f'https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{oss_key}'
        print(f'[1/5] 上传音频到OSS成功: {audio_url}')

        # 更新 job_application 表
        application = JobApplication.query.filter_by(user_id=user_id, job_id=job_id).first()
        if not application:
            application = JobApplication(user_id=user_id, job_id=job_id)
            db.session.add(application)
        application.audio_path = audio_url
        db.session.commit()
        print('[2/5] 更新数据库成功')

        # 获取最近的转写文本
        voice_record = VoiceRecord.query.filter_by(user_id=user_id).order_by(VoiceRecord.created_at.desc()).first()

        if not voice_record or not voice_record.transcription:
            print("[3/5] 未找到对应转写文本")
            return jsonify({
                'code': 200,
                'msg': '上传成功，但未找到转写文本',
                'audio_url': audio_url
            })

        transcription = voice_record.transcription.strip()
        print(f"[3/5] 获取转写文本成功：{transcription[:50]}...")

        # 讯飞 ISE 评测
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"[4/5] 开始第{attempt+1}次讯飞ISE评测...")
                xml_result, score_dict = ise_eval(audio_url, transcription)
                print("[4/5] 讯飞ISE评测成功")
                break
            except Exception as e:
                print(f"评测失败: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)

        # 只保存需要的字段
        evaluation_data = {
            'fluency_score': score_dict.get('fluency_score', 0.0),
            'tone_score': score_dict.get('tone_score', 0.0),
            'phone_score': score_dict.get('phone_score', 0.0),
            'integrity_score': score_dict.get('integrity_score', 0.0),
            'total_score': score_dict.get('total_score', 0.0),
            'timestamp': datetime.utcnow().isoformat()
        }

        application.evaluation_result = json.dumps(evaluation_data)
        db.session.commit()
        print("[5/5] 评测结果已保存数据库")

        return jsonify({
            'code': 200,
            'msg': '上传并测评成功',
            'audio_url': audio_url,
            'scores': evaluation_data
        })

    except Exception as e:
        db.session.rollback()
        print(f"[错误] 处理失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'上传失败: {str(e)}',
            'audio_url': audio_url if 'audio_url' in locals() else None
        })

#查询语音测评：
@jobApplication_bp.route('/evaluation', methods=['GET'])
def get_evaluation_by_user_job():
    user_id = request.args.get('user_id', type=int)
    job_id = request.args.get('job_id', type=int)

    if not user_id or not job_id:
        return jsonify({'msg': '缺少 user_id 或 job_id 参数'}), 400

    application = JobApplication.query.filter_by(user_id=user_id, job_id=job_id).first()
    if not application:
        return jsonify({'msg': '未找到对应的申请'}), 404

    return jsonify({
        'application_id': application.id,
        'user_id': application.user_id,
        'job_id': application.job_id,
        'evaluation_result': application.evaluation_result or '',
    })

#上传证件照
@jobApplication_bp.route('/upload_photo', methods=['POST'])
def upload_photo():
    user_id = request.form.get('user_id', type=int)
    file = request.files.get('photo')
    job_id = request.form.get('job_id')

    if not user_id:
        return jsonify({'msg': 'user_id 为必填项'}), 400
    if not file or not job_id:
        return jsonify({'msg': 'photo 文件 和 job_id 为必填项'}), 400

    import base64
    photo_bytes = file.read()
    photo_base64 = base64.b64encode(photo_bytes).decode()

    api_key = '6d207e02198a847aa98d0a2a901485a5'
    api_url = 'https://freeimage.host/api/1/upload'

    data = {
        'key': api_key,
        'action': 'upload',
        'source': photo_base64,
        'format': 'json'
    }

    try:
        import requests
        response = requests.post(api_url, data=data)
        res_json = response.json()

        if res_json.get('status_code') != 200:
            return jsonify({'msg': '图床上传失败', 'detail': res_json}), 500

        photo_url = res_json['image']['url']
    except Exception as e:
        return jsonify({'msg': '上传图床失败', 'error': str(e)}), 500

    application = JobApplication.query.filter_by(user_id=user_id, job_id=job_id).first()
    if not application:
        application = JobApplication(
            user_id=user_id,
            job_id=job_id,
            apply_time=datetime.utcnow(),
            status='待审核',
            photo_path=photo_url
        )
        db.session.add(application)
    else:
        application.photo_path = photo_url
        application.apply_time = datetime.utcnow()

    db.session.commit()

    return jsonify({'msg': '照片上传成功', 'photo_url': photo_url}), 200

#人脸比对
@jobApplication_bp.route('/face-verify', methods=['POST'])
def face_verify():
    user_id = request.form.get('user_id')
    job_id = request.form.get('job_id')
    photo_file = request.files.get('photo')  # 前端摄像头照片

    if not user_id or not job_id or not photo_file:
        return jsonify({'msg': '参数缺失'}), 400

    application = JobApplication.query.filter_by(user_id=user_id, job_id=job_id).first()
    if not application or not application.photo_path:
        return jsonify({'msg': '未找到证件照'}), 404

    try:
        # 获取照片数据
        id_photo_bytes = requests.get(application.photo_path).content
        live_photo_bytes = photo_file.read()

        result = gen_face_verify_payload(
            appid='e5850021',
            api_key='dda0f69489a3db1e0d495f40a5fd40eb',
            api_secret='OTNlMGI0OWUxM2JlMWRhM2EzNDVhZjAw',
            id_photo_bytes=id_photo_bytes,
            live_photo_bytes=live_photo_bytes
        )

        score = float(result.get('score', 0))
        passed = score > 0.85  # 阈值，可调整

        return jsonify({
            'msg': '比对完成',
            'score': score,
            'passed': passed
        })
    except Exception as e:
        return jsonify({'msg': '人脸识别失败', 'error': str(e)}), 500

#语音评测
@jobApplication_bp.route('/ise/evaluate', methods=['POST'])
def ise_evaluate():
    if "audio" not in request.files or "text" not in request.form:
        return jsonify({"code": 400, "msg": "参数缺失"})
    audio_file = request.files["audio"]
    text = request.form["text"]
    tmp_path = "./tmp_audio.wav"
    audio_file.save(tmp_path)
    try:
        result = run_ise_eval(tmp_path, text)
        return jsonify({"code": 200, "msg": "评测成功", "data": result})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


