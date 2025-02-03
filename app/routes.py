# Defining app's routes (e.g. home, login, ...)
# POST = Sending to Server
# GET = Recieving from Server

# Imports - Flask, Plotly, SQLite, Random, datetime
from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from app.models import User, Transaction
from app.helpers import validate_login, create_new_user_account, create_new_expense, get_cashflow_difference, create_pie, update_transaction_in_db, get_latest_cursor, update_latest_cursor, apply_transaction_updates
from app import db
import random # For fake data
import datetime # Converting transaction dates

# Imports - Plaid
import plaid
from plaid.api import plaid_api

from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_request import LinkTokenCreateRequest

from plaid.model.link_token_create_request_income_verification import LinkTokenCreateRequestIncomeVerification
from plaid.model.income_verification_source_type import IncomeVerificationSourceType
from plaid.model.link_token_create_request_income_verification_bank_income import LinkTokenCreateRequestIncomeVerificationBankIncome

from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_get_request import LinkTokenGetRequest

from plaid.model.transactions_sync_request import TransactionsSyncRequest

from plaid.model.user_create_request import UserCreateRequest
from plaid.model.consumer_report_user_identity import ConsumerReportUserIdentity
from plaid.model.address_data import AddressData

from plaid.model.credit_bank_income_get_request import CreditBankIncomeGetRequest
from plaid.model.credit_bank_income_get_request_options import CreditBankIncomeGetRequestOptions

from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid import ApiClient

# Flask
main = Blueprint("main", __name__)

# Set up Plaid API client configuration
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,  # Sandbox environment
    api_key={
        "clientId": "67671f77ec5d8b0026b53248",
        "secret": "07f24d6c85c5534b4c7e074bbe85c5"
    }
)

# Load/Intialize the enviorment variables
api_client = ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)

# Sandbox environment variables
unique_id = 2250225022
fake_data = True

# Step 0: Create new user alongside their unique token
@main.route('/create_new_user', methods=["POST"])
def create_new_user():
    # Fetch user from the seession based off email
    user = User.query.filter_by(email=session["user"]).first()

    # Edge Case
    if not user:
        return jsonify({'error': 'User not found'}), 404

    print("Plaid user ID:", user.plaid_user_token)

    # Check if user already has Plaid user token
    if user.plaid_user_token:
        print("User already has a Plaid user token.")
        return redirect(url_for("main.user"))

    print("User ID:", user.id + unique_id)
    first_name = request.form["first-name"]
    user.name = first_name

    # Pull form data to create new Plaid user via the user_token endpoint
    create_user_request = UserCreateRequest(
        client_user_id=str(user.id + unique_id),  # Unique database identification
        consumer_report_user_identity=ConsumerReportUserIdentity(
            # Retrieve and convert form data
            first_name=first_name,
            last_name=request.form["last-name"],
            phone_numbers=[request.form["phone"]],
            emails=[user.email],
            date_of_birth=datetime.date(2000, 2, 22),
            primary_address=AddressData(
                city=request.form["city"],
                region=request.form["state-province"],
                street=request.form["address-line"],
                postal_code=request.form["zip-code"],
                country='US'
            )
        )
    )

    # Generate & update user with user_id & user_token
    try:
        # Get JSON Response & parse need values
        response = plaid_client.user_create(create_user_request)
        user_id = response['user_id']
        user_token = response['user_token']

        print("create_new_user() route reponse: ", response)

        # Update user account & commit to database
        user.plaid_user_id = user_id
        user.plaid_user_token = user_token
        db.session.commit()

        # Return the user_id to be used by create_link_token
        return redirect(url_for("main.home"))

    except Exception as e:
        print(f"Error creating Plaid user - from create_new_user(): {e}")
        return jsonify({"error": "Failed to create Plaid user"}), 400

