from flask import Flask, request, render_template, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

# Modèle Transaction (Revenu/Dépense)
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # "revenu" ou "dépense"
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid user')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['email']).first()
    transactions = Transaction.query.filter_by(user_id=user.id).all()

    total_revenu = sum(t.amount for t in transactions if t.type == "revenu")
    total_depense = sum(t.amount for t in transactions if t.type == "dépense")
    solde = total_revenu - total_depense

    return render_template('dashboard.html', user=user, transactions=transactions, solde=solde)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'email' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['email']).first()
    type_transaction = request.form['type']
    amount = float(request.form['amount'])
    description = request.form['description']

    new_transaction = Transaction(user_id=user.id, type=type_transaction, amount=amount, description=description)
    db.session.add(new_transaction)
    db.session.commit()

    flash("Transaction ajoutée avec succès !")
    return redirect('/dashboard')

@app.route('/delete_transaction/<int:id>')
def delete_transaction(id):
    if 'email' not in session:
        return redirect('/login')

    transaction = Transaction.query.get(id)
    if transaction:
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaction supprimée !")

    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
