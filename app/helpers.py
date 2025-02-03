# Helper functions (like validating login)

import plotly.graph_objects as go # Plotly
from app.models import User, Transaction # SQLAlchemy
from sqlalchemy.orm.attributes import flag_modified # SQLAlchemy
from app import db # Flask
from validator_collection import validators, errors # validator-collection from Problem Set 7
from datetime import datetime # Datetime from Problem Set 8

def validate_login(email, password):
    try:
        # Find matching credentials
        matching_user_email = User.query.filter_by(email = email).first()
        matching_user_password = False

        if matching_user_email.password == password:
            matching_user_password = True

        print("Email:", matching_user_email, "Password:", matching_user_password)

        if matching_user_email and matching_user_password:
            print("Correct User Credentials!")
            return True
        elif matching_user_email:
            print("Incorrect Email")
        elif matching_user_password:
            print("Incorrect Password")
        else:
            print("Both email & password incorrect")
        return False

    except Exception as e:
        return e

def create_new_user_account(email, password):
    # Find first match with user's name
    found_user = User.query.filter_by(email = email).first()

    # Ensure user with email dosen't already existing
    if not found_user:
        try:
            # Use Validator-collection library
            valid_email = validators.email(email)

            if valid_email:
                # Create new User object and add them to database
                new_user = User(name = None, email = email, password = password)
                db.session.add(new_user) # Add user's name to database
                db.session.commit() # Commit the changes to the database

                print("New user created successfully! - From helper: create_new_user()")
                return True
            else:
                print("Invalid email!")
                return False

        except Exception as e:
            print(f"Error when creating new user: {e}")


def create_new_expense(description, category, amount):
    # Create new Expense object and add them to database
    new_expense = Expense(description = description, category = category, amount = amount)
    db.session.add(new_expense) # Add expense to database
    db.session.commit() # Commit the changes to the database


def get_cashflow_difference(user):
    if user:
        return user.income - user.expenses

        '''
        desired_cashflow = user.cashflow
        cashflow_difference = current_cashflow - desired_cashflow
        if cashflow_difference > 0:
            return f"You're beating your current cashflow goal by ${int(cashflow_difference)}!"
        elif cashflow_difference == 0:
            return f"You're meeting your current cashflow goal, congrats!"
        else:
            return f"You're off by ${abs(cashflow_difference)} for your cashflow goal!"
        '''


def create_pie(current_user):
    # Verify user
    if current_user:
        # Initialize data for pie chart
        colors = ["blue", "red", "green"]
        income = current_user.income
        expenses = current_user.expenses
        cashflow = income - expenses

        # Create pie chart
        fig = go.Figure(data=[go.Pie(labels=['Income','Expenses','Cashflow'], values=[income, expenses, cashflow])])

        fig.update_traces(hoverinfo='label+percent', textinfo='value', textfont_size=20,
                  marker=dict(colors=colors, line=dict(color='#000000', width=2)))

        return fig.to_json()

def update_user_data(user, **kwargs):
    for key, value in kwargs.items():
        if value is not None: # Only update given User data values
            setattr(user, key, value)
    db.session.commit() # Save changes to the database

def update_transaction_in_db(user_email, id, field, value):
    # Fetch transaction
    print("@helpers - update_transaction_in_db called")
    transaction = Transaction.query.filter_by(transaction_id = id).first()
    current_user = User.query.filter_by(email = user_email).first()

    try:
        if transaction:
            setattr(transaction, field, value)
        else:
            # Fetch all associated user transactions and assign new transaction under random account
            user_transactions = Transaction.query.filter_by(user_id = current_user.id).all()

            # Get User's transaction save route/account
            for transaction in user_transactions:
                if user_account_id := transaction.account_id:
                    break

            # Debug: print("@helpers < @update_transaction_in_db - Current Date:", datetime.today())

            new_transaction = Transaction(
                transaction_id = id,
                user_id = current_user.id, # Pass through user object or email that can be used to get user_id
                account_id = user_account_id,
                date = datetime.today(),
                description = "New Transaction",
                category = None,
                amount = 0
            )

            setattr(new_transaction, field, value)

            db.session.add(new_transaction)
            print("@helpers < @update_transaction_in_db - New Transaction Synced:", new_transaction)


        db.session.commit()
        print("@helpers < @update_transaction_in_db - Database successfully committed.")

    except Exception as e:
        print("@helpers < @update_transaction_in_db - Something went wrong commiting to database:", e)

