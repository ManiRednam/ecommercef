from flask import redirect, url_for, request
import jwt


def json_success(payload=None, status_code=200):
    resp = {"status": "success"}
    if payload is not None:
        resp["data"] = payload
    return (resp, status_code)


def json_error(message, status_code=400, code=None):
    resp = {"status": "error", "message": message}
    if code is not None:
        resp["code"] = code
    return (resp, status_code)


def get_data_from_token(app):
    token = request.cookies.get('token')
    if not token:
        return redirect(url_for('login'))

    try:
        return jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return redirect(url_for('login'))
    except jwt.InvalidTokenError:
        return redirect(url_for('login'))

