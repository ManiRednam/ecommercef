from .connection import databaseConfig


def checkUserExists(email: str) -> bool:
    db_config = databaseConfig()
    cursor = db_config.cursor()
    cursor.execute("select user_id from users where email=%s;", (email,))
    exists = bool(cursor.fetchone())
    cursor.close()
    db_config.close()
    return exists


def addUser(name: str, email: str, phone_number: str, password: str, profile_image: str = None):
    db = databaseConfig()
    cursor = db.cursor()

    query = """
        INSERT INTO users
        (NAME, EMAIL, PHONE_NUMBER, PASSWORD, PROFILE_IMAGE, ROLE)
        VALUES (%s, %s, %s, %s, %s, 'user')
    """

    cursor.execute(query, (name, email, phone_number, password, profile_image))
    db.commit()
    cursor.close()
    db.close()


def getUserDetails(email: str, role: str = None):
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)
    user_details_query = "select user_id,name, password, role from users where email = %s;"
    if role:
        user_details_query = "select user_id, password, role from users where email = %s and role = %s"
        cursor.execute(user_details_query, (email, role))
    else:
        cursor.execute(user_details_query, (email,))
    data = cursor.fetchone()
    cursor.close()
    db_config.close()
    return data


def getUserDetailsByID(user_id: int, role: str = None):
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)
    user_details_query = "select * from users where user_id = %s;"
    cursor.execute(user_details_query, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db_config.close()
    return user


def getCatagoriesFromDB():
    db_config = databaseConfig()
    cursor = db_config.cursor()
    cursor.execute("select distinct(category) from products;")
    category_list = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db_config.close()
    return category_list


def getProductsFromDB(name: str = "", category: str = "", status: str = ""):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM products WHERE 1=1"
    values = []

    if name:
        query += " AND NAME LIKE %s"
        values.append(f"%{name}%")

    if category:
        query += " AND CATEGORY = %s"
        values.append(category)

    if status is not None and status != "":
        query += " AND ACTIVE = %s"
        values.append(status)

    cursor.execute(query, values)
    products = cursor.fetchall()
    cursor.close()
    db.close()
    return products


def addProductToDB(name, description, category, price, stock, active, image_url):
    db = databaseConfig()
    cursor = db.cursor()

    product_insert_query = """
        INSERT INTO products
        (NAME, DEScrIPTION, CATEGORY, PRICE, STOCK, ACTIVE, IMAGE_URL)
        VALUES (%s,%s,%s,%s,%s,%s, %s)
    """

    cursor.execute(product_insert_query, (name, description, category, price, stock, active, image_url))
    db.commit()
    cursor.close()
    db.close()


def totalOrdersCount(status: str = None):
    db = databaseConfig()
    cursor = db.cursor()

    if status:
        cursor.execute("SELECT COUNT(*) FROM ORDERS WHERE ORDERSTATUS = %s;", (status,))
    else:
        cursor.execute("SELECT COUNT(*) FROM ORDERS;")

    orders_count = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return orders_count


def getOrders(orderid="", product_name="", from_date="", to_date=""):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT 
            o.ORDERID AS ORDER_ID,
            o.USERID AS USER_ID,
            o.CREATED_AT,
            o.ORDERSTATUS AS ORDER_STATUS,

            oi.PRODUCTNAME AS PRODUCT_NAME,
            oi.TOTALPRICE AS TOTAL_PRICE

        FROM ORDERS o
        JOIN ORDER_ITEMS oi ON o.ORDERID = oi.ORDERID
        WHERE 1=1
    """

    params = []

    if orderid:
        query += " AND o.ORDERID = %s"
        params.append(orderid)

    if product_name:
        query += " AND oi.PRODUCTNAME LIKE %s"
        params.append(f"%{product_name}%")

    if from_date:
        query += " AND DATE(o.CREATED_AT) >= %s"
        params.append(from_date)

    if to_date:
        query += " AND DATE(o.CREATED_AT) <= %s"
        params.append(to_date)

    query += " ORDER BY o.CREATED_AT DESC"

    cursor.execute(query, tuple(params))
    orders = cursor.fetchall()
    cursor.close()
    db.close()
    return orders


def usersDetails(name: str = "", email: str = "", role: str = ""):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    query = "SELECT USER_ID, NAME, EMAIL, PHONE_NUMBER, ROLE, CREATED_AT, PROFILE_IMAGE FROM USERS WHERE 1=1"
    values = []

    if name:
        query += " AND NAME LIKE %s"
        values.append(f"%{name}%")

    if email:
        query += " AND EMAIL LIKE %s"
        values.append(f"%{email}%")

    if role:
        query += " AND ROLE = %s"
        values.append(role)

    query += " ORDER BY CREATED_AT DESC"

    cursor.execute(query, values)
    users = cursor.fetchall()
    cursor.close()
    db.close()
    return users


def updateAdminProfile(user_id: int, name: str = None, phone: str = None, new_password: str = None):
    db = databaseConfig()
    cursor = db.cursor()
    fields = []
    values = []

    if name is not None:
        fields.append("NAME = %s")
        values.append(name)
    if phone is not None:
        fields.append("PHONE_NUMBER = %s")
        values.append(phone)
    if new_password is not None:
        fields.append("PASSWORD = %s")
        values.append(new_password)

    if not fields:
        cursor.close()
        db.close()
        return False

    values.append(user_id)
    cursor.execute(
        f"UPDATE USERS SET {', '.join(fields)} WHERE USER_ID = %s",
        tuple(values),
    )
    db.commit()
    cursor.close()
    db.close()
    return True


def getProductDetailsByID(productid: int):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE PRODUCTID = %s", (productid,))
    product = cursor.fetchone()
    cursor.close()
    db.close()
    return product


def updateProductInfo(name, description, category, price, stock, active, productid):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)
    update_query = """
            UPDATE products
            SET NAME=%s, DESCRIPTION=%s, CATEGORY=%s, PRICE=%s, STOCK=%s, ACTIVE=%s
            WHERE PRODUCTID=%s;
        """

    cursor.execute(update_query, (name, description, category, price, stock, active, productid))
    db.commit()
    cursor.close()
    db.close()
    return True


def updateProductStatus(productid, status: int = 0):
    db = databaseConfig()
    cursor = db.cursor()
    cursor.execute("UPDATE products SET ACTIVE = %s WHERE PRODUCTID = %s", (status, productid))
    db.commit()
    cursor.close()
    db.close()
    return True


def viewUserByAdmin(user_id):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT USER_ID, NAME, EMAIL, ROLE, STATUS, CREATED_AT 
        FROM users WHERE USER_ID = %s
        """,
        (user_id,),
    )
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user


