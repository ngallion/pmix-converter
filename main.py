import csv
import os
from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

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

product_list = []

@app.context_processor
def utility_processor():
    def is_recipe(recipe_name):
        recipe = Recipe.query.filter_by(name=recipe_name).first()
        if recipe:
            association = Association.query.filter_by(recipe_id=recipe.id).first()
            if association:
                return True
            else:
                return False
    return dict(is_recipe=is_recipe)
    

@app.route('/')
def index():
    return redirect('/upload')

@app.route('/upload', methods=['POST','GET'])
def upload():
    return render_template('upload.html')

@app.route('/upload-file', methods=['POST','GET'])
def upload_file():
    if request.method == "POST":
        global product_list
        file = request.files['fileupload']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        product_list = []

        pmix_to_list('./uploads/' + filename)
        flash("Pmix uploaded")

        return redirect('/pmix-viewer')

    else:
        flash("didnt work")
        return redirect('/')

@app.route('/pmix-viewer', methods=['POST','GET'])
def pmix_viewer():
    
    session['search'] = product_list

    return render_template('pmix-viewer.html',product_list=product_list)

@app.route('/search', methods=['POST'])
def search():
    search = request.form['search']

    
    filtered_product_list = []
    
    for product in product_list:
        lowercase_name = product[0].lower()
        if lowercase_name.find(search.lower()) != -1:
            filtered_product_list.append(product)
    
    session['search'] = filtered_product_list

    return render_template('pmix-viewer.html',product_list=filtered_product_list)
 
@app.route('/view-ingredients')
def view_ingredients():
    recipe_name = request.args.get('recipe')

    recipe = Recipe.query.filter_by(name=recipe_name).first()

    if not recipe:
        flash("Recipe does not contain any ingredients", category='error')
        if session['search']:
            return render_template('pmix-viewer.html',product_list=session['search'])
        else:
            return render_template('pmix-viewer.html', product_list=product_list)

    ingredient_list = []

    association_list = Association.query.filter_by(recipe_id=recipe.id).all()

    for association in association_list:
        ingredient = Ingredient.query.filter_by(id=association.ingredient_id).first()
        ingredient_list.append((ingredient.name, association.quantity))
    
    if ingredient_list != []:
        return render_template('view-ingredients.html', ingredient_list=ingredient_list, recipe=recipe_name)
    else:
        return render_template('view-ingredients.html', recipe_name="No ingredients added :(")


@app.route('/delete-ingredient', methods=['POST','GET'])
def delete_ingredient():
    ingredient_name = request.form["ingredient_name"]
    recipe_name = request.form["recipe_name"]

    ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
    recipe = Recipe.query.filter_by(name=recipe_name).first()

    association = Association.query.filter_by(ingredient_id=ingredient.id,
        recipe_id=recipe.id).first()

    db.session.delete(association)
    db.session.commit()

    ingredient_list = []

    association_list = Association.query.filter_by(recipe_id=recipe.id).all()
    for association in association_list:
        ingredient = Ingredient.query.filter_by(id=association.ingredient_id).first()
        ingredient_list.append((ingredient.name, association.quantity))

    flash("Recipe deleted")

    return render_template('view-ingredients.html', recipe=recipe_name, ingredient_list=ingredient_list)

@app.route('/view-product', methods=['POST','GET'])
def view_product():
    product_not_converted = []
    product_converted = []
    ingredient_list = Ingredient.query.all()
    for ingredient in ingredient_list:
        product_converted.append([ingredient.name, 0])

    for product,quantity in product_list:
        recipe = Recipe.query.filter_by(name=product).first()
        if not recipe:
            product_not_converted.append(product)
        else:
            association_list = Association.query.filter_by(recipe_id=recipe.id).all()
            for association in association_list:
                ingredient = Ingredient.query.filter_by(id=association.ingredient_id).first()
                for item in product_converted:
                    if item[0] == ingredient.name:
                        item[1] += (association.quantity * float(quantity))
    
    return render_template('view-product.html', product_converted=product_converted, product_not_converted=product_not_converted)


@app.route('/add-ingredient', methods=['POST'])
def add_ingredient():
    ingredient = request.form['ingredient'].lower()
    recipe = request.form['recipe'].lower()
    
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

    if session['search'] != []:
        return render_template('pmix-viewer.html', product_list=session['search'])
    else:
        return render_template('pmix-viewer.html', product_list=product_list)


def pmix_to_list(pmix):
    with open(pmix, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        
        next(csv_reader)

        for line in csv_reader:
            product_list.append((line[1], line[5]))

if __name__ == '__main__':
    app.run()


