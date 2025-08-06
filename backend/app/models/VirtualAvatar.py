from app import db
from datetime import datetime
class VirtualAvatar(db.Model):
    __tablename__ = 'virtual_avatar'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    description = db.Column(db.String(255))
    avatar_id = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)