# Step 1: Client creates a Link token (One-time password)
@main.route('/create_link_token', methods=['POST'])
def create_link_token():
    if "user" in session:
        # Get current user
        current_user = User.query.filter_by(email=session["user"]).first()
        # Debugging: check session contents
        print("Session contents - From start():", session)

        # Get current user_id
        user_id = current_user.plaid_user_id
        print("Plaid User ID: ", user_id)

        # Get current user_token
        user_token = current_user.plaid_user_token
        print("Plaid User Token: ", user_token)

        # Get user object from user_id
        user_object = LinkTokenCreateRequestUser(
            client_user_id=user_id
        )

        # Required user information for link token
        link_request = LinkTokenCreateRequest(
            user=user_object,
            user_token=user_token,
            client_name="Aki Financial Assistant",
            products=[Products('auth'), Products(
                'transactions'), Products('income_verification')],
            country_codes=[CountryCode('US')],
            language="en",
            enable_multi_item_link=True,
            income_verification=LinkTokenCreateRequestIncomeVerification(
                income_source_types=[IncomeVerificationSourceType('bank')],
                bank_income=LinkTokenCreateRequestIncomeVerificationBankIncome(
                    days_requested=30
                )
            )
        )

        try:
            create_token_response = plaid_client.link_token_create(
                link_request)
            print("Link token create request response:", create_token_response)
            return jsonify({
                "link_token": create_token_response['link_token'],
                "user_email": current_user.email,
            })
        except Exception as e:
            print(f"Error creating link token: {e}")
            return jsonify({"error": "Failed to create link token"}), 500
    else:
        print("No user in session at route: create_link_token()")
        return jsonify({"error": "Failed to create link token - User Not Logged in"})


access_token = None
item_id = None

# Step 2: Server requests a Link token from PLAID
@main.route('/exchange_public_token', methods=['POST'])
def exchange_public_token():
    # Recieve link token from frontend & retrieve API object from /link/token/get endpoint
    try:
        link_token = request.form['link_token']
        link_token_request = LinkTokenGetRequest(link_token=link_token)
        link_token_response = plaid_client.link_token_get(link_token_request)
        # Debug: print("LinkTokenGetRequest - @exchange_public_token():", link_token_response)
    except Exception as e:
        print("Error occurred while calling LinkTokenGetRequest from @exchange_public_token():", e)
        return jsonify({"error": "Failed to retrieve public tokens from link token"})

    # Get the each public token from the multi-item link
    public_tokens = []

    for session in link_token_response.get('link_sessions', []):
        results = session.get('results', {})
        item_add_results = results.get('item_add_results', [])

        for item in item_add_results:
            public_token = item.get('public_token')
            if public_token:
                public_tokens.append(public_token)

    # Debug: Print public tokens
    print("Public Tokens:", public_tokens)

    try:
        # Ensure the current user is logged in and their email is in the session
        current_user_email = request.form['user_email']
        print("@exchange_public_token, current user email:", current_user_email)
        if not current_user_email:
            return jsonify({"error": "User is not logged in"})

        current_user = User.query.filter_by(email=current_user_email).first()
        print("@exchange_public_token, current user:", current_user)
        if not current_user:
            return jsonify({"error": "User not found"})

        for public_token in public_tokens:

            print(f"Exchanging Public Token ({
                  public_token}) via exchange_public_token()")

            # Call Plaid API
            exchange_request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )

            # Exchange the public token for an access token
            response = plaid_client.item_public_token_exchange(
                exchange_request)
            print("Item public token exchange request's response :):", response)

            # Parse JSON values
            access_token = response['access_token']
            item_id = response['item_id']
            # institution_name = response['institution_name']

            # These values should be saved to a persistent database and
            # associated with the currently signed-in user
            save_connection = current_user.add_bank_connection(
                current_user_email, access_token, item_id, "Aki Financial AI")
            print("Created new connection via @exchange_public_token():",
                  save_connection)

        # Use the access token to retrieve account information, transactions, etc.
        # Return a URL for redirection
        return jsonify({'redirect_url': '/user'}), 200

    except Exception as e:
        print("Error during multi-link exchange @exchange_public_token():", e)
        return jsonify({'error': str(e)})

