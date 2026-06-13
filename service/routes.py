"""
Routes for the Account API Service
"""
from flask import jsonify, request, abort
from service.models import Account
from service.common import status
from . import app


@app.after_request
def add_security_headers(response):
    # Security headers
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self'; object-src 'none'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # CORS header
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/")
def index():
    return jsonify({"message": "Welcome to the Account API Service"}), status.HTTP_200_OK


@app.route("/health")
def health():
    return jsonify({"status": "OK"}), status.HTTP_200_OK


@app.route("/accounts", methods=["POST"])
def create_account():
    if request.content_type != "application/json":
        abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Content-Type must be application/json")
    data = request.get_json()
    if not data or "name" not in data or "email" not in data:
        abort(status.HTTP_400_BAD_REQUEST, "Invalid account data")
    account = Account()
    account.deserialize(data)
    account.create()
    response = jsonify(account.serialize())
    response.status_code = status.HTTP_201_CREATED
    response.headers["Location"] = f"/accounts/{account.id}"
    return response


@app.route("/accounts", methods=["GET"])
def list_accounts():
    accounts = Account.all()
    return jsonify([a.serialize() for a in accounts]), status.HTTP_200_OK


@app.route("/accounts/<int:account_id>", methods=["GET"])
def get_account(account_id):
    account = Account.find(account_id)
    if not account:
        abort(status.HTTP_404_NOT_FOUND, f"Account with id {account_id} not found")
    return jsonify(account.serialize()), status.HTTP_200_OK


@app.route("/accounts/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    account = Account.find(account_id)
    if not account:
        abort(status.HTTP_404_NOT_FOUND, f"Account with id {account_id} not found")
    data = request.get_json()
    account.deserialize(data)
    account.update()
    return jsonify(account.serialize()), status.HTTP_200_OK


@app.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    account = Account.find(account_id)
    if account:
        account.delete()
    return "", status.HTTP_204_NO_CONTENT

