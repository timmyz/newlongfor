from sqlalchemy.orm import Session
import models

# --- User CRUD ---

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_account_id(db: Session, account_id: str):
    return db.query(models.User).filter(models.User.account_id == account_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user_data: dict):
    db_user = models.User(
        username=user_data['username'], 
        account_id=user_data['account_id'],
        token=user_data['token'],
        x_lf_usertoken=user_data.get('x_lf_usertoken', user_data['token']),  # 默认使用token的值
        cookie=user_data.get('cookie'),
        x_lf_dxrisk_token=user_data.get('x_lf_dxrisk_token'),
        x_lf_channel=user_data.get('x_lf_channel', 'L0'),
        x_lf_bu_code=user_data.get('x_lf_bu_code', 'L00602'),
        x_lf_dxrisk_source=user_data.get('x_lf_dxrisk_source', '2'),
        is_active=user_data.get('is_active', True),
        checkin_time=user_data.get('checkin_time', '01:05')
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_data: dict):
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    # 更新所有提供的字段
    for key, value in user_data.items():
        if hasattr(db_user, key):
            # 处理前端传递的字段名差异
            if key == 'x-lf-usertoken':
                setattr(db_user, 'x_lf_usertoken', value)
            elif key == 'x-lf-dxrisk-token':
                setattr(db_user, 'x_lf_dxrisk_token', value)
            elif key == 'x-lf-channel':
                setattr(db_user, 'x_lf_channel', value)
            elif key == 'x-lf-bu-code':
                setattr(db_user, 'x_lf_bu_code', value)
            elif key == 'x-lf-dxrisk-source':
                setattr(db_user, 'x_lf_dxrisk_source', value)
            else:
                setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# --- Settings CRUD ---

def get_setting(db: Session, key: str) -> str:
    setting = db.query(models.Setting).filter(models.Setting.key == key).first()
    return setting.value if setting else None

def update_setting(db: Session, key: str, value: str):
    setting = db.query(models.Setting).filter(models.Setting.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = models.Setting(key=key, value=value)
        db.add(setting)
    db.commit()
    return setting