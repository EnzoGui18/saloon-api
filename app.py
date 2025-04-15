from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from config import Config
from models import db
from routes import api

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
app.mail = Mail(app)

app.register_blueprint(api, url_prefix='/api')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)