# 3 Additional custom functions cannot be nested in classes or other functions
'''
Personal Finance Assistant - Key Features:
1) Budget Tracking
2) Financial Goals
3) Basic Recommendations based on current budget/spending & future goals

Development Environment: Flask for web interface
User Input/Interface: Gui in web form to get user income, expenses, and financial goals
Create Classes to store: User, Expenses, Budget

Resources:
Create Flask App: https://www.youtube.com/playlist?list=PLzMcBGfZo4-n4vJJybUVV3Un_NFS5EOgX
Figma + Builder.io: https://www.figma.com/design/K1e6BEfJrFrTNXJY3ZUhU7/Free-Figma-Website-Landing-Pages---Startup-App-(Community)?node-id=0-3004&p=f&m=dev


Documentation(s):
Flask SQL Alchemy: https://flask-sqlalchemy.readthedocs.io/en/3.1.x/
Flask: https://flask.palletsprojects.com/en/3.0.x/
BootStrap: https://getbootstrap.com/
Plotly: https://plotly.com/python/
HTML: https://developer.mozilla.org/en-US/

Plaid: https://plaid.com/docs/
    - Client Library (GitHub): https://github.com/plaid/plaid-python

Google Places: https://developers.google.com/maps/documentation/javascript/place-autocomplete#javascript
    - GitHub: https://github.com/googlemaps/js-samples/blob/3a7f666640b90fcbed4b17b8f6e59f9e371f4263/dist/samples/places-autocomplete-multiple-countries/docs/index.js#L40-L43

REST Countries: https://restcountries.com/
'''
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug = True) # Run Webapp

