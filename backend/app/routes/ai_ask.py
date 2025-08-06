from flask import Flask, request, jsonify, Blueprint

from app.models.UserAnswerAnalysis import UserAnswerAnalysis
from app.models.ai_ask import AIAsk  # 你之前定义的模型
from app.models.user_answer import UserAnswer
from app import app, db   # 你的Flask app 和 db
from app.spark_ai import ask_spark_model_quiz_analysis
import json
import re
ai_ask_bp = Blueprint('ai_ask', __name__)
from app.models.user_answer import UserAnswer
from datetime import datetime
# 获取题目列表接口，direction为可选参数，默认返回所有题目
@ai_ask_bp.route('/questions', methods=['GET'])
def get_questions():
    direction = request.args.get('direction')
    query = AIAsk.query
    if direction:
        query = query.filter_by(direction=direction)
    questions = query.limit(10).all()  # 最多返回50道题

    result = []
    for q in questions:
        result.append({
            'id': q.id,
            'direction': q.direction,
            'type': q.type,
            'content': q.content,
            'options': q.options  # 选择题的选项，简答和操作题为None
            # 不返回答案！
        })

    return jsonify(result)


# 提交答卷接口
@ai_ask_bp.route('/submit_answers', methods=['POST'])
def submit_answers():
    data = request.json
    answers = data.get('answers', [])
    user_id = data.get('user_id')
    if not answers or not user_id:
        return jsonify({"error": "用户ID或答案不能为空"}), 400

    correct_count = 0
    results = []

    for item in answers:
        qid = item.get('question_id')
        user_answer = item.get('answer', '').strip()
        question = AIAsk.query.get(qid)
        if not question:
            continue

        options = question.options or {}

        # 先计算正确答案文本和用户答案文本
        if question.type == 'choice':
            user_answer_text = options.get(user_answer.upper(), '')
            correct_answer_text = options.get((question.answer or '').upper(), '')
        else:
            user_answer_text = user_answer
            correct_answer_text = question.reference_answer or ''

        correct_answer = question.answer or question.reference_answer or ""
        is_correct = False
        item_score = 0.0

        if question.type == "choice":
            is_correct = (user_answer.upper() == (question.answer or "").upper())
            item_score = 1.0 if is_correct else 0.0
        else:
            keywords = question.keywords or []
            if keywords:
                is_correct = all(kw in user_answer for kw in keywords)
            else:
                is_correct = user_answer in correct_answer
            item_score = 1.0 if is_correct else 0.0

        if is_correct:
            correct_count += 1

        ua = UserAnswer(
            user_id=user_id,
            question_id=qid,
            answer=user_answer,
            user_answer_text=user_answer_text,
            is_correct=is_correct,
            score=item_score,
            question_content=question.content,  # 新增赋值
            correct_answer_text=correct_answer_text,  # 这里确保已经赋值正确答案文本
            correct_answer=question.answer,
            reference_answer=question.reference_answer,
            question_type=question.type,
            direction=question.direction,
            created_at=datetime.utcnow()
        )
        db.session.add(ua)

        results.append({
            "question_id": qid,
            "correct": is_correct,
            "correct_answer": question.answer,
            "correct_answer_text": correct_answer_text,
            "reference_answer": question.reference_answer,
            "user_answer_text": user_answer_text
        })

    db.session.commit()

    total = len(answers)
    score = round((correct_count / total) * 100, 2) if total > 0 else 0

    return jsonify({
        "results": results,
        "score": score,
        "total": total,
        "correct_count": correct_count
    })


# 获取某个用户的答题记录列表
@ai_ask_bp.route('/user_answers/<int:user_id>', methods=['GET'])
def get_user_answers(user_id):
    answers = UserAnswer.query.filter_by(user_id=user_id).order_by(UserAnswer.id.desc()).all()

    result = []
    for ua in answers:
        result.append({
            "question_id": ua.question_id,
            "answer": ua.answer,
            "user_answer_text": ua.user_answer_text,
            "is_correct": ua.is_correct,
            "score": ua.score,
            "correct_answer_text": ua.correct_answer_text,  # ✅ 增加返回
            "correct_answer": ua.correct_answer,
            "reference_answer": ua.reference_answer,
            "question_type": ua.question_type,
            "direction": ua.direction,
            "question_content": ua.question_content,
            "created_at": ua.created_at.strftime('%Y-%m-%d %H:%M:%S') if ua.created_at else None
        })

    return jsonify(result)
