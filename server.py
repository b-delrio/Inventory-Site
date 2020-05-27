from flask import Flask, render_template, redirect, request, session, flash, url_for
from mysqlconn import connectToMySQL
from flask_bcrypt import Bcrypt        
from datetime import datetime
import re
import smtplib

app = Flask(__name__)
app.secret_key = 'tho'
bcrypt = Bcrypt(app)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
PASSWORD_REGEX = re.compile("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$")

@app.route('/')
def logreg():
    return render_template('login.html')

@app.route("/register", methods = ["POST"])
def registration():
    is_valid = True

    if len(request.form['fname']) < 1:
        is_valid = False
        flash('Please endter a valid first name')
    if len(request.form['lname']) < 1:
        is_valid = False
        flash('Please enter a valid last name')
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash('Invalid email address')
    if not PASSWORD_REGEX.match(request.form['pword']):
        is_valid = False
        flash('Must use combination of upper case, numbers, and special characters in password.')
    if len(request.form['pword']) < 5:
        is_valid = False
        flash('Password must be at least 5 characters long')
    if request.form['cpword'] != request.form['pword']:
        is_valid = False
        flash('Passwords entered do not match. Please try again')

    if is_valid:
        pw_hash = bcrypt.generate_password_hash(request.form['pword'])
        mysql = connectToMySQL('inventory')
        query = 'INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(pw)s, NOW(), NOW())'
        data = {
            'fn': request.form['fname'],
            'ln': request.form['lname'],
            'em': request.form['email'],
            'pw': pw_hash,
        }
        user_id = mysql.query_db(query, data)
        session['user_id'] = user_id
        flash("user successfully added!") 

        return redirect('/welcome')
    else:
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    is_valid = True

    if len(request.form['email']) < 1:
        is_valid = False
        flash('Please enter your email')
    if len(request.form['pword']) < 1:
        is_valid = False
        flash('Please enter your password')
    if not EMAIL_REGEX.match(request.form['email']):
        flash('Invalid email address')

    if not is_valid:
        return redirect('/')
    else:
        query = 'SELECT * FROM users WHERE users.email = %(em)s'
        data = {'em': request.form.get('email')}
        mysql = connectToMySQL('inventory')
        user = mysql.query_db(query, data)
        print(user)

        if user:
            hashed_password = user[0]['password']
            if bcrypt.check_password_hash(hashed_password, request.form['pword']):
                session['user_id'] = user[0]['id']
                session['user_name'] = user[0]['first_name']
                return redirect('/welcome')
            else:
                flash('Password incorrect')
                return redirect('/')

@app.route('/welcome')
def welcome():
    mysql = connectToMySQL('inventory')
    query = 'SELECT inventory.id as inventory_id, inventory.users_id, inventory.description, inventory.price, inventory.location FROM inventory WHERE users_id = %(uid)s'
    data = { 'uid' : session['user_id']}
    items = mysql.query_db(query, data)
    print(items)

    total_value = 0
    for item in items:
        total_value = total_value + item['price']

    return render_template('welcome.html', items=items, total_value=total_value)

@app.route('/add')
def add():
    return render_template('add.html')

@app.route('/cancel')
def cancel():
    return redirect('/welcome')

@app.route('/add_inv', methods=['POST'])
def add_inv():
    mysql = connectToMySQL('inventory')
    query = 'INSERT INTO inventory (users_id, description, price, location, created_at) VALUES (%(uid)s, %(des)s, %(pr)s, %(lo)s, NOW())' 
    data = {
        'uid': session['user_id'],
        'des': request.form['description'],
        'pr': request.form['price'],
        'lo': request.form['location'],
    }
    mysql.query_db(query, data)
    flash("Item successfully added!")
    return redirect('/welcome')

@app.route('/<inventory_id>/delete', methods=['POST'])
def delete(inventory_id):
    query = 'DELETE FROM inventory WHERE id = %(inv_id)s'
    data = { 'inv_id': inventory_id}
    mysql = connectToMySQL('inventory')
    mysql.query_db(query, data)
    return redirect('/welcome')

@app.route('/<inventory_id>/edit')
def edit(inventory_id):
    query = 'SELECT * FROM inventory WHERE id = %(inv_id)s'
    data = { 'inv_id': inventory_id}
    mysql = connectToMySQL('inventory')
    items = mysql.query_db(query, data)
    return render_template('edit.html', items = items, inventory_id = inventory_id)

@app.route('/<inventory_id>/save', methods=['POST'])
def save(inventory_id):
    query = 'UPDATE inventory SET description = %(des)s, price = %(pr)s, location = %(lo)s, updated_at = NOW() WHERE id = %(id)s' 
    data = {
        'des': request.form['description'],
        'pr': request.form['price'],
        'lo': request.form['location'],
        'id': inventory_id,
    }
    mysql = connectToMySQL('inventory')
    mysql.query_db(query, data)
    return redirect('/welcome')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
    
if __name__ == "__main__":
    app.run(debug=True)