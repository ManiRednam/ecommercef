import jwt
from functools import wraps
from flask import request, redirect, url_for


def token_required(app, role=None):

    """Token protection decorator using JWT stored in cookie `token`."""

    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.cookies.get('token')
            if not token:
                return redirect(url_for('login'))

            try:
                data = jwt.decode(
                    token,
                    app.config['SECRET_KEY'],
                    algorithms=["HS256"],
                )
            except jwt.ExpiredSignatureError:
                return redirect(url_for('login'))
            except jwt.InvalidTokenError:
                return redirect(url_for('login'))

            if role and data.get('role') != role:
                return "Unauthorized access"

            return f(*args, **kwargs)

        return decorated

    return wrapper


def get_user_by_token(app, get_user_details_by_id):
    """Decode token, fetch user record using provided DB function."""
    token = request.cookies.get('token')
    if not token:
        return None

    try:
        data = jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=["HS256"],
        )
        user_id = data.get('user_id')
        if not user_id:
            return None
        return get_user_details_by_id(user_id=user_id)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

