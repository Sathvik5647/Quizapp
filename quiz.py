from flask import Flask, render_template, request, redirect, url_for, session, flash
from urllib.parse import quote_plus
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

password = quote_plus('ms290171')
app.secret_key = 'sathvik123'
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{password}@localhost/quiz_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)

class Score(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    class Questions(db.Model):
        __tablename__ = 'questions'
        __table_args__ = {'autoload_with': db.engine}
    db.create_all()

# Session check for deleted users
@app.before_request
def check_user_exists():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if not user:
            session.pop('user_id', None)
            flash("Your account no longer exists.")
            return redirect(url_for('login'))

def is_logged_in():
    return 'user_id' in session

@app.route('/')
def home():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    leaderboard = Score.query.order_by(Score.score.desc()).all()
    names = User.query.all()
    return render_template('index.html',leaderboard=leaderboard, names=names)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash("Please enter a username or a password")
        else:
            existing_user = User.query.filter_by(username=username, password=password).first()
            if existing_user:
                session['user_id'] = existing_user.id
                return redirect(url_for('dashboard'))
            else:
                flash("Incorrect username or password")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        repassword = request.form.get('repassword')

        if not username or not password:
            flash("Please enter username and password")
        elif password != repassword:
            flash("Passwords do not match")
        else:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Username exists, please login")
                return redirect(url_for('login'))
            else:
                new_user = User(username=username, password=password)
                db.session.add(new_user)
                db.session.commit()
                flash("Account successfully registered, please login")
                return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if request.method=="POST":
        username=request.form.get('username')
        new_password=request.form.get('new_password')
        repassword=request.form.get('repassword')
        user=User.query.filter_by(username=username).first()
        if not username or not new_password:
            flash("Please enter username and password")
        elif not user:
            flash("Username does not exist")
        elif new_password!=repassword:
            flash("Passwords do not match!")
        elif user.password==new_password:
            flash("Password is already in use for this user")
        else:
            user.password=new_password
            db.session.commit()
            flash("Password successfully changed! You can login using your new password")
            return redirect(url_for('login'))
    return render_template('forgot_password.html')
        

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("User successfully logged out")
    return redirect(url_for('login'))

@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for('login'))
    user_id = session['user_id']
    user = User.query.get(user_id)
    personal_record = Score.query.filter_by(user_id=user_id).order_by(Score.score.desc()).all()
    leaderboard = Score.query.order_by(Score.score.desc()).all()
    names = User.query.all()
    return render_template('dashboard.html', user=user.username, personal_record=personal_record, leaderboard=leaderboard, names=names)

@app.route("/quiz/<int:qno>", methods=["GET", "POST"])
def quiz(qno):
    if not is_logged_in():
        return redirect(url_for('login'))
    question = Questions.query.get(qno)  
    if request.method == "POST":
        selected_option = request.form.get('option')
        if selected_option and selected_option.upper() == question.correct_option.upper():
            if qno==5:
                score = Score(score=qno, user_id=session['user_id'])
                db.session.add(score)
                db.session.commit()
                flash("Quiz Finished!")
                return redirect(url_for("finished", score=qno))
            else:
                flash("Correct!")
                return redirect(url_for("quiz", qno=qno + 1))
        else:
            flash("Incorrect! You're out of the quiz")
            score = Score(score=qno-1, user_id=session['user_id'])
            db.session.add(score)
            db.session.commit()
            return redirect(url_for('finished', score=qno - 1))
    return render_template('quiz.html', question=question)

@app.route("/finished")
def finished():
    score = request.args.get('score', 0)
    return render_template('finished.html', score=score)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
