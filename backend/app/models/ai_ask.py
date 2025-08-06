from app import db
from datetime import datetime

class AIAsk(db.Model):
    __tablename__ = 'ai_ask'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    direction = db.Column(db.String(100), nullable=False)   # 方向：人工智能、大数据、物联网等
    type = db.Column(db.String(50), nullable=False)         # 题型：choice/simple/operation
    content = db.Column(db.Text, nullable=False)            # 题目内容

    options = db.Column(db.JSON, nullable=True)             # 选择题选项，格式：{"A":"选项1","B":"选项2"}
    answer = db.Column(db.String(255), nullable=True)       # 标准答案，选择题存选项字母，简答和操作题存参考答案或关键词

    keywords = db.Column(db.JSON, nullable=True)            # 简答/操作题关键词列表
    reference_answer = db.Column(db.Text, nullable=True)    # 参考答案

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'direction': self.direction,
            'type': self.type,
            'content': self.content,
            'options': self.options,
            'answer': self.answer,
            'keywords': self.keywords,
            'reference_answer': self.reference_answer,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
