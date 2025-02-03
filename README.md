 # AKi Personal Finance Assitant
    #### Video Demo:  <URL HERE>
    #### Description:
    The **Aki Personal Finance Assistant** is a Python-based web application designed to help users manange their finanances by tracking income, expenses, and calculate user return on investment (ROI) for their finanacial goals. The application integrates with the **Plaid API** to securely pull finanacial data such as transactions & income details for user's bank accounts., providing user with real-time insights into their financial health.

    Key Features:
    - **User Authentication:** Secure login & account creation fucntionality via Plaid Link.
    - **Budget Tracking:** Users can input, update, & categorize spending transactiosn.
    - **Income Tracking:** Plaid API fetches income data & user ROI is calculated.
    - **Transaction Management:** Ability for users to add, edit, and remove financial transactions.

    This application uses **Flask** for backend and **SQLAlchemy** for data storage, providing an efficient & scalable solution for manging personal finance.

    Technologies Used:
    - Python
    - Flask (Web Framework)
    - SQLAlchemy (ORM for database)
    - Plaid API (Financial Data Integration)
    - Bootstrap (UI/UX Design)
    - Jinja2 (HTML Templating)
    - unittest (Testing Framework)

    ---

    #### Installation:

    1. Clone this repository:
      ```back
      git clone <REPOSITORY_URL>

    2. Install dependencies
      pip install -r requirements.txt

    3. Set up enviormental variables (e.g. Plaid API keys):
      - Might need to sign up for Plaid API & change configuration API keys:
          api_key = {
          "clientId": "",
          "secret": ""
        }

     4. Run: python project.py

    TODO:
    - Add more detailed unit tests.
    - Improve UI/UX design.
    - Add multi-user support.
    - Expand budgeting features.

