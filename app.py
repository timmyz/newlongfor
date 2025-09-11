import os
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import engine, SessionLocal
from models import Base, User, Admin
import crud
import scheduler
import hashlib
from functools import wraps

# 尝试加载配置文件
try:
    from config import TURNSTILE_ENABLED, TURNSTILE_SITE_KEY, TURNSTILE_SECRET_KEY
except ImportError:
    # 如果没有配置文件，使用环境变量或默认值
    TURNSTILE_ENABLED = os.getenv('TURNSTILE_ENABLED', 'false').lower() == 'true'
    TURNSTILE_SITE_KEY = os.getenv('TURNSTILE_SITE_KEY', '')
    TURNSTILE_SECRET_KEY = os.getenv('TURNSTILE_SECRET_KEY', '')

app = Flask(__name__)
app.secret_key = 'longfor-signin-secret-key-2024'  # 生产环境应使用环境变量

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

# Initialize default admin account
def init_admin():
    db = SessionLocal()
    try:
        admin = db.query(Admin).first()
        if not admin:
            password_hash = hashlib.sha256('admin'.encode()).hexdigest()
            default_admin = Admin(username='admin', password_hash=password_hash)
            db.add(default_admin)
            db.commit()
            print("Default admin account created: admin/admin")
    finally:
        db.close()

init_admin()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Middleware to create a new DB session for each request
@app.before_request
def before_request():
    request.db = SessionLocal()

@app.teardown_request
def teardown_request(exception=None):
    db = getattr(request, 'db', None)
    if db is not None:
        db.close()

def verify_turnstile(token):
    """验证 Turnstile token"""
    # 先检查配置文件
    if TURNSTILE_ENABLED and TURNSTILE_SECRET_KEY:
        secret_key = TURNSTILE_SECRET_KEY
    else:
        # 再从数据库获取配置
        db = SessionLocal()
        try:
            enabled = crud.get_setting(db, 'turnstile_enabled')
            secret_key = crud.get_setting(db, 'turnstile_secret_key')
            
            # 如果未启用或没有配置密钥，跳过验证
            if enabled != 'true' or not secret_key:
                return True  # 未配置则跳过验证
        finally:
            db.close()
    
    try:
        response = requests.post('https://challenges.cloudflare.com/turnstile/v0/siteverify', data={
            'secret': secret_key,
            'response': token
        }, timeout=10)
        
        result = response.json()
        return result.get('success', False)
    except Exception:
        return False  # 验证失败时拒绝

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # 优先使用配置文件
        if TURNSTILE_ENABLED and TURNSTILE_SITE_KEY:
            site_key = TURNSTILE_SITE_KEY
            turnstile_enabled = True
        else:
            # 从数据库获取配置
            db = SessionLocal()
            try:
                site_key = crud.get_setting(db, 'turnstile_site_key') or ''
                enabled = crud.get_setting(db, 'turnstile_enabled')
                turnstile_enabled = enabled == 'true' if enabled else False
            finally:
                db.close()
        
        return render_template('login.html', 
                             turnstile_site_key=site_key,
                             turnstile_enabled=turnstile_enabled)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    turnstile_token = data.get('turnstile_token')
    
    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    # 验证 Turnstile
    if not verify_turnstile(turnstile_token):
        return jsonify({'message': '安全验证失败，请重试'}), 400
    
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.username == username).first()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if admin and admin.password_hash == password_hash:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return jsonify({'message': '登录成功'}), 200
        else:
            return jsonify({'message': '用户名或密码错误'}), 401
    finally:
        db.close()

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# --- API Routes ---

@app.route('/api/users', methods=['GET'])
@login_required
def get_users_api():
    users = crud.get_users(request.db)
    users_list = []
    for user in users:
        users_list.append({
            "id": user.id,
            "username": user.username,
            "account_id": user.account_id,
            "is_active": user.is_active,
            "last_checkin_time": user.last_checkin_time.isoformat() if user.last_checkin_time else None,
            "last_checkin_status": user.last_checkin_status,
            "checkin_time": user.checkin_time,
            "token": user.token,
            "x-lf-usertoken": user.x_lf_usertoken,
            "cookie": user.cookie,
            "x-lf-dxrisk-token": user.x_lf_dxrisk_token,
            "x-lf-channel": user.x_lf_channel,
            "x-lf-bu-code": user.x_lf_bu_code,
            "x-lf-dxrisk-source": user.x_lf_dxrisk_source
        })
    return jsonify(users_list)

