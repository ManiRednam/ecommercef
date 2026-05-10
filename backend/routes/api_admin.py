import os
from flask import Blueprint, current_app, request

from backend.functions.http import json_error, json_success
from backend.functions.auth import token_required



def create_api_admin_blueprint(db_utility_module, userutility_module, get_user_details_by_id):
    """Create API admin blueprint.

    db_utility_module: backend.database.utility (where admin DB functions are imported)
    userutility_module: backend.database.userutility (optional; not used here yet)
    """

    api_admin = Blueprint('api_admin', __name__, url_prefix='/api/admin')

    # Decorators can access current_app safely at request time
    @api_admin.get('/dashboard')
    @token_required(current_app._get_current_object(), role='admin')

    def dashboard():

        try:
            total_products = db_utility_module.totalProducts()
            total_orders = db_utility_module.totalOrdersCount()
            pending_orders = db_utility_module.totalOrdersCount(status="PENDING")
            total_users = len(db_utility_module.usersDetails())

            stats = [
                {"title": "Products", "value": total_products},
                {"title": "Orders", "value": total_orders},
                {"title": "Pending", "value": pending_orders},
                {"title": "Users", "value": total_users},
            ]

            return json_success({"stats": stats, "activities": []})
        except Exception as e:
            return json_error(str(e), status_code=500)

    @api_admin.get('/products')
    @token_required(role='admin')

    def products_get():
        name = request.args.get('name', "").strip()
        category = request.args.get('category', "").strip()
        status = request.args.get('status', "").strip()  # expects 1/0

        if status == "1":
            status = 1
        elif status == "0":
            status = 0
        elif status == "":
            status = ''

        products = db_utility_module.getProductsFromDB(name=name, category=category, status=status)

        normalized = []
        for p in products:
            normalized.append({
                "id": p.get("PRODUCTID"),
                "name": p.get("NAME"),
                "description": p.get("DESCRIPTION"),
                "category": p.get("CATEGORY"),
                "imageUrl": p.get("IMAGE_URL"),
                "price": float(p.get("PRICE")) if p.get("PRICE") is not None else None,
                "stock": p.get("STOCK"),
                "active": int(p.get("ACTIVE")) if p.get("ACTIVE") is not None else None,
            })

        return json_success(normalized)

    @api_admin.post('/products')
    @token_required(role='admin')

    def products_post():
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            category = request.form.get('category')
            price = request.form.get('price')
            stock = request.form.get('stock')
            active = request.form.get('active', '1')
            active = int(active) if str(active).isdigit() else 1

            image = request.files.get('image')

            image_path = None
            if image and image.filename:
                ext = image.filename.rsplit('.', 1)[-1].lower()
                if ext in current_app.config['ALLOWED_EXTENSIONS']:
                    import uuid
                    from werkzeug.utils import secure_filename

                    filename = str(uuid.uuid4()) + "_" + secure_filename(image.filename)
                    save_path = os.path.join(current_app.config['PRODUCT_UPLOAD_FOLDER'], filename)
                    image.save(save_path)
                    image_path = f"uploads/products/{filename}"

            db_utility_module.addProductToDB(
                name=name,
                description=description,
                category=category,
                price=price,
                stock=stock,
                active=active,
                image_url=image_path,
            )

            return json_success({"message": "Product added"})
        except Exception as e:
            return json_error(str(e), status_code=500)

    @api_admin.get('/orders')
    @token_required(role='admin')

    def orders_get():
        orderid = request.args.get('orderid', "").strip()
        product_name = request.args.get('productname', "").strip()
        from_date = request.args.get('fromdate', "").strip()
        to_date = request.args.get('todate', "").strip()

        orders = db_utility_module.getOrders(
            orderid=orderid,
            product_name=product_name,
            from_date=from_date,
            to_date=to_date,
        )

        normalized = []
        for o in orders:
            normalized.append({
                "id": o.get('ORDER_ID'),
                "orderId": o.get('ORDER_ID'),
                "productName": o.get('PRODUCT_NAME'),
                "date": o.get('CREATED_AT').isoformat() if o.get('CREATED_AT') else None,
                "totalPrice": float(o.get('TOTAL_PRICE')) if o.get('TOTAL_PRICE') is not None else None,
                "status": str(o.get('ORDER_STATUS')).lower() if o.get('ORDER_STATUS') else None,
            })

        return json_success({"orders": normalized, "count": len(normalized)})

    return api_admin

