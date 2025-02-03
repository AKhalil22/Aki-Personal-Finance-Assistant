from app.helpers import validate_login, create_new_user_account, apply_transaction_updates
from app.models import Transaction
from app import create_app

import datetime

def main():
    test_validate_login()
    test_create_new_user_account()


def test_validate_login():
    app = create_app() # Intialize "mock" app

    with app.app_context():
        assert validate_login("cs50dev@harvard.edu", "CS50P") == True # User has valid credentials


def test_create_new_user_account():
    app = create_app()

    with app.app_context():
        assert create_new_user_account("cs50dev@harvard.edu", "CS50P") == False # User already exists


def test_apply_transaction_updates():
    app = create_app()

    with app.app_context():
        # Sample API Object from Plaid API
        added = [{
        "account_id": "BxBXxLj1m4HMXBm9WZZmCWVbPjX16EHwv99vp",
        "account_owner": None,
        "amount": 0.01,
        "iso_currency_code": "USD",
        "unofficial_currency_code": None,
        "category": [
            "Shops",
            "Supermarkets and Groceries"
        ],
        "category_id": "19046000",
        "check_number": None,
        "counterparties": [
            {
            "name": "Walmart",
            "type": "merchant",
            "logo_url": "https://plaid-merchant-logos.plaid.com/walmart_1100.png",
            "website": "walmart.com",
            "entity_id": "O5W5j4dN9OR3E6ypQmjdkWZZRoXEzVMz2ByWM",
            "confidence_level": "VERY_HIGH"
            }
        ],
        "date": datetime.date(2023, 9, 24),
        "datetime": "2023-09-24T11:01:01Z",
        "authorized_date": "2023-09-22",
        "authorized_datetime": "2023-09-22T10:34:50Z",
        "location": {
            "address": "13425 Community Rd",
            "city": "Poway",
            "region": "CA",
            "postal_code": "92064",
            "country": "US",
            "lat": 32.959068,
            "lon": -117.037666,
            "store_number": "1700"
        },
        "name": "Test/Pending PURCHASE WM SUPERCENTER #1700",
        "merchant_name": "Walmart",
        "merchant_entity_id": "O5W5j4dN9OR3E6ypQmjdkWZZRoXEzVMz2ByWM",
        "logo_url": "https://plaid-merchant-logos.plaid.com/walmart_1100.png",
        "website": "walmart.com",
        "payment_meta": {
            "by_order_of": None,
            "payee": None,
            "payer": None,
            "payment_method": None,
            "payment_processor": None,
            "ppd_id": None,
            "reason": None,
            "reference_number": None
        },
        "payment_channel": "in store",
        "pending": False,
        "pending_transaction_id": "no86Eox18VHMvaOVL7gPUM9ap3aR1LsAVZ5nc",
        "personal_finance_category": {
            "primary": "GENERAL_MERCHANDISE",
            "detailed": "GENERAL_MERCHANDISE_SUPERSTORES",
            "confidence_level": "VERY_HIGH"
        },
        "personal_finance_category_icon_url": "https://plaid-category-icons.plaid.com/PFC_GENERAL_MERCHANDISE.png",
        "transaction_id": "lPNjeW1nR6CDn5okmGQ6hEpMo4lLNoSrzqDje",
        "transaction_code": None,
        "transaction_type": "place"
        }]

        # user_id, added, modified, removed
        apply_transaction_updates(1, added, [], [])

        # Attempt to Fetch transaction after database changes
        existing_transaction = Transaction.query.filter_by(transaction_id = "lPNjeW1nR6CDn5okmGQ6hEpMo4lLNoSrzqDje").first()

        assert existing_transaction is not None


if __name__ == "__main__":
    main()
