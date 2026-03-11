from flask import Flask, render_template, request, redirect, session, url_for, g
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "budgetiq_secretkey"

DATABASE = "budget.db"

# ---------------- DATABASE CONNECTION ----------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO users (username,email,password) VALUES (?,?,?)",
            (username, email, password)
        )

        db.commit()

        return redirect('/login')

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
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

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, amount, category, description, date
        FROM expenses
        WHERE user_id=? AND strftime('%Y',date)=?
        ORDER BY date DESC
        """,
        (session['user_id'], str(year))
    )

    expenses = cursor.fetchall()

    return render_template("dashboard.html", expenses=expenses, year=year)

# ---------------- ADD EXPENSE ----------------
@app.route('/add_expense', methods=['POST'])
def add_expense():

    if 'user_id' not in session:
        return redirect('/login')

    amount = request.form['amount']
    category = request.form['category']
    description = request.form['description']
    date = request.form['date']

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO expenses (user_id,amount,category,description,date)
        VALUES (?,?,?,?,?)
        """,
        (session['user_id'], amount, category, description, date)
    )

    db.commit()

    return redirect('/dashboard')

# ---------------- DELETE EXPENSE ----------------
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):

    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id=? AND user_id=?",
        (id, session['user_id'])
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

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT strftime('%m',date) as month, SUM(amount)
        FROM expenses
        WHERE user_id=? AND strftime('%Y',date)=?
        GROUP BY month
        """,
        (session['user_id'], str(year))
    )

    data = cursor.fetchall()

    months = [row['month'] for row in data]
    totals = [row[1] for row in data]

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

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT strftime('%Y',date) as year, SUM(amount) as total
        FROM expenses
        WHERE user_id=?
        GROUP BY year
        ORDER BY year
        """,
        (session['user_id'],)
    )

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

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=? AND strftime('%Y',date)=?
        GROUP BY category
        """,
        (session['user_id'], str(year))
    )

    data = cursor.fetchall()

    categories = [row['category'] for row in data]
    totals = [row[1] for row in data]

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
    app.run(debug=True)