# Helper function for Plaid API - sync_transactions to retrieve latest_cursor
def get_latest_cursor(user_id, access_token):
    # Get user from database
    user = User.query.filter_by(id = user_id).first()

    # Verify user
    if not user:
        raise ValueError("User not found.")

    # Iterate over Plaid user connection & match access token
    for connection in user.plaid_connections:
        if connection["access_token"] == access_token: # Match found
            print("@helpers -> get_latest_cursor - Access Token:", connection["access_token"])
            return connection.get("latest_cursor", '') # Return latest_cursor otherwise return empty cursor

    # Edge Case: No user connections
    return None

# Helper function to update Plaid user's cursor
def update_latest_cursor(user, access_token, new_cursor):
    print("@update_latest_cursor - Fetching latest user cursor.")
    # Iterate over user connections
    for connection in user.plaid_connections:
        if connection["access_token"] == access_token: # Found matching access_token
            connection["latest_cursor"] = new_cursor
            break

    else:
        raise ValueError("Access token not found in user's connections.")

    # Update the user's connection JSON in database
    flag_modified(user, "plaid_connections")
    db.session.commit() # Update database
    print("@helpers -> @update_latest_cursor: Successfully updated!")

# Update database
def apply_transaction_updates(user_id, added, modified, removed):
    # Fetch user
    user = User.query.filter_by(id = user_id).first()

    # Debug: print("@helpers -> @apply_transaction_updates - Called.")

    # Verify user
    if not user:
        raise ValueError("User not found.")

    # Get user expenses total
    transactions_total = user.expenses

    # Debug: print(added, ":@helpers -> @apply_transaction_updates - Transactions to add")

    # Handle added transactions
    for transaction in added:
        # Try to fetch transaction from database
        existing_transaction = Transaction.query.filter_by(transaction_id = transaction["transaction_id"]).first()

        # Skip adding transaction if already in database
        if existing_transaction:
            continue

        amount = transaction["amount"]
        #Debug: print("@helpers -> @apply_transaction_updates - Adding Transaction:", transaction["name"], "$", amount)
        """
        Positive values when money moves out of the account.
        Negative values when money moves in.
        """
        if amount >= 0:
            transactions_total += amount

        new_transaction = Transaction(
            transaction_id = transaction["transaction_id"],
            user_id = user_id,
            account_id = transaction["account_id"],
            date = transaction["date"],
            description = transaction["name"],
            category = transaction["category"][0] if transaction["category"] else None,
            amount = amount
        )
        db.session.add(new_transaction)
        db.session.flush()  # Ensure transaction is added before commit
        # Debug: print("@helpers -> @apply_transaction_updates - Added new Transaction:", new_transaction)

    # Handle modified transactions
    for transaction in modified:
        # Fetch transaction from database
        existing_transaction = Transaction.query.filter_by(transaction_id = transaction["transaction_id"]).first()

        # Update existing transaction details
        if existing_transaction:
            existing_transaction.amount = transaction["amount"]
            existing_transaction.description = transaction["name"]
            existing_transaction.category = transaction["category"][0] if transaction["category"] else None

    # Handle removed transaction
    for transaction_id in removed:
        # Get matching expense
        existing_transaction = Transaction.query.filter_by(transaction_id = transaction_id).first()

        # Delete transaction
        if existing_transaction:
            db.session.delete(existing_transaction)

    # Update user's total expenses
    user.expenses = round(transactions_total, 2)
    try:
        db.session.commit()
        print("@helpers -> @apply_transaction_updates - Database successfully updated!")
    except Exception as e:
        db.session.rollback() # Rollback database to previous version
        print(f"@helpers -> @apply_transaction_updates - Commit failed: {e}")
