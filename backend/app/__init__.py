from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from .config import config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # 启用CORS，允许所有源
    CORS(app, supports_credentials=True)

    # 注册蓝图
    from .routes.vision import vision_bp
    from .routes.auth import auth_bp
    from .routes.resume import resume_bp
    from .routes.ai.spark import spark_bp
    from .routes.main import bp as main_bp
    from .routes.tts import tts_bp
    from .routes.asr import asr_bp
    from .routes.job import job_bp, jobApplication_bp
    from .routes.interview import interview_bp
    from .routes.user import user_bp
    from .routes.voice_record import voice_record_bp
    from .routes.ai_ask import ai_ask_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(resume_bp, url_prefix='/api/resume')
    app.register_blueprint(interview_bp, url_prefix='/api/interview')
    app.register_blueprint(asr_bp, url_prefix='/api/asr')
    app.register_blueprint(vision_bp, url_prefix='/api/vision')
    app.register_blueprint(tts_bp, url_prefix='/api/tts')
    app.register_blueprint(spark_bp, url_prefix='/api/spark')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(main_bp)
    app.register_blueprint(job_bp, url_prefix='/api/job')  # ← 新增
    app.register_blueprint(jobApplication_bp, url_prefix='/api/apply')
    app.register_blueprint(voice_record_bp, url_prefix='/api/voice_record')
    app.register_blueprint(ai_ask_bp, url_prefix='/api/ask')
    return app