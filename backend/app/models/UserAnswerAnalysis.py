from app import db
from datetime import datetime

class UserAnswerAnalysis(db.Model):
    __tablename__ = 'user_answer_analysis'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.String(50))
    analysis_json = db.Column(db.Text)  # 保存 json 字符串
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 可选：反向关联答题记录
    answers = db.relationship('UserAnswer', backref='analysis', lazy=True)
    # 新增字段，关联岗位申请


    job_application_id = db.Column(db.Integer, db.ForeignKey('job_applications.id'), nullable=True)

# 关系映射，方便通过UserAnswerAnalysis获取对应岗位申请
    job_application = db.relationship('JobApplication', backref=db.backref('answer_analyses', lazy=True))