###答题分析
@ai_ask_bp.route('/analyze_answers', methods=['POST'])
def analyze_answers():
    data = request.get_json(silent=True) or {}

    user_id = data.get('user_id')
    answers = data.get('answers')
    direction = data.get('direction')

    if not user_id or not answers:
        return jsonify({'error': 'user_id和answers为必填项'}), 400

    try:
        # 获取分析结果（你自己封装的函数）
        raw_result = ask_spark_model_quiz_analysis(answers)

        # 清洗输出
        clean_str = re.sub(r'```json|```', '', raw_result).strip()
        analysis = json.loads(clean_str)

        # ✅ 保存分析记录
        analysis_record = UserAnswerAnalysis(
            user_id=user_id,
            direction=direction,
            analysis_json=json.dumps(analysis, ensure_ascii=False)
        )
        db.session.add(analysis_record)
        db.session.flush()  # 预提交，获取 analysis_record.id

        # ✅ 给当前用户当前方向未关联分析的答题记录打上 analysis_id
        UserAnswer.query.filter_by(user_id=user_id, direction=direction, analysis_id=None)\
            .update({'analysis_id': analysis_record.id})

        db.session.commit()

        return jsonify({'user_id': user_id, 'direction': direction, 'analysis': analysis})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'raw': raw_result if 'raw_result' in locals() else ''}), 500


###查询答题分析结果
@ai_ask_bp.route('/user_analysis/<int:user_id>', methods=['GET'])
def get_user_analysis(user_id):
    records = UserAnswerAnalysis.query.filter_by(user_id=user_id).order_by(UserAnswerAnalysis.created_at.desc()).all()
    result = []
    for r in records:
        result.append({
            "id": r.id,
            "direction": r.direction,
            "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "analysis": json.loads(r.analysis_json)
        })
    return jsonify(result)

from sqlalchemy import and_, desc
from flask import Blueprint, jsonify

@ai_ask_bp.route('/user_answers_with_analysis/<int:user_id>', methods=['GET'])
def get_user_answers_with_analysis(user_id):
    try:
        # 查询所有答题记录，并按创建时间降序排列
        answers = UserAnswer.query \
            .filter_by(user_id=user_id) \
            .order_by(desc(UserAnswer.created_at)) \
            .all()

        # 按 analysis_id 分组答题
        grouped_answers = {}
        for ans in answers:
            key = ans.analysis_id or f"unlinked_{ans.direction}_{ans.created_at.strftime('%Y%m%d%H%M')}"
            if key not in grouped_answers:
                grouped_answers[key] = {
                    "analysis_id": ans.analysis_id,
                    "direction": ans.direction,
                    "created_at": ans.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "answers": [],
                    "analysis": None
                }
            # ✅ 使用 to_dict() 加完整答题信息
            grouped_answers[key]["answers"].append(ans.to_dict())

        # 查询所有分析记录
        analysis_records = UserAnswerAnalysis.query \
            .filter_by(user_id=user_id) \
            .order_by(desc(UserAnswerAnalysis.created_at)) \
            .all()

        analysis_map = {r.id: {
            "analysis": json.loads(r.analysis_json),
            "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for r in analysis_records}

        # 合并分析记录到分组
        for group in grouped_answers.values():
            aid = group.get("analysis_id")
            if aid and aid in analysis_map:
                group["analysis"] = analysis_map[aid]["analysis"]

        return jsonify(list(grouped_answers.values()))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
from app.models.VirtualVoice import  VirtualVoice
@ai_ask_bp.route('/voice/list', methods=['GET'])
def list_voices():
    voices = VirtualVoice.query.all()
    result = [{
        'id': v.id,
        'voice_vcn': v.voice_vcn,
        'image_url': v.image_url,
        'description': v.description,
        'create_time': v.create_time.strftime('%Y-%m-%d %H:%M:%S') if v.create_time else None,
        'update_time': v.update_time.strftime('%Y-%m-%d %H:%M:%S') if v.update_time else None,
    } for v in voices]
    return jsonify({'success': True, 'data': result})
from app.models.VirtualAvatar import VirtualAvatar
@ai_ask_bp.route('/avatar/list', methods=['GET'])
def list_avatars():
    avatars = VirtualAvatar.query.all()
    result = [{
        'id': a.id,
        'description': a.description,
        'avatar_id': a.avatar_id,
        'image_url': a.image_url,
        'create_time': a.create_time.strftime('%Y-%m-%d %H:%M:%S') if a.create_time else None,
        'update_time': a.update_time.strftime('%Y-%m-%d %H:%M:%S') if a.update_time else None,
    } for a in avatars]
    return jsonify({'success': True, 'data': result})