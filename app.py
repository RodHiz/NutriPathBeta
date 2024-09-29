# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 20:42:19 2024

@author: rodri
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a more secure key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User Model
# Update the User model to include calorie goals
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    goal_intake = db.Column(db.Integer, nullable=True)  # Daily calorie intake goal
    goal_burn = db.Column(db.Integer, nullable=True)    # Daily calorie burn goal



class CalorieLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Make sure this is DateTime
    calories_eaten = db.Column(db.Integer, nullable=False)
    calories_burned = db.Column(db.Integer, nullable=False)

    def net_calories(self):
        return self.calories_eaten - self.calories_burned
    

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/log_calories', methods=['GET', 'POST'])
def log_calories():
    try:
        if request.method == 'POST':
            # Log the form data for debugging
            print(request.form)

            # Convert input values to integers
            calories_eaten = int(request.form['calories_eaten'])
            calories_burned = int(request.form['calories_burned'])

            # Parse the timestamp from the form (datetime-local field returns a string)
            timestamp_str = request.form['timestamp']
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M')

            # Check if session contains 'user_id'
            if 'user_id' not in session:
                raise Exception("User ID not found in session")

            # Create a new CalorieLog entry
            new_log = CalorieLog(
                user_id=session['user_id'],
                calories_eaten=calories_eaten,
                calories_burned=calories_burned,
                timestamp=timestamp
            )
            
            # Add and commit the new log to the database
            db.session.add(new_log)
            db.session.commit()
            
            return redirect(url_for('view_progress'))

    except ValueError as ve:
        # Handle invalid inputs (e.g., non-numeric values for calories)
        print(f"ValueError: {ve}")
        return render_template('error.html', message="Please enter valid numbers for calories."), 400
    
    except Exception as e:
        # Catch any other unexpected errors and print the error to the console
        print(f"Error: {e}")
        return render_template('500.html'), 500
    
    return render_template('log_calories.html')


from datetime import datetime

from datetime import datetime

from datetime import datetime

from datetime import datetime

@app.route('/view_progress')
def view_progress():
    user = db.session.get(User, session['user_id'])  # Ensure user is logged in
    logs = CalorieLog.query.filter_by(user_id=session['user_id']).order_by(CalorieLog.timestamp).all()

    dates = []
    cumulative_eaten = 0
    cumulative_burned = 0

    calories_eaten = []
    calories_burned = []
    net_calories = []

    individual_eaten = []
    individual_burned = []

    previous_day = None

    # Iterate over logs and calculate cumulative values, resetting at the start of each new day
    for log in logs:
        current_day = log.timestamp.date()  # Get the current log's date (ignoring time)

        # If it's a new day, insert None values to create breaks in the line graph
        if previous_day is None or current_day != previous_day:
#            if previous_day is not None:
 #               # Insert `None` to break the line in the graph
  #              dates.append(None)  # Creates a gap in the graph
   #             calories_eaten.append(None)
    #            calories_burned.append(None)
     #           net_calories.append(None)

            # Reset cumulative totals for the new day
            cumulative_eaten = 0
            cumulative_burned = 0

        # Add current calories to the cumulative totals
        cumulative_eaten += log.calories_eaten
        cumulative_burned += log.calories_burned

        # Append the cumulative values
        dates.append(log.timestamp.strftime('%Y-%m-%d %H:%M'))  # Include date and time for accurate logging
        calories_eaten.append(cumulative_eaten)
        calories_burned.append(cumulative_burned)
        net_calories.append(cumulative_eaten - cumulative_burned)

        # Append individual values for tooltips
        individual_eaten.append(log.calories_eaten)
        individual_burned.append(log.calories_burned)

        # Update the previous_day to the current log's date
        previous_day = current_day

    # Pass all the necessary data to the template
    return render_template('view_progress.html', 
                           dates=dates, 
                           calories_eaten=calories_eaten, 
                           calories_burned=calories_burned, 
                           net_calories=net_calories, 
                           individual_eaten=individual_eaten, 
                           individual_burned=individual_burned, 
                           goal_intake=user.goal_intake,
                           goal_burn=user.goal_burn)


@app.route('/sign_in_form', methods=['GET', 'POST'])
def sign_in_form():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        user = User.query.filter_by(username=username, email=email).first()
        
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome, {user.username.capitalize()}!', 'success')
            return redirect(url_for('home'))
        else:
            return render_template('error.html', message="Invalid credentials. Please try again.")

    return render_template('sign_in.html')


@app.route('/add_user', methods=['GET', 'POST'])
def add_user_form():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form['username']
            email = request.form['email']
            
            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                flash(f"Username '{username}' is already taken.", 'error')
                return redirect(url_for('add_user'))

            if User.query.filter_by(email=email).first():
                flash(f"Email '{email}' is already registered.", 'error')
                return redirect(url_for('add_user'))

            # Create a new user
            new_user = User(username=username, email=email)
            db.session.add(new_user)
            db.session.commit()
            
            flash(f"User '{username}' added successfully!", 'success')
            return redirect(url_for('home'))
        
        except Exception as e:
            # Catch and display any unexpected errors
            print(f"Error: {e}")
            return render_template('error.html', message="An unexpected error occurred. Please try again later."), 500
    
    return render_template('add_user.html')


# Sign-out route
@app.route('/sign_out', methods=['POST'])
def sign_out():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been signed out.', 'info')
    return redirect(url_for('home'))


@app.route('/set_goals', methods=['GET', 'POST'])
def set_goals():
    try:
        if request.method == 'POST':
            goal_intake = int(request.form['goal_intake'])
            goal_burn = int(request.form['goal_burn'])
            
            user = User.query.get(session['user_id'])  # Ensure user is logged in
            
            # Update user goals
            user.goal_intake = goal_intake
            user.goal_burn = goal_burn
            db.session.commit()

            return redirect(url_for('view_progress'))

    except ValueError:
        return render_template('error.html', message="Invalid input. Please enter valid calorie goals."), 400
    
    except Exception as e:
        print(f"Error: {e}")
        return render_template('500.html'), 500

    return render_template('set_goals.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)