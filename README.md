# AKi Personal Finance Assistant
#### Video Demo: <URL HERE>

#### Description:
The **AKi Personal Finance Assistant** is a Python-based web application designed to help users manage their finances by tracking income, expenses, and calculating user return on investment (ROI) for their financial goals. The application integrates with the **Plaid API** to securely pull financial data such as transactions & income details for user's bank accounts, providing users with real-time insights into their financial health.

#### Key Features:
- **User Authentication:** Secure login & account creation functionality via Plaid Link.
- **Budget Tracking:** Users can input, update, & categorize spending transactions.
- **Income Tracking:** Plaid API fetches income data & user ROI is calculated.
- **Transaction Management:** Ability for users to add, edit, and remove financial transactions.

This application uses **Flask** for backend and **SQLAlchemy** for data storage, providing an efficient & scalable solution for managing personal finance.

#### Technologies Used:
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
   ```bash
   git clone https://github.com/AKhalil22/Aki-Personal-Finance-Assistant.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environmental variables (e.g., Plaid API keys):
   - Might need to sign up for Plaid API & change configuration API keys:
     ```python
     api_key = {
         "clientId": "",
         "secret": ""
     }
     ```

4. Run:
   ```bash
   python project.py
   ```

---

#### TODO:
- [ ] Integrate Google Places API for auto-filling sign-up.
- [ ] Implement AI budgeting features.
