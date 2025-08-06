from app import db
from datetime import datetime
class VirtualVoice(db.Model):
    __tablename__ = 'virtual_voice'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    voice_vcn = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    description = db.Column(db.String(255))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)