def viewOrderDetails(order_id):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM ORDERS WHERE ORDERID = %s", (order_id,))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        db.close()
        return None, []

    cursor.execute(
        """
        SELECT PRODUCTNAME, PRODUCTPRICE, QUANTITY, TOTALPRICE
        FROM ORDER_ITEMS
        WHERE ORDERID = %s
        """,
        (order_id,),
    )
    items = cursor.fetchall()

    cursor.close()
    db.close()
    return order, items


def totalProducts():
    db = databaseConfig()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM PRODUCTS;")
    total = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return total


def getProductById(productid: int):
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PRODUCTS WHERE PRODUCTID=%s;", (productid,))
    product = cursor.fetchone()
    cursor.close()
    db_config.close()
    return product


def getProductsByCategory(category_name, min_price, max_price, sort):
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)
    query = "SELECT * FROM PRODUCTS WHERE category=%s AND ACTIVE=1"
    params = [category_name]

    if min_price is not None and min_price != "":
        query += " AND PRICE >= %s"
        params.append(min_price)

    if max_price is not None and max_price != "":
        query += " AND PRICE <= %s"
        params.append(max_price)

    if sort == "low":
        query += " ORDER BY PRICE ASC"
    elif sort == "high":
        query += " ORDER BY PRICE DESC"
    else:
        query += " ORDER BY PRODUCTID DESC"

    cursor.execute(query, tuple(params))
    products = cursor.fetchall()
    cursor.close()
    db_config.close()
    return products


def toggleProduct(pid, status):
    db = databaseConfig()
    cursor = db.cursor()
    cursor.execute("UPDATE products SET ACTIVE=%s WHERE PRODUCTID=%s", (status, pid))
    db.commit()
    cursor.close()
    db.close()
