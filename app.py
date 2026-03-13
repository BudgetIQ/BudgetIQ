from flask import Flask, render_template, request, redirect, session, url_for
from datetime import datetime

import os
import mysql.connector

db = mysql.connector.connect(
    host="switchyard.proxy.rlwy.net",
    user="root",
    password="HhsBngedzoatYOvNROuzDzLSvrRzaebG",
    database="railway",
    port=37938
)
cursor = db.cursor(dictionary=True)
# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        cursor.execute(
            "INSERT INTO users (username,email,password) VALUES (%s,%s,%s)",
            (username,email,password)
        )

        db.commit()

        return redirect('/login')

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email,password)
        )

        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            return redirect('/dashboard')

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    year = request.args.get('year')

    if not year:
        year = datetime.now().year

    cursor.execute("""
        SELECT id, amount, category, description, date
        FROM expenses
        WHERE user_id=%s AND YEAR(date)=%s
        ORDER BY date DESC
    """,(session['user_id'],year))

    expenses = cursor.fetchall()

    return render_template("dashboard.html",expenses=expenses,year=year)

# ---------------- ADD EXPENSE ----------------
@app.route('/add_expense',methods=['POST'])
def add_expense():

    if 'user_id' not in session:
        return redirect('/login')

    amount = request.form.get('amount')
    category = request.form.get('category')
    description = request.form.get('description')
    date = request.form.get('date')

    cursor.execute("""
        INSERT INTO expenses (user_id,amount,category,description,date)
        VALUES (%s,%s,%s,%s,%s)
    """,(session['user_id'],amount,category,description,date))

    db.commit()

    return redirect('/dashboard')

# ---------------- DELETE EXPENSE ----------------
@app.route('/delete/<int:id>',methods=['POST'])
def delete(id):

    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute(
        "DELETE FROM expenses WHERE id=%s AND user_id=%s",
        (id,session['user_id'])
    )

    db.commit()

    return redirect('/dashboard')

# ---------------- MONTHLY REPORT ----------------
@app.route('/monthly_report')
def monthly_report():

    if 'user_id' not in session:
        return redirect('/login')

    year = request.args.get('year')

    if not year:
        year = datetime.now().year

    cursor.execute("""
        SELECT MONTH(date) AS month, SUM(amount) AS total
        FROM expenses
        WHERE user_id=%s AND YEAR(date)=%s
        GROUP BY MONTH(date)
    """,(session['user_id'],year))

    data = cursor.fetchall()

    months = [row['month'] for row in data]
    totals = [row['total'] for row in data]

    return render_template(
        "monthly_report.html",
        data=data,
        months=months,
        totals=totals,
        year=year
    )

# ---------------- YEARLY REPORT ----------------
@app.route('/yearly_report')
def yearly_report():

    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute("""
        SELECT YEAR(date) AS year, SUM(amount) AS total
        FROM expenses
        WHERE user_id=%s
        GROUP BY YEAR(date)
        ORDER BY YEAR(date)
    """,(session['user_id'],))

    data = cursor.fetchall()

    years = [row['year'] for row in data]
    amounts = [row['total'] for row in data]

    return render_template(
        "yearly_report.html",
        data=data,
        years=years,
        amounts=amounts
    )

# ---------------- CATEGORY REPORT ----------------
@app.route('/category_report')
def category_report():

    if 'user_id' not in session:
        return redirect('/login')

    year = request.args.get('year')

    if not year:
        year = datetime.now().year

    cursor.execute("""
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE user_id=%s AND YEAR(date)=%s
        GROUP BY category
    """,(session['user_id'],year))

    data = cursor.fetchall()

    categories = [row['category'] for row in data]
    totals = [row['total'] for row in data]

    return render_template(
        "category_report.html",
        data=data,
        categories=categories,
        totals=totals,
        year=year
    )

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
