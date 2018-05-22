import csv
import os
from flask import request, redirect, render_template, session, flash
from app import app, db
from models import Recipe, Association, Ingredient
from werkzeug.utils import secure_filename


product_list = []


#Allows templates to run functions
@app.context_processor
def utility_processor():
    #Check if name is in recipe table, returns boolean
    def is_recipe(recipe_name):
        recipe = Recipe.query.filter_by(name=recipe_name).first()
        if recipe:
            association = Association.query.filter_by(recipe_id=recipe.id).first()
            if association:
                return True
            else:
                return False
    
    #Gets collection of recipes given an ingredient
    def get_recipes(ingredient_name):
        ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
        if ingredient:
            associations = Association.query.filter_by(ingredient_id=ingredient.id).all()
            recipes = []
            for association in associations:
                recipe = Recipe.query.filter_by(id=association.recipe_id).first()
                recipes.append((recipe.name, association.quantity))
            
            return recipes
    #removes spaces from string to allow unique html elements
    def remove_spaces(string):
        return string.replace(" ", "")
    return dict(is_recipe=is_recipe, get_recipes=get_recipes, remove_spaces=remove_spaces)
    

@app.route('/')
def index():
    return redirect('/upload')

@app.route('/upload', methods=['POST','GET'])
def upload():
    return render_template('upload.html')

#handles requests from upload file
@app.route('/upload-file', methods=['POST','GET'])
def upload_file():
    #saves an uploaded CSV file to uploads directory, then converts to product list
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

#uploads preset sample, converts to list
@app.route('/upload-sample', methods=['POST','GET'])
def upload_sample():
    if request.method == "POST":
        global product_list
        product_list = []

        pmix_to_list('./static/sample-pmix.csv') #url_for('static',filename='styles/main.css'
        flash("Pmix uploaded")

        return redirect('/pmix-viewer')

    else:
        flash("didnt work")
        return redirect('/')

@app.route('/pmix-viewer', methods=['POST','GET'])
def pmix_viewer():
    
    session['search'] = product_list

    return render_template('pmix-viewer.html',product_list=product_list)

#handles requests from /search
@app.route('/search', methods=['POST'])
def search():
    search = request.form['search']
    
    filtered_product_list = []
    
    #generates new product list filtered by search terms

    for product in product_list:
        lowercase_name = product[0].lower()
        if lowercase_name.find(search.lower()) != -1:
            filtered_product_list.append(product)
    
    session['search'] = filtered_product_list

    return render_template('pmix-viewer.html',product_list=filtered_product_list)

#handles requests to /view-ingredients
@app.route('/view-ingredients')
def view_ingredients():

    #gets recipe objects
    recipe_name = request.args.get('recipe')

    recipe = Recipe.query.filter_by(name=recipe_name).first()

    #redirects and displays message if no ingredients are added
    if not recipe:
        flash("Recipe does not contain any ingredients", category='error')
        if session['search']:
            return render_template('pmix-viewer.html',product_list=session['search'])
        else:
            return render_template('pmix-viewer.html', product_list=product_list)

    ingredient_list = []

    #checks association table to get ingredients that are in a given recipe
    association_list = Association.query.filter_by(recipe_id=recipe.id).all()

    for association in association_list:
        ingredient = Ingredient.query.filter_by(id=association.ingredient_id).first()
        ingredient_list.append((ingredient.name, association.quantity))
    
    if ingredient_list != []:
        return render_template('view-ingredients.html', ingredient_list=ingredient_list, recipe=recipe_name)
    else:
        return render_template('view-ingredients.html', recipe_name="No ingredients added :(")


#handles requests from /delete-ingredient, allows deletion of ingredients from recipes
@app.route('/delete-ingredient', methods=['POST','GET'])
def delete_ingredient():
    ingredient_name = request.form["ingredient_name"]
    recipe_name = request.form["recipe_name"]

    ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
    recipe = Recipe.query.filter_by(name=recipe_name).first()

    association = Association.query.filter_by(ingredient_id=ingredient.id,
        recipe_id=recipe.id).first()

    #deletes ingredient from association table, but leaves ingredient on ingredient table
    db.session.delete(association)
    db.session.commit()

    ingredient_list = []

    association_list = Association.query.filter_by(recipe_id=recipe.id).all()
    for association in association_list:
        ingredient = Ingredient.query.filter_by(id=association.ingredient_id).first()
        ingredient_list.append((ingredient.name, association.quantity))

    flash("Recipe deleted")

    return render_template('view-ingredients.html', recipe=recipe_name, ingredient_list=ingredient_list)

#handles product conversion request--where the magic happens
@app.route('/view-product', methods=['POST','GET'])
def view_product():
    #create lists of product, and list of recipes not used
    product_not_converted = []
    product_converted = []

    #gets all ingredients, adds to product converted
    ingredient_list = Ingredient.query.all()
    for ingredient in ingredient_list:
        product_converted.append([ingredient.name, 0])

    #checks if ingredient has recipe, if not, adds to product not converted
    #if it has recipe, multiplies pmix quantity x recipe quantity to obtain product quantity and adds to list
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
    
    #cuts decimals short to prevent float errors from displaying
    for item in product_converted:
        item[1]= format(item[1], '.2f')


    return render_template('view-product.html', product_converted=product_converted, product_not_converted=product_not_converted)

#handles requests to add ingredients
@app.route('/add-ingredient', methods=['POST'])
def add_ingredient():
    ingredient = request.form['ingredient'].lower()
    recipe = request.form['recipe'].lower()
    
    #checks if recipe exists, if not, adds to db
    existing_recipe = Recipe.query.filter_by(name=recipe).first()
    if not existing_recipe:
        new_recipe = Recipe(recipe)
        db.session.add(new_recipe)
    
    #checks if ingredient exists, if not, adds to db
    existing_ingredient = Ingredient.query.filter_by(name=ingredient).first()
    if not existing_ingredient:
        new_ingredient = Ingredient(ingredient)
        db.session.add(new_ingredient)

    db.session.commit()

    #gets quantity from form, and corresponding recipe and ingredient ids
    quantity = request.form['quantity']
    ingredient_id = Ingredient.query.filter_by(name=ingredient).first().id
    recipe_id = Recipe.query.filter_by(name=recipe).first().id

    #grabs potential preexisting association
    existing_association = Association.query.filter_by(ingredient_id=ingredient_id,recipe_id=recipe_id).first()
    
    #adds recipe to association table if recipe does not already exist
    if not existing_association:
        new_association = Association(ingredient_id,recipe_id,quantity)
        db.session.add(new_association)
        db.session.commit()
        flash("ingredient added")
    else:
        flash("recipe already contains this ingredient")

    #returns to pmix view--if coming from searched list, returns to same filtered list
    if session['search'] != []:
        return render_template('pmix-viewer.html', product_list=session['search'])
    else:
        return render_template('pmix-viewer.html', product_list=product_list)


#uses csv reader to read in csv file and convert to list based on predetermined columns
def pmix_to_list(pmix):
    with open(pmix, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        
        next(csv_reader)

        for line in csv_reader:
            product_list.append((line[1], line[5]))

if __name__ == '__main__':
    app.run()


