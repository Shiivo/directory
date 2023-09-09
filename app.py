from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import random, string
from faker import Faker
app = Flask(__name__)
app.secret_key = '$2b$12$SAJRDMEizf0sOwS2AC9ZS.ADWLYua93Gghmdncp/mUct4RONOhmH2'
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///directory.db'
db = SQLAlchemy(app)
faker = Faker()
fake_address = faker.address()
fake_business_name = faker.company()
def generate_fake_bio():
    return faker.paragraph(nb_sentences=3)
fake_bio = generate_fake_bio()



class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"<Admin {self.username}>"

class business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    sponsorship_budget = db.Column(db.Float, nullable=False)
    website = db.Column(db.String(200))
    bio = db.Column(db.Text)

# Create the database tables
with app.app_context():
    db.create_all()

# Homepage - Redirect to login page
@app.route('/')
def index():
    return redirect('/home')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Process the form data
        business_name = request.form['business_name']
        phone_number = request.form['phone_number']
        address = request.form['address']
        sponsorship_budget = float(request.form['sponsorship_budget'])
        website = request.form['website']
        bio = request.form['bio']

        # Create a new Business instance
        new_business = business(
            business_name=business_name,
            phone_number=phone_number,
            address=address,
            sponsorship_budget=sponsorship_budget,
            website=website,
            bio=bio
                )
        # Add the new business to the database

        if 'survey_checkbox' in request.form and request.form['survey_checkbox'] == 'on':
            return redirect(url_for('survey'))  # Redirect to the survey page


        thank_you_message = "Thank you for registering your company!"
        return render_template('home.html', thank_you_message=thank_you_message)

    return render_template('home.html')



@app.route('/register', methods=['GET', 'POST'])
def register_admin():
    # Check if there is already an admin user
    existing_admin = Admin.query.first()

    if existing_admin:
        return render_template('register.html', error='Admin account already exists')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash the password using bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create and add the admin user to the database
        new_admin = Admin(username=username, password=hashed_password)
        db.session.add(new_admin)
        db.session.commit()

        return redirect('/login')  # Redirect to the login page

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()
        if admin and bcrypt.check_password_hash(admin.password, password):
            session['admin_logged_in'] = True
            print("Admin logged in successfully")
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
            print("Invalid credentials provided")


    return render_template('admin_login.html')

def sort_by_sponsorship_budget_high(business):
    return business.sponsorship_budget

def sort_by_sponsorship_budget_low(business):
    return -business.sponsorship_budget

def sort_by_business_name(business):
    return business.business_name


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    businesses = business.query.all()
    sort_option = request.args.get('sort')

    if sort_option == 'sponsorship_budget_high':
        businesses = sorted(businesses, key=sort_by_sponsorship_budget_high)
    elif sort_option == 'sponsorship_budget_low':
        businesses = sorted(businesses, key=sort_by_sponsorship_budget_low)
    else:
        # Default sorting
        businesses = sorted(businesses, key=sort_by_business_name)

    search_query = request.args.get('search')
    if search_query:
        businesses = [business for business in businesses if search_query.lower() in business.business_name.lower()]

    return render_template('admin_dashboard.html', businesses=businesses)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


def generate_business_name():
    return f"{faker.company()} {faker.company_suffix()}"

def generate_random_phone_number():
    return '04' + ''.join(random.choice(string.digits) for _ in range(8))

def generate_random_address():
    return f"{faker.building_number()} {faker.street_name()} St, {faker.city()}"

def generate_random_sponsorship_budget():
    return round(random.uniform(500, 5000), 2)

def generate_random_website():
    business_name = generate_business_name().replace(' ', '').replace(',', '')
    return f"https://www.{business_name.lower()}.com"


def generate_random_bio():
    return faker.paragraph(nb_sentences=3)


@app.route('/survey')
def survey():
    # You can render a template for the survey page here
    return render_template('survey.html')


@app.route('/addb')
def add_autogenerated_businesses():
    num_businesses = 10  # Number of autogenerated businesses to create

    autogenerated_businesses = []
    for _ in range(num_businesses):
        new_business = business(
            business_name=generate_business_name(),
            phone_number=generate_random_phone_number(),
            address=generate_random_address(),
            sponsorship_budget=generate_random_sponsorship_budget(),
            website=generate_random_website(),
            bio=generate_random_bio()
        )
        autogenerated_businesses.append(new_business)

    db.session.add_all(autogenerated_businesses)
    db.session.commit()

    return f"{num_businesses} autogenerated businesses added to the database."


if __name__ == '__main__':
    app.run(debug=True)
