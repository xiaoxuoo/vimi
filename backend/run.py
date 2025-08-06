import os
os.environ['FLASK_SKIP_DOTENV'] = '1'  # 禁用 Flask 的 .env 自动加载

from app import create_app
from app import db
app = create_app()
# ✅ 添加环境变量设置
os.environ['OSS_ACCESS_KEY_ID'] = 'LTAI5tMYdh1oB63TbHanBcEk'
os.environ['OSS_ACCESS_KEY_SECRET'] = 'qgniObrISa8W9IQv4vuaOQWJHWxyxh'
if __name__ == '__main__':
    # 使用 0.0.0.0 允许外部访问，端口 5000
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)