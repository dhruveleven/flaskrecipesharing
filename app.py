#ALL REQUIRED IMPORTS
from flask import Flask,render_template,request,redirect,url_for,flash,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user,login_required, current_user
from werkzeug.security import generate_password_hash,check_password_hash
from flask_redis import FlaskRedis

#INITIALIZING APP
app = Flask(__name__)
app.config['SECRET_KEY'] = 'abc'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = FlaskRedis(host='localhost',port=6379,db=0)
db = SQLAlchemy(app)

#LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

#USER MODEL
class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(50),unique=True,nullable=False)
    password_hash = db.Column(db.String(100),nullable=False)

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)
    
#RECIPE MODEL
class Recipe(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100),nullable=False)
    ingredients = db.Column(db.Text,nullable=False)
    instructions = db.Column(db.Text,nullable=False)

    chef_name = db.Column(db.String(100), nullable=False)  # New field
    cuisine = db.Column(db.String(50), nullable=False)  # New field

    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)

#Flask-Login Callback to Load User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#ROUTES
@app.route('/')
def index():
    return render_template('index.html')

#LOGIN ROUTE
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!','success')
            return redirect(url_for('options'))
        else:
            flash('Invalid username or password!','error')
            return redirect(url_for('create_account'))
    return render_template('login.html')

#CREATE ACCOUNT ROUTE
@app.route('/create_account',methods=['GET','POST'])
def create_account():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. PLease choose a different username.','error')
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please login','success')
            return redirect(url_for('login'))
    return render_template('create_account.html')

#LOGOUT ROUTE
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!','success')
    return redirect(url_for('index'))

#OPTIONS ROUTE
@app.route('/options')
@login_required
def options():
    return render_template('options.html')

#RECIPES ROUTE
@app.route('/recipes', methods=['GET', 'POST'])
@login_required
def recipes():
    search_query = request.args.get('q', '')
    if search_query:
        recipes = Recipe.query.filter(Recipe.title.contains(search_query) | Recipe.ingredients.contains(search_query)).all()
    else:
        recipes = Recipe.query.all()
    return render_template('recipes.html', recipes=recipes)

#CREATE NEW RECIPE ROUTE
@app.route('/recipe/create',methods=['GET','POST'])
@login_required 
def create_recipe():
    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        chef_name = request.form['chef_name'] 
        cuisine = request.form['cuisine']
        recipe = Recipe(title=title,ingredients=ingredients,instructions=instructions,chef_name=chef_name,cuisine=cuisine,user_id=current_user.id)
        db.session.add(recipe)
        db.session.commit()
        flash('Recipe created successfully!','success')
        return redirect(url_for('recipes'))
    return render_template('create_recipe.html')

#RECIPE DETAILS ROUTE
@app.route('/recipe/<int:recipe_id>')
@login_required
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('recipe_detail.html',recipe=recipe)

#MY_RECIPE DETAILS ROUTE
@app.route('/myrecipedeets/<int:recipe_id>')
@login_required
def my_recipes_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('my_recipes_detail.html',recipe=recipe)

#MY_RECIPES ROUTE
@app.route('/my_recipes')
@login_required
def my_recipes():
    my_recipes = Recipe.query.filter_by(user_id=current_user.id)
    return render_template('my_recipes.html',recipes=my_recipes)

#DELETE RECIPE ROUTE
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    del_recipe = Recipe.query.get_or_404(id)
    try:
        db.session.delete(del_recipe)
        db.session.commit()
        return redirect('/my_recipes')
    except:
        return "There was an error deleting your recipe!"

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)




