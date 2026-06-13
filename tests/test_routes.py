"""
Account API Service Test Suite
Run with:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import logging
import unittest
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status
from service.models import db, Account, init_db
from service import app, talisman

DATABASE_URI = "sqlite:///:memory:"
BASE_URL = "/accounts"
HTTPS_ENVIRON = {"wsgi.url_scheme": "https"}


class TestAccountAPIService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["TESTING"] = True
        talisman.force_https = False

    def setUp(self):
        self.client = app.test_client()

    def test_security_headers(self):
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'self'; object-src 'none'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

    def test_cors_security(self):
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "*")


class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        talisman.force_https = False
        init_db(app)

    def setUp(self):
        db.session.query(Account).delete()
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()

    def _create_accounts(self, count):
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Could not create test Account")
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize(), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

    def test_bad_request(self):
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize(), content_type="test/html")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_account(self):
        account = self._create_accounts(1)[0]
        resp = self.client.get(f"{BASE_URL}/{account.id}", content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_accounts(self):
        account1 = AccountFactory(); account1.create()
        account2 = AccountFactory(); account2.create()
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_account_list(self):
        self._create_accounts(5)
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_update_account(self):
        test_account = AccountFactory()
        resp = self.client.post(BASE_URL, json=test_account.serialize())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        new_account = resp.get_json()
        new_account["name"] = "Updated Name"
        resp = self.client.put(f"{BASE_URL}/{new_account['id']}", json=new_account)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_account(self):
        account = self._create_accounts(1)[0]
        resp = self.client.delete(f"{BASE_URL}/{account.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)