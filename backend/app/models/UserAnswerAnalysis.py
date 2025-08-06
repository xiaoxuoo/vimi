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
