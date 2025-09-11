from flask import Flask, render_template, request, jsonify
from database import engine, SessionLocal
from models import Base, User
import crud
import scheduler

app = Flask(__name__)

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

# Middleware to create a new DB session for each request
@app.before_request
def before_request():
    request.db = SessionLocal()

@app.teardown_request
def teardown_request(exception=None):
    db = getattr(request, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('index.html')

# --- API Routes ---

@app.route('/api/users', methods=['GET'])
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
def update_user_api(user_id):
    data = request.get_json()
    updated_user = crud.update_user(request.db, user_id=user_id, user_data=data)
    if updated_user:
        scheduler.add_or_update_job_for_user(updated_user, app)
    return jsonify({"id": updated_user.id})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user_api(user_id):
    scheduler.remove_job_for_user(user_id)
    crud.delete_user(request.db, user_id=user_id)
    return '', 204

# --- Settings API ---

@app.route('/api/settings', methods=['GET'])
def get_settings_api():
    webhook = crud.get_setting(request.db, 'dingtalk_webhook') or ''
    secret = crud.get_setting(request.db, 'dingtalk_secret') or ''
    return jsonify({'dingtalk_webhook': webhook, 'dingtalk_secret': secret})

@app.route('/api/settings', methods=['POST'])
def update_settings_api():
    data = request.get_json()
    crud.update_setting(request.db, 'dingtalk_webhook', data.get('dingtalk_webhook', ''))
    crud.update_setting(request.db, 'dingtalk_secret', data.get('dingtalk_secret', ''))
    return jsonify({"message": "Settings updated"})

if __name__ == '__main__':
    scheduler.initialize_scheduler(app)
    app.run(debug=True, port=8000, use_reloader=False)