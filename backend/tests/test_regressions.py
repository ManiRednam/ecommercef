import sys
from pathlib import Path
import unittest
from unittest.mock import patch


BACKEND_DIR = str(Path(__file__).resolve().parents[1])
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import jwt
import app as app_module
from database import utility, userutility


class FakeCursor:
    def __init__(self, rowcount=1, one=None, many=None):
        self.rowcount = rowcount
        self.lastrowid = 99
        self.one = one
        self.many = many or []
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.many

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, **kwargs):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class RegressionTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True, DEBUG=True)
        self.client = app_module.app.test_client()

    def set_admin_cookie(self, role="admin"):
        token = jwt.encode(
            {"user_id": 1, "role": role},
            app_module.app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        self.client.set_cookie("token", token)

    def test_app_factory_registers_admin_api_once(self):
        created_app = app_module.create_app()
        product_post_rules = [
            rule
            for rule in created_app.url_map.iter_rules()
            if rule.rule == "/api/admin/products" and "POST" in rule.methods
        ]
        order_get_rules = [
            rule
            for rule in created_app.url_map.iter_rules()
            if rule.rule == "/api/admin/orders" and "GET" in rule.methods
        ]
        self.assertEqual(len(product_post_rules), 1)
        self.assertEqual(len(order_get_rules), 1)
        self.assertEqual(
            created_app.config["PRODUCT_UPLOAD_FOLDER"],
            str(Path(created_app.static_folder) / "uploads" / "products"),
        )

    def test_admin_api_checks_role_inside_request_context(self):
        response = self.client.get("/api/admin/dashboard")
        self.assertEqual(response.status_code, 302)

        self.set_admin_cookie(role="user")
        response = self.client.get("/api/admin/dashboard")
        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_succeeds_for_admin_token(self):
        self.set_admin_cookie()
        with (
            patch.object(app_module.db_utility_module, "totalProducts", return_value=3),
            patch.object(app_module.db_utility_module, "totalOrdersCount", side_effect=[8, 2]),
            patch.object(app_module.db_utility_module, "usersDetails", return_value=[{}]),
        ):
            response = self.client.get("/api/admin/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["stats"][0]["value"], 3)

    def test_public_user_insert_explicitly_uses_user_role(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        with patch.object(utility, "databaseConfig", return_value=connection):
            utility.addUser("New User", "user@example.test", "123", "hash")

        self.assertIn("'user'", cursor.executed[0][0])

    def test_inactive_product_filter_keeps_zero_status(self):
        cursor = FakeCursor(many=[])
        connection = FakeConnection(cursor)
        with patch.object(utility, "databaseConfig", return_value=connection):
            utility.getProductsFromDB(status=0)

        query, params = cursor.executed[0]
        self.assertIn("ACTIVE = %s", query)
        self.assertEqual(params, [0])

    def test_order_status_count_uses_requested_status(self):
        cursor = FakeCursor(one=(2,))
        connection = FakeConnection(cursor)
        with patch.object(utility, "databaseConfig", return_value=connection):
            count = utility.totalOrdersCount(status="PENDING")

        query, params = cursor.executed[0]
        self.assertIn("ORDERSTATUS = %s", query)
        self.assertEqual(params, ("PENDING",))
        self.assertEqual(count, 2)

    def test_profile_update_builds_only_requested_fields(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        with patch.object(utility, "databaseConfig", return_value=connection):
            updated = utility.updateAdminProfile(
                user_id=7,
                name="Updated Name",
                phone="555",
                new_password="hash",
            )

        query, params = cursor.executed[0]
        self.assertIn("NAME = %s", query)
        self.assertIn("PHONE_NUMBER = %s", query)
        self.assertIn("PASSWORD = %s", query)
        self.assertEqual(params, ("Updated Name", "555", "hash", 7))
        self.assertTrue(updated)

    def test_cart_quantity_must_be_positive(self):
        with patch.object(userutility, "databaseConfig") as database_config:
            with self.assertRaises(ValueError):
                userutility.updateCartQuantity(0, user_id=1, product_id=2)

        database_config.assert_not_called()

    def test_cart_update_is_bounded_by_stock_and_active_status(self):
        cursor = FakeCursor(rowcount=0)
        connection = FakeConnection(cursor)
        with patch.object(userutility, "databaseConfig", return_value=connection):
            updated = userutility.updateCartQuantity(4, user_id=1, product_id=2)

        query, params = cursor.executed[0]
        self.assertIn("%s <= P.STOCK AND P.ACTIVE = 1", query)
        self.assertEqual(params, (4, 1, 2, 4))
        self.assertFalse(updated)

    def test_order_stock_decrement_is_atomic(self):
        cursor = FakeCursor(rowcount=1)
        connection = FakeConnection(cursor)
        items = [
            {
                "PRODUCTID": 2,
                "NAME": "Item",
                "PRICE": 10,
                "QUANTITY": 3,
            }
        ]
        with patch.object(userutility, "databaseConfig", return_value=connection):
            placed, _ = userutility.placeOrder(1, "Name", "123", "Address", "City", "00000", 30, items)

        stock_update = next(call for call in cursor.executed if "SET STOCK = STOCK - %s" in call[0])
        self.assertIn("STOCK >= %s AND ACTIVE = 1", stock_update[0])
        self.assertEqual(stock_update[1], (3, 2, 3))
        self.assertTrue(placed)
        self.assertTrue(connection.committed)

    def test_order_rolls_back_when_inventory_is_insufficient(self):
        cursor = FakeCursor(rowcount=0, one={"STOCK": 2})
        connection = FakeConnection(cursor)
        items = [
            {
                "PRODUCTID": 2,
                "NAME": "Item",
                "PRICE": 10,
                "QUANTITY": 3,
            }
        ]
        with patch.object(userutility, "databaseConfig", return_value=connection):
            placed, message = userutility.placeOrder(1, "Name", "123", "Address", "City", "00000", 30, items)

        self.assertFalse(placed)
        self.assertIn("available quantity is 2", message)
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)

    def test_user_orders_and_placeholder_routes_are_protected(self):
        for route in ("/my-orders", "/user/categories", "/users/orders", "/user/cart"):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 302)

    def test_product_detail_route_parameter_names_match(self):
        response = self.client.get("/user/products/electronics/7")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "Product Info")

    def test_checkout_order_uses_database_user_id(self):
        self.set_admin_cookie(role="user")
        with (
            patch.object(app_module, "getUserByToken", return_value={"USER_ID": 23}),
            patch.object(app_module, "getCartItems", return_value=(12, [{"PRODUCTID": 5}])),
            patch.object(app_module, "placeOrder", return_value=(True, "Success")) as place_order,
        ):
            response = self.client.post(
                "/user/place-order",
                data={
                    "fullname": "Customer",
                    "phone": "123",
                    "address": "1 Main Street",
                    "city": "Town",
                    "pincode": "00000",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(place_order.call_args.args[0], 23)

    def test_add_to_cart_uses_database_user_id(self):
        self.set_admin_cookie(role="user")
        product = {"PRODUCTID": 5, "ACTIVE": 1, "STOCK": 4, "PRICE": 12}
        with (
            patch.object(app_module, "getUserByToken", return_value={"USER_ID": 23}),
            patch.object(app_module, "getProductById", return_value=product),
            patch.object(app_module, "getCartItem", return_value=None),
            patch.object(app_module, "insertCartItem") as insert_cart_item,
        ):
            response = self.client.post("/add-to-cart", data={"product_id": "5"})

        self.assertEqual(response.status_code, 302)
        insert_cart_item.assert_called_once_with(23, 5, 12)

    def test_admin_profile_update_uses_user_id_and_profile_fields(self):
        self.set_admin_cookie()
        with (
            patch.object(app_module, "getUserByToken", return_value={"USER_ID": 9}),
            patch.object(app_module, "updateAdminProfile") as update_profile,
        ):
            response = self.client.post(
                "/admin/profile",
                data={"name": "Admin Name", "phone": "555"},
            )

        self.assertEqual(response.status_code, 302)
        update_profile.assert_called_once_with(user_id=9, name="Admin Name", phone="555")


if __name__ == "__main__":
    unittest.main()