# Sync User Transactions
@main.route('/sync_transactions', methods=['POST'])
def sync_transactions(access_token, user_id):
    # Verify user is logged in
    if not "user" in session:
        print("@sync_transactions - User not logged in.")
        return redirect(url_for("main.login"))

    try:
        # Retrieve the latest cursor
        cursor = get_latest_cursor(user_id, access_token)
        if cursor == None or "null":
            cursor = "" # Assign empty string if NoneType

        # Initialize variables
        added, modified, removed = [], [], []
        has_more = True

        # Fetch transactions from Plaid
        while has_more:
            # Call sync transactions
            transaction_request = TransactionsSyncRequest(access_token = access_token, cursor = cursor)
            response = plaid_client.transactions_sync(transaction_request)
            # Debug: print("@sync_transactions - Response:", response)

            # Collect transaction updates
            added.extend(response["added"])
            modified.extend(response["modified"])
            removed.extend(response["removed"])
            has_more = response["has_more"]
            cursor = response["next_cursor"]

            # Debug: Print the number of transactions added, modified, and removed
            print(f"Added Transaction: {len(response['added'])}")
            print(f"Modified Transactions: {len(response['modified'])}")
            print(f"Removed Transactions: {len(response['removed'])}")

        # Update the latest cursor & transactions in database
        user = User.query.filter_by(id = user_id).first()
        update_latest_cursor(user, access_token, cursor)
        apply_transaction_updates(user_id, added, modified, removed)

        return jsonify({"message": "Transactions synchronized sucessfully!"}), 200

    except Exception as e:
        print(f"@sync_transacions - Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get user's income
@main.route('/get_bank_income', methods=['POST'])
def get_bank_income(user_token):
    try:
        # Get user
        user = User.query.filter_by(email=session["user"]).first()

        get_bank_income_request = CreditBankIncomeGetRequest(
            user_token=str(user_token),
            options=CreditBankIncomeGetRequestOptions(
                count=1
            )
        )

        bank_income_response = plaid_client.credit_bank_income_get(get_bank_income_request)

        # Extract earning from JSON
        total_amounts_list = []
        total_earned = 0

        for bank_income in bank_income_response["bank_income"]:
            bank_income_summary = bank_income.get("bank_income_summary", {})

            # Check historical summary
            for historical in bank_income_summary.get("historical_summary", []):
                total_amounts = historical.get("total_amounts", [])
                for amount_entry in total_amounts:
                    total_amounts_list.append(amount_entry["amount"])

            # Check main total_amounts
            for amount_entry in bank_income_summary.get("total_amounts", []):
                total_earned += amount_entry["amount"]
                total_amounts_list.append(amount_entry["amount"])

        # Add random earnings for testing
        random_number = 0
        user_income = user.income
        # print("@get_bank_income - Attempting to Assign User Income!")
        if user_income <= 999 and fake_data:
            # Generates a random float between 999 and 4999
            random_number = random.uniform(999, 4999)

            # Add total_earned & fake data for testing purposes
            # print("@get_bank_income - Random Income!")
            user_income = round(total_earned + random_number, 2)

            # Commit changes
            user.assign_income(user.email, user_income)
            db.session.commit()

        # Debug: Print updated income
        print("@get_bank_income - Updated user income:", user.income)

        return jsonify({"user_income": user_income, "total_amounts_list": total_amounts_list})
    except Exception as e:
        print("Error - @get_bank_income(): ", e)
        return jsonify({'error': str(e)}), 400

# Decorator
@main.route("/")
def home():
    return render_template("index.html")


@main.route("/view")
def view():
    return render_template("view.html", users=User.query.all(), transactions=Transaction.query.all())


@main.route("/expenses")
def expenses():
    if "user" in session:
        # Create Dictionary of Expenses to be passed as JSON
        expensesDict = []

        # Query all associated user transactions (expenses)
        current_user = User.query.filter_by(email=session["user"]).first()
        user_transactions = Transaction.query.filter_by(
            user_id=current_user.id).all()

        # Append each expense to the dictionary
        for transaction in user_transactions:
            if transaction.amount >= 0:
                expensesDict.append({
                    "id": transaction.transaction_id,
                    "date": transaction.date,
                    "description": transaction.description,
                    "category": transaction.category,
                    "amount": transaction.amount
                })

        # Debug: print("Dictionary of Expenses:", expensesDict)
        return jsonify(expensesDict)
    else:
        print("No user in session: @/expenses")


@main.route("/login", methods=["POST", "GET"])
def login():
    """
    1) Render login page
    2) Pull form data
    3) Create account if new account
    4) Open Plaid Link if new account
    """
    if request.method == "POST":

        # Retrieve user's account credentials
        # name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Ensure account email doesn't already exist & email is valid
        if validate_login(email, password):

            session.permanent = True  # Allows the user to stay logged in by default for 5 days
            session['user'] = email  # Replace with database's unique int

            # If email dosen't already exist in the database
            # create new user account, then intialize Plaid link
            if create_new_user_account(email, password):
                print("Created new user! - From routes: login()")
                # Load get started page to start link process
                # When a new user is created
                return redirect(url_for("main.start"))
            else:
                flash("Login Successful!")
                # print(f"{name} logged in.")
                return redirect(url_for("main.user"))  # Redirect to user page

        else:
            flash("Invalid username/password")
            return render_template("login.html")

    else:  # Get Method
        # If the user's login information is still in the session, redirect them to user page
        if "user" in session:
            flash("Already Logged In!")
            return redirect(url_for("main.user"))
        # Outerwise redirect the user to login page
        return render_template("login.html")


@main.route("/start", methods=["POST", "GET"])
def start():
    # Debugging: check session contents
    print("Session contents - From start():", session)

    if "user" in session:  # Check if user is logged in
        if request.method == "POST":
            print("POST REQUEST")

            # Fetch user by email
            user = User.query.filter_by(email=session["user"]).first()

            if create_new_user():
                create_link_token(user)

        # If it's a GET request (default)
        else:
            return render_template("start.html")  # Show the setup form

    else:
        # Redirect the user to login page if not logged in
        return render_template("login.html")


@main.route("/user", methods=["POST", "GET"])
def user():
    # Verify user if still logged in
    if not "user" in session:
        print("@user - User not logged in.")
        return redirect(url_for("main.login"))

    try:
        # Get current user
        current_user = User.query.filter_by(email=session["user"]).first()
        print("@user - Current User:", current_user)

        # Get the each access tokens & cursors for each linked item
        user_access_tokens = []
        user_latest_cursors = []

        # Debug: print("@user - Plaid Connections:", current_user.plaid_connections)

        # Get user's access tokens & cursors *in-order
        for item in current_user.plaid_connections:
            try:
                user_access_tokens.append(item["access_token"])
                user_latest_cursors.append(item.get("latest_cursor", None)) # Default None
            except Exception as e:
                print("@user - Missing key in plaid_connections item:", e)

        # Debug:
        print("@user - Access Tokens:", user_access_tokens)
        print("@user - Latest Cursors:", user_latest_cursors)

    except Exception as e:
        print("@user - Error occured retrieving user access tokens or cursors:", e)

    # Check if user has Plaid access tokens
    if user_access_tokens:
        try:
            for index_key, access_token in enumerate(user_access_tokens):
                # Debug: print("Accessing User access token:", access_token)

                # Intialize cursor corresponding to access_token
                latest_cursor = user_latest_cursors[index_key]

                # Debug: print("Retrieving User cursor", latest_cursor)

                # Sync income
                get_bank_income(user_token = current_user.plaid_user_token)
                print("@user - Bank income synced:", current_user.income)

                # Sync transactions
                sync_transactions(access_token = access_token, user_id = current_user.id)
                print("@user - Transactions synced for access token:", access_token)

            # Reload user object to ensure data is synced
            db.session.refresh(current_user)

        except Exception as e:
            print(f"@user - Error syncing: {e}")
            return jsonify({"error": "Failed to sync."}), 500

        # Prepare financial data to be passed to user.html
        pie_chart = create_pie(current_user) # Plotly
        cashflow_value = get_cashflow_difference(current_user) # Helper
        cashflow_percentage = (cashflow_value / current_user.income * 100 if current_user.income else 0)

        # GET request (default)
        return render_template(
            "user_new.html",
            name = current_user.name,
            pie = pie_chart,
            cashflow_value = cashflow_value,
            cashflow_percentage = cashflow_percentage,
            transactions_redirect = "/transactions"
            # cashflow_statment=cashflow_statment
        )


@main.route("/transactions")
def transactions():
    # Verify user if still logged in
    if not "user" in session:
        print("@transactions - User not logged in.")
        return redirect(url_for("main.login"))

    # Fetch expenses by calling @expenses route
    expense_response = expenses()

    # Attempt to extract JSON data from response
    try:
        # Built in Flask function "get_json()" to parse response
        transactions = expense_response.get_json()
        # Debug: print("@transactions - Parsed Transactions:", transactions)
    except Exception as e:
        print("Error parsing transactions:", str(e))
        transactions = []

    for transaction in transactions:
        # Format all amounts as current (US format) - Example: $50.22
        transaction['formatted_amount'] = f"- ${transaction['amount']:,.2f}"

        # Format all date's as strings - Example: YYYY-MM-DD
        # Debug: print("Transaction Date:", transaction["date"])
        # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        transaction_date = datetime.datetime.strptime(
            transaction["date"], "%a, %d %b %Y %H:%M:%S %Z")
        transaction["formatted_date"] = transaction_date.strftime(
            "%a, %d %b %Y")  # e.g., "Fri, 22 Dec 2024"

    if request.method == "POST":
        ...
    else:  # GET request (render HTML)
        return render_template("transactions.html", transactions=transactions)


