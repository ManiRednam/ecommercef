from .connection import databaseConfig


def getProductsByCategory(category_name, min_price, max_price, sort):
    # kept for backward-compat; imported from app.py userutility
    from .utility import getProductsByCategory as _impl

    return _impl(category_name, min_price, max_price, sort)


def getProductById(productid: int):
    from .utility import getProductById as _impl

    return _impl(productid)


def getCartItem(user_id, product_id):
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT * FROM CART
        WHERE USER_ID = %s AND PRODUCTID = %s;
        """,
        (user_id, product_id),
    )
    result = cursor.fetchone()

    cursor.close()
    db_config.close()
    return result


def increaseCartQuantity(user_id, product_id):
    db_config = databaseConfig()
    cursor = db_config.cursor()

    query = """
        UPDATE CART
        SET QUANTITY = QUANTITY + 1,
            UPDATED_AT = CURRENT_TIMESTAMP
        WHERE USER_ID = %s AND PRODUCTID = %s;
    """

    cursor.execute(query, (user_id, product_id))
    db_config.commit()
    cursor.close()
    db_config.close()


def insertCartItem(user_id, product_id, price):
    db_config = databaseConfig()
    cursor = db_config.cursor()

    query = """
        INSERT INTO CART (USER_ID, PRODUCTID, QUANTITY, PRICE)
        VALUES (%s, %s, 1, %s);
    """

    cursor.execute(query, (user_id, product_id, price))
    db_config.commit()
    cursor.close()
    db_config.close()


def getUserCartItems(user_id):
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)

    query = """
        SELECT 
            C.CARTID,
            C.PRODUCTID,
            P.NAME,
            P.IMAGE_URL,
            C.QUANTITY,
            C.PRICE,
            (C.QUANTITY * C.PRICE) AS TOTAL_PRICE
        FROM CART C
        JOIN PRODUCTS P ON C.PRODUCTID = P.PRODUCTID
        WHERE C.USER_ID = %s;
    """

    cursor.execute(query, (user_id,))
    results = cursor.fetchall()

    cursor.close()
    db_config.close()
    return results


def removeFromCart(user_id: int, product_id: int):
    db_config = databaseConfig()
    cursor = db_config.cursor()

    query = """
        DELETE FROM CART
        WHERE USER_ID = %s AND PRODUCTID = %s;
    """

    cursor.execute(query, (user_id, product_id))
    db_config.commit()
    cursor.close()
    db_config.close()


def updateCartQuantity(quantity: int, user_id: int, product_id: int):
    db_config = databaseConfig()
    cursor = db_config.cursor()

    query = """
        UPDATE CART
        SET QUANTITY = %s,
            UPDATED_AT = CURRENT_TIMESTAMP
        WHERE USER_ID = %s AND PRODUCTID = %s;
    """

    cursor.execute(query, (quantity, user_id, product_id))
    db_config.commit()
    cursor.close()
    db_config.close()


def getProductsBasedOnSearch(product_name: str):
    db_config = databaseConfig()
    cursor = db_config.cursor(dictionary=True)
    cursor.execute("select * from products where name like %s;", (f"%{product_name}%",))
    products = cursor.fetchall()
    cursor.close()
    db_config.close()
    return products


def getCartItems(user_id):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT p.NAME,
                p.PRODUCTID,
                p.PRICE,
                c.QUANTITY,
                (p.PRICE * c.QUANTITY) AS TOTAL
        FROM CART c
        JOIN PRODUCTS p ON c.PRODUCTID = p.PRODUCTID
        WHERE c.USER_ID = %s
    """

    cursor.execute(query, (user_id,))
    cart_items = cursor.fetchall()

    total_amount = sum(item["TOTAL"] for item in cart_items)

    cursor.close()
    db.close()
    return total_amount, cart_items


def placeOrder(user_id, fullname, phone, address, city, pincode, total_amount, cart_items):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        INSERT INTO ORDERS (USERID, FULLNAME, PHONE, ADDRESS, CITY, PINCODE,TOTAL_AMOUNT)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, fullname, phone, address, city, pincode, total_amount))

    order_id = cursor.lastrowid

    for item in cart_items:
        cursor.execute(
            """
            INSERT INTO ORDER_ITEMS
            (ORDERID, PRODUCTID, PRODUCTNAME, PRODUCTPRICE, QUANTITY)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (order_id, item["PRODUCTID"], item["NAME"], item["PRICE"], item["QUANTITY"]),
        )

    cursor.execute("DELETE FROM CART WHERE USER_ID=%s", (user_id,))

    for item in cart_items:
        cursor.execute("select STOCK from products where productid = %s", (item["PRODUCTID"],))
        row = cursor.fetchone()
        current_quantity = row["STOCK"] if row else 0
        if current_quantity >= item["QUANTITY"]:
            cursor.execute(
                "update products set STOCK = STOCK - %s WHERE PRODUCTID = %s",
                (item["QUANTITY"], item["PRODUCTID"]),
            )
        else:
            db.rollback()
            cursor.close()
            db.close()
            return False, f"{item['NAME']} avalilabe quantity is {current_quantity}"

    db.commit()
    cursor.close()
    db.close()
    return True, "Success"


def myOrders(user_id):
    db = databaseConfig()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT * FROM ORDERS
        WHERE USERID = %s
        ORDER BY CREATED_AT DESC
        """,
        (user_id,),
    )

    orders = cursor.fetchall()
    cursor.close()
    db.close()
    return orders

