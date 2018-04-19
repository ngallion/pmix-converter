import csv
from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://pmix-converter:whichwich@localhost:8889/pmix-converter'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "axbxcd98"

# class User(db.Model):
    
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(120), unique=True)
#     password = db.Column(db.String(120))

#     def __init__(self, username, password):
#         self.username = username
#         self.password = password

class Association(db.Model):
    __tablename__ = 'association'
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
    quantity = db.Column(db.Float)
    recipe = db.relationship("Recipe")
    ingredient = db.relationship("Ingredient")

    def __init__(self,ingredient_id,recipe_id,quantity):
        self.ingredient_id = ingredient_id
        self.recipe_id = recipe_id
        self.quantity = quantity

class Recipe(db.Model):
    __tablename__='recipe'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    ingredients = db.relationship("Association")

    def __init__(self, name):
        self.name = name

class Ingredient(db.Model):
    __tablename__='ingredient'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    recipes = db.relationship("Association")

    def __init__(self, name):
        self.name = name

@app.route('/', methods=['POST','GET'])
def index():
    return render_template('index.html')

@app.route('/csvviewer', methods=['POST','GET'])
def csvviewer():
    
    return render_template('csvviewer.html',product_list=product_list)

@app.route('/search', methods=['POST'])
def search():
    search = request.form['search']

    filtered_product_list = []
    
    for product in product_list:
        if product[0].find(search) != -1:
            filtered_product_list.append(product)
    
    return render_template('csvviewer.html',product_list=filtered_product_list)
 



@app.route('/add-ingredient', methods=['POST'])
def add_ingredient():
    ingredient = request.form['ingredient']
    recipe = request.form['recipe']
    
    existing_recipe = Recipe.query.filter_by(name=recipe).first()
    if not existing_recipe:
        new_recipe = Recipe(recipe)
        db.session.add(new_recipe)
    

    existing_ingredient = Ingredient.query.filter_by(name=ingredient).first()
    if not existing_ingredient:
        new_ingredient = Ingredient(ingredient)
        db.session.add(new_ingredient)

    db.session.commit()

    quantity = request.form['quantity']
    ingredient_id = Ingredient.query.filter_by(name=ingredient).first().id
    recipe_id = Recipe.query.filter_by(name=recipe).first().id

    existing_association = Association.query.filter_by(ingredient_id=ingredient_id,recipe_id=recipe_id).first()
    
    if not existing_association:
        new_association = Association(ingredient_id,recipe_id,quantity)
        db.session.add(new_association)
        db.session.commit()
        flash("ingredient added")
    else:
        flash("recipe already contains this ingredient")

    return redirect('/csvviewer')

product_list = []
pmix = "pmix.csv"

def pmix_to_list(pmix):
    with open(pmix, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        
        next(csv_reader)

        for line in csv_reader:
            product_list.append((line[1], line[5]))

pmix_to_list(pmix)

if __name__ == '__main__':
    app.run()


