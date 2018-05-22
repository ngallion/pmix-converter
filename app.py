from flask import Flask
from flask_sqlalchemy import SQLAlchemy


UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['.csv'])


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://pmix-converter:whichwich@localhost:8889/pmix-converter'
# 'mysql+pymysql://ngallion:ndg0000086192@ngallion.mysql.pythonanywhere-services.com/pmix-converter'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "axbxcd98"