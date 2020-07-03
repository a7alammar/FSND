import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


db_drop_and_create_all()

## ROUTES

@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()

    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks]
    }), 200


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()

    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in drinks]
    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    req = request.get_json()

    new_title = req.get('title', None)
    new_recipe = json.dumps(req.get('recipe', None))

    drink = Drink(
        title=new_title,
        recipe=new_recipe
    )

    drink.insert()

    return jsonify({
        "success": True,
        "drinks": [drink.long()]
    })

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    req = request.get_json()

    drink = Drink.query.filter_by(id=id).first()

    if drink is None:
        abort(404)

    if req.get('title', None) is not None:
        drink.title = req.get('title', None)

    if req.get('recipe', None) is not None:
        drink.recipe = json.dumps(req.get('recipe', None))

    drink.update()

    return jsonify({
        "success": True,
        "drinks": [drink.long()]
    })

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if drink is None:
        abort(404)

    try:
        drink.delete()
    except Exception:
        abort(400)

    return jsonify({'success': True, 'deleted': id}), 200

## Error Handling

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": 'Bad Request'
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": 'Unathorized'
    }), 401

@app.errorhandler(403)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": 'Forbidden'
    }), 403


@app.errorhandler(404)
def not_found(error):
    jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
         "success": False,
         "error": 422,
         "message": "unprocessable"
    }), 422


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code