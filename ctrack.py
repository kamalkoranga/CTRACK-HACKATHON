import os
from app import create_app
from app import db
from app.models import User, Post
from flask import jsonify
from flask_migrate import Migrate

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.route('/system_status', methods=['GET'])
def system_status():
    return jsonify({'message': "System is running properly ✅"}), 200


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Post=Post)


if __name__ == '__main__':
    app.run()
