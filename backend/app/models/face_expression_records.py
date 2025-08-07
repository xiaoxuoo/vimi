from datetime import datetime
from app import db
class FaceExpressionRecord(db.Model):
    __tablename__ = 'face_expression_records'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, nullable=True, index=True)
    record_id = db.Column(db.BigInteger, nullable=True, index=True)
    expression_data = db.Column(db.Text, nullable=False)
    is_summary = db.Column(db.Boolean, default=False, nullable=False)
    job_title = db.Column(db.String(255), nullable=True)  # 新增岗位名称字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    question_set_id = db.Column(db.String(64))  # 新增字段
    def __repr__(self):
        return f'<FaceExpressionRecord id={self.id} user_id={self.user_id} job_title={self.job_title} is_summary={self.is_summary} created_at={self.created_at}>'