@main.route("/update_transaction", methods=["POST"])
def update_transaction():
    if not "user" in session:
        print("@transactions - User not logged in.")
        return redirect(url_for("main.login"))

    try:
        data = request.get_json()
        # Debug: print("@update_transaction - Data:", data)
        transaction_id = data["id"]
        field = data["field"]
        value = data["value"]

        user = session["user"]

        # Parse date into datetime format used by database
        if field == "date":
            input_date = datetime.datetime.strptime(value, "%a, %d %b %Y")
            value = input_date.date()
            print("@update_transaction - Updated Date:", value)

        # Remove currency formatting
        if field == "amount":
            # Remove non-numeric characters
            value = value.replace('$', '').replace(',', '').replace('-', '')
            print("@update_transaction - Updated Amount:", value)

        # Update the transaction in the database via update_transaction_in_db()
        update_transaction_in_db(user, transaction_id, field, value)

        # Return a JSON response indicating success
        return jsonify({"status": "success", "message": "@update_transaction - Transaction updated."}), 200

    except Exception as e:
        print("@update_transaction - Error updating transaction:", str(e))
        return jsonify({"status": "error", "message": "@update_transaction - Failed to update transaction."})


@main.route("/delete_transaction", methods=["POST"])
def delete_transaction():
    if not "user" in session:
        print("@delete_transaction - User not logged in.")
        return redirect(url_for("main.login"))

    try:
        data = request.get_json()
        # Debug:
        print("@update_transaction - Data:", data)

    except Exception as e:
        print("@delete_transaction - Error deleting transaction:", str(e))
        return jsonify({"status": "error", "message": "@delete_transaction - Failed to delete transaction."})


@main.route("/logout")
def logout():
    if "user" in session:
        user = session["user"]
        flash(f"You've successfully logged out, {user}", "info")
    else:
        flash(f"You're already logged out.")
    # Remove the username from the session if it's there
    session.pop("user", None)
    session.pop("email", None)
    return redirect(url_for("main.login"))
