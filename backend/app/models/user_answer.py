from app import db
from datetime import datetime

class UserAnswer(db.Model):
    __tablename__ = 'user_answer'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)  # 用户 ID
    question_id = db.Column(db.Integer, db.ForeignKey('ai_ask.id'), nullable=False)
    answer = db.Column(db.Text, nullable=False)  # 用户答案
    is_correct = db.Column(db.Boolean, nullable=False)  # 是否正确
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float, default=0.0)  # 每题得分

    # ✅ 新增字段
    correct_answer = db.Column(db.String(255), nullable=True)      # 标准答案（用于展示）
    reference_answer = db.Column(db.Text, nullable=True)           # 参考答案（简答题）
    question_type = db.Column(db.String(50), nullable=True)        # 题目类型（choice/simple/operation）
    direction = db.Column(db.String(100), nullable=True)           # 方向（人工智能/大数据/物联网等）
    analysis_id = db.Column(db.Integer, db.ForeignKey('user_answer_analysis.id'), nullable=True)
    user_answer_text = db.Column(db.Text, nullable=True)  # 用户选项对应的文本内容
    correct_answer_text = db.Column(db.Text, nullable=True)  # 正确选项对应的文本内容
    question_content = db.Column(db.Text)  # 新增字段，存题干
    # 关联题目（可选）
    question_set_id = db.Column(db.String(36), nullable=False, default='')

    question = db.relationship("AIAsk", backref="user_answers")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ 添加这一行
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question_id": self.question_id,
            "answer": self.answer,
            "is_correct": self.is_correct,
            "score": self.score,
            "submitted_at": self.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            "correct_answer": self.correct_answer,
            "reference_answer": self.reference_answer,
            "question_type": self.question_type,
            "direction": self.direction,
            "correct_answer_text": self.correct_answer_text,  # ✅ 添加这一行
            "user_answer_text": self.user_answer_text , # ✅ 同样加这个
            "analysis_id": self.analysis_id,
            "question_content":self.question_content,
            "question_set_id": self.question_set_id  # ✅ 新增返回

        }
