import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response


    @app.route("/categories", methods=["GET"])
    def categories():
        categories = {category.id: category.type for category in Category.query.all()}

        if len(categories) == 0:
            abort(404)
    
        return jsonify({
                'success': True,
                'categories': categories
            })

    @app.route('/questions')
    def questions():

        selection = Question.query.all()
        current_questions = paginate_questions(request, selection)
        categories = {category.id: category.type for category in Category.query.all()}

        if (len(current_questions) == 0):
             abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': categories
        })

    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        try:
            question = Question.query.filter_by(id=id).one_or_none()

            if question is None:
                abort(404)
            else:
              question.delete()
              selection = Question.query.all()
              current_questions = paginate_questions(request, selection)
              categories = {category.id: category.type for category in Category.query.all()}


            return jsonify({
                'success': True,
                'deleted': id,
                'questions': current_questions,
                'total_questions': len(selection),
                'categories': categories
            })

        except:
            abort(422)

    ###

    @app.route('/questions/create', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)
        new_answer = body.get('answer', None)

        if new_question is None:
            abort(422)

        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                difficulty=new_difficulty,
                category=new_category
            )
            question.insert()

            selection = Question.query.all()
            current_questions = paginate_questions(request, selection)

            return jsonify ({
                "success": True,
                "created": question.id,
                "questions": current_questions,
                "total_questions": len(selection)
            })

        except:
            abort(422)


    @app.route('/questions/search', methods=['POST'])
    def search_questions():
      body = request.get_json()
      if 'searchTerm' in body:
                query = body['searchTerm']
                results = Question.query.filter(Question.question.ilike('%' + query + '%')).all()
                paginated = paginate_questions(request, results)
                return jsonify({
                    'success': True,
                    'questions': paginated,
                    'total_questions': len(Question.query.all()),
                    'current_category': None
                })
      else:
        abort(404)

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def category_questions(category_id):
        try:
            selection = Question.query.filter(Question.category == category_id).all()
            current_questions = paginate_questions(request, selection)
            
            if len(current_questions) == 0:
                abort(404)

            current_category = Category.query.filter(Category.id == category_id).one_or_none().format()

            return jsonify ({
                "success": True,
                "questions": current_questions,
                "total_questions": len(selection),
                "current_category": current_category
            })

        except():
            abort(404)
    

    @app.route('/quizzes', methods=['POST'])
    def play_quiz_question():
        data = request.get_json()
        previous_questions = data.get('previous_questions')
        quiz_category = data.get('quiz_category')

        if ((quiz_category is None) or (previous_questions is None)):
            abort(400)

       
        if (quiz_category['id'] == 0):
            questions = Question.query.all()
        else:
            questions = Question.query.filter_by(category=quiz_category['id']).all()

        def get_random_question():
            return questions[random.randint(0, len(questions)-1)]

        next_question = get_random_question()

        found = True

        while found:
            if next_question.id in previous_questions:
                next_question = get_random_question()
            else:
                found = False

        return jsonify({
            'success': True,
            'question': next_question.format(),
        }), 200

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad request'
        }), 400

    # Creating error handler for 404 errors
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource not found'
        }), 404

    # Creating error handler for 422 errors
    @app.errorhandler(422)
    def unable_to_process(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unable to process request'
        }), 422

  
                
    return app 