@app.route('/api/users', methods=['POST'])
@login_required
def create_user_api():
    data = request.get_json()
    # 处理前端传递的字段名差异
    if 'x-lf-usertoken' in data:
        data['x_lf_usertoken'] = data.pop('x-lf-usertoken')
    if 'x-lf-dxrisk-token' in data:
        data['x_lf_dxrisk_token'] = data.pop('x-lf-dxrisk-token')
    if 'x-lf-channel' in data:
        data['x_lf_channel'] = data.pop('x-lf-channel')
    if 'x-lf-bu-code' in data:
        data['x_lf_bu_code'] = data.pop('x-lf-bu-code')
    if 'x-lf-dxrisk-source' in data:
        data['x_lf_dxrisk_source'] = data.pop('x-lf-dxrisk-source')
    
    user = crud.create_user(request.db, user_data=data)
    scheduler.add_or_update_job_for_user(user, app)
    return jsonify({"id": user.id, "username": user.username}), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user_api(user_id):
    data = request.get_json()
    updated_user = crud.update_user(request.db, user_id=user_id, user_data=data)
    if updated_user:
        scheduler.add_or_update_job_for_user(updated_user, app)
    return jsonify({"id": updated_user.id})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user_api(user_id):
    scheduler.remove_job_for_user(user_id)
    crud.delete_user(request.db, user_id=user_id)
    return '', 204

# --- Settings API ---

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password_api():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'message': '当前密码和新密码不能为空'}), 400
    
    if len(new_password) < 4:
        return jsonify({'message': '新密码长度至少为4位'}), 400
    
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.username == session['admin_username']).first()
        current_password_hash = hashlib.sha256(current_password.encode()).hexdigest()
        
        if admin.password_hash != current_password_hash:
            return jsonify({'message': '当前密码错误'}), 401
        
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        admin.password_hash = new_password_hash
        db.commit()
        
        return jsonify({'message': '密码修改成功'}), 200
        
    finally:
        db.close()

@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings_api():
    webhook = crud.get_setting(request.db, 'dingtalk_webhook') or ''
    secret = crud.get_setting(request.db, 'dingtalk_secret') or ''
    turnstile_enabled = crud.get_setting(request.db, 'turnstile_enabled') == 'true'
    turnstile_site_key = crud.get_setting(request.db, 'turnstile_site_key') or ''
    turnstile_secret_key = crud.get_setting(request.db, 'turnstile_secret_key') or ''
    
    return jsonify({
        'dingtalk_webhook': webhook, 
        'dingtalk_secret': secret,
        'turnstile_enabled': turnstile_enabled,
        'turnstile_site_key': turnstile_site_key,
        'turnstile_secret_key': turnstile_secret_key
    })

@app.route('/api/settings', methods=['POST'])
@login_required
def update_settings_api():
    data = request.get_json()
    crud.update_setting(request.db, 'dingtalk_webhook', data.get('dingtalk_webhook', ''))
    crud.update_setting(request.db, 'dingtalk_secret', data.get('dingtalk_secret', ''))
    return jsonify({"message": "Settings updated"})

@app.route('/api/turnstile', methods=['POST'])
@login_required
def update_turnstile_api():
    data = request.get_json()
    crud.update_setting(request.db, 'turnstile_enabled', 'true' if data.get('turnstile_enabled') else 'false')
    crud.update_setting(request.db, 'turnstile_site_key', data.get('turnstile_site_key', ''))
    crud.update_setting(request.db, 'turnstile_secret_key', data.get('turnstile_secret_key', ''))
    return jsonify({"message": "Turnstile settings updated"})

if __name__ == '__main__':
    scheduler.initialize_scheduler(app)
    # 生产环境建议设置 debug=False
    app.run(debug=False, port=5900, use_reloader=False)