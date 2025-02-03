# Define the database models
# nullable = instance can be nothing

from app import db
from sqlalchemy.ext.mutable import MutableList

# Define a model class by subclassing db.Model
class User(db.Model):
    # Each object in out model will have: An ID of type Integer that will act as the reference, e.g. the primary key
    id = db.Column("id", db.Integer, primary_key = True)

    # Initialize user verification parameters
    name = db.Column(db.String(100), nullable = True)
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))

    # Initialize user financial parameters
    income = db.Column(db.Float, nullable = True)
    expenses = db.Column(db.Float, nullable = True)
    cashflow = db.Column(db.Float, nullable = True)

    # Plaid-specific parameters for linking bank accounts
    plaid_user_id = db.Column(db.String(), nullable = True)
    plaid_user_token = db.Column(db.String(128), nullable = True)

    # Plaid Multilink connections stored as JSON
    plaid_connections = db.Column(MutableList.as_mutable(db.JSON), nullable = True, default = list)

    @classmethod
    def find(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def assign_income(cls, email, income):
        # Fetch current user object
        user = cls.query.filter_by(email = email).first()
        if not user:
            print("User not found @db.Model: User")
            return

        user.income = income
        print(f"assign_income - Setting income for {email} to {income}")

        try:
            db.session.commit()
            print(f"User income updated successfully for {email}!")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating user income for {email}: {str(e)}")

    # Create JSON for each individual plaid connection
    @classmethod
    def add_bank_connection(cls, email, access_token, item_id, institution_name):
        # Fetch current user object
        user = cls.query.filter_by(email = email).first()
        if not user:
            print("User not found @db.Model: User")
            return

        # If first time initialization:
        if user.plaid_connections is None:
            user.plaid_connections = [] # Initialize if None

        # Create new connection
        new_connection = {
            "access_token": access_token,
            "item_id": item_id,
            "institution_name": institution_name,
            "latest_cursor": None # Plaid parameter for syncing user Transactions
        }

        # Add newly create connection
        user.plaid_connections.append(new_connection)

        try:
            db.session.commit()
            print("Bank connection added successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding new bank conenction: {e}")

    # Declearing of User's object parameters (Defaulting financials to 0.0)
    def __init__(self, name, email, password, income=0.0, expenses=0.0, cashflow=0.0, plaid_connections=None):
        self.name = name
        self.email = email
        self.password = password
        self.income = income
        self.expenses = expenses
        self.cashflow = cashflow
        self.plaid_connections = plaid_connections or []

    def __repr__(self):
        return f"<User {self.name}, {self.email}>"

# Model for transaction
class Transaction(db.Model):

    # Unique User Transaction ID
    transaction_id = db.Column(db.String, primary_key = True)

    # Link to user's transaction
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    user = db.relationship('User', backref = db.backref('user_expenses', lazy = True))

    # The associated linked account (e.g. checking, credit, etc.)
    account_id = db.Column(db.String(50))

    # Information about the expense
    date = db.Column(db.Date)
    description = db.Column(db.String(100))
    category = db.Column(db.String(100), nullable = True)
    amount = db.Column(db.Float)

    # Initalize Expense's attributes
    def __init__(self, transaction_id, user_id, account_id, date, description, category, amount):
        self.transaction_id = transaction_id
        self.user_id = user_id
        self.account_id = account_id
        self.date = date
        self.description = description
        self.category = category
        self.amount = amount
