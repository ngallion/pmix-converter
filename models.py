from app import db

class Association(db.Model):
    __tablename__ = 'association'
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    quantity = db.Column(db.Float)
    recipe = db.relationship("Recipe")
    ingredient = db.relationship("Ingredient")
    user = db.relationship("User")

    def __init__(self,ingredient_id,recipe_id,user_id,quantity):
        self.ingredient_id = ingredient_id
        self.recipe_id = recipe_id
        self.user_id = user_id
        self.quantity = quantity

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    ingredients = db.relationship("Association")
    recipes = db.relationship("Association")

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Recipe(db.Model):
    __tablename__='recipe'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    ingredients = db.relationship("Association")
    user = db.relationship("Association")

    def __init__(self, name):
        self.name = name

class Ingredient(db.Model):
    __tablename__='ingredient'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    recipes = db.relationship("Association")
    user = db.relationship("Association")

    def __init__(self, name):
        self.name = name
