from flask import Flask, render_template, request, redirect, session,url_for
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = "budgetiq_secretkey"

# ---------------- DATABASE CONNECTION ----------------
db = mysql.connector.connect(
    host="localhost",
    user="karan",
    password="karan@1234",  # 🔴 change this
    database="budgetiq"
)

cursor = db.cursor(dictionary=True, buffered=True)
# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        values = (username, email, password)

        cursor.execute(sql, values)
        db.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            return redirect('/dashboard')

    return render_template('login.html')


# ---------------- DASHBOARD ----------------
from datetime import datetime

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    year = request.args.get('year')

    if not year:
        year = datetime.now().year

    cursor = db.cursor()

    cursor.execute("""
        SELECT id, amount, category, description, date
        FROM expenses
        WHERE user_id=%s AND YEAR(date)=%s
        ORDER BY date DESC
    """, (session['user_id'], year))

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
    user_id = session['user_id']
    cursor.execute("""
        INSERT INTO expenses (user_id, amount, category, description, date)
        VALUES (%s, %s, %s, %s, %s)
    """, (session['user_id'], amount, category, description, date))

    db.commit()
    return redirect('/dashboard')


# ---------------- DELETE EXPENSE ----------------
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id=%s AND user_id=%s",
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

    cursor = db.cursor()

    cursor.execute("""
        SELECT MONTH(date), SUM(amount)
        FROM expenses
        WHERE user_id=%s AND YEAR(date)=%s
        GROUP BY MONTH(date)
    """, (session['user_id'], year))

    data = cursor.fetchall()

    months = [row[0] for row in data]
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

    cursor.execute("""
        SELECT YEAR(date) AS year, SUM(amount) AS total
        FROM expenses
        WHERE user_id=%s
        GROUP BY YEAR(date)
        ORDER BY YEAR(date)
    """, (session['user_id'],))

    data = cursor.fetchall()

    years = [row['year'] for row in data]
    amounts = [float(row['total']) for row in data]

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

    cursor = db.cursor()

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=%s AND YEAR(date)=%s
        GROUP BY category
    """, (session['user_id'], year))

    data = cursor.fetchall()

    categories = [row[0] for row in data]
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
