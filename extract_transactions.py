import requests
from bs4 import BeautifulSoup
import datetime
from prettytable import PrettyTable

# Define your credentials and URLs
username = 'Elvin Ali'
password = 'clxict0vMx'
login_url = 'https://portal.mlmproperty.co.uk/LoginPage.aspx'
history_url = 'https://portal.mlmproperty.co.uk/History.aspx'

# Initialize a session
session = requests.Session()

def login():
    # Get login page to retrieve VIEWSTATE and EVENTVALIDATION
    response = session.get(login_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract necessary form fields
    viewstate = soup.find(id='__VIEWSTATE')['value']
    viewstate_generator = soup.find(id='__VIEWSTATEGENERATOR')['value']
    eventvalidation = soup.find(id='__EVENTVALIDATION')['value']
    
    # Create payload for login
    form_data = {
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstate_generator,
        '__EVENTVALIDATION': eventvalidation,
        'ctl00$ctl00$baseContentPlaceHolder$mainContentPlaceHolder$UserName': username,
        'ctl00$ctl00$baseContentPlaceHolder$mainContentPlaceHolder$Password': password,
        'ctl00$ctl00$baseContentPlaceHolder$mainContentPlaceHolder$loginButton': 'Login'
    }
    
    # Post the login request
    login_response = session.post(login_url, data=form_data)
    login_response.raise_for_status()
    
    if 'Logout' not in login_response.text:
        raise Exception("Login failed. Please check your credentials.")
    else:
        print("Login successful!")

def fetch_history_page(viewstate, viewstate_generator, eventvalidation, from_date, to_date, page=1):
    form_data = {
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstate_generator,
        '__EVENTVALIDATION': eventvalidation,
        '__EVENTTARGET': 'ctl00$ctl00$baseContentPlaceHolder$mainContentPlaceHolder$_history$_historyGrid',
        '__EVENTARGUMENT': f'Page${page}',
        'ctl00$ctl00$baseContentPlaceHolder$mainContentPlaceHolder$_history$_fromDate': from_date,
        'ctl00$ctl00$baseContentPlaceHolder$mainContentPlaceHolder$_history$_toDate': to_date,
        'ctl00$ctl00$baseContentPlaceHolder$mainContentPlaceHolder$_history$_searchButton': 'Search',
        '__LASTFOCUS': '',
        '_scriptManager_TSM': ';;System.Web.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35:en-US:18f1b484-bbc5-4e2e-8ca4-477603537f34:ea597d4b:b25378d2;Telerik.Web.UI:en-US:65ded1fa-0224-45b6-a6df-acf9eb472a15:16e4e7cd:f7645509:22a6274a'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    history_response = session.post(history_url, data=form_data, headers=headers)
    history_response.raise_for_status()
    return history_response.content

def parse_transactions(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', {'id': 'baseContentPlaceHolder_mainContentPlaceHolder__history__historyGrid'})
    
    if not table:
        print("No transactions found.")
        return []
    
    transactions = []
    for row in table.select('tr.HistoryGridRow, tr.HistoryGridAlternatingRow'):
        columns = row.find_all('td')
        transaction = {
            'date': columns[0].text.strip(),
            'period_dates': columns[1].text.strip(),
            'description': columns[2].text.strip(),
            'due': columns[4].text.strip(),
            'paid': columns[5].text.strip(),
            'running_balance': columns[6].text.strip(),
        }
        transactions.append(transaction)
    
    return transactions

def fetch_all_transactions():
    # Get initial history page to retrieve VIEWSTATE and EVENTVALIDATION
    response = session.get(history_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract necessary form fields
    viewstate = soup.find(id='__VIEWSTATE')['value']
    viewstate_generator = soup.find(id='__VIEWSTATEGENERATOR')['value']
    eventvalidation = soup.find(id='__EVENTVALIDATION')['value']
    
    # Define the date range
    from_date = '2022-08-15'
    to_date = datetime.date.today().strftime('%Y-%m-%d')
    
    # Fetch the first page
    html_content = fetch_history_page(viewstate, viewstate_generator, eventvalidation, from_date, to_date, page=1)
    transactions = parse_transactions(html_content)
    
    # Parse the number of pages
    soup = BeautifulSoup(html_content, 'html.parser')
    pager = soup.find('tr', {'class': 'HistoryGridPager'})
    if pager:
        pages = pager.find_all('a')
        total_pages = int(pages[-1].text) if pages else 1
    else:
        total_pages = 1
    
    print(f"Total Pages Found: {total_pages}")
    
    # Fetch remaining pages and accumulate transactions
    for page in range(2, total_pages + 1):
        print(f"Fetching page {page}...")
        response = session.get(history_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        viewstate = soup.find(id='__VIEWSTATE')['value']
        viewstate_generator = soup.find(id='__VIEWSTATEGENERATOR')['value']
        eventvalidation = soup.find(id='__EVENTVALIDATION')['value']
        
        html_content = fetch_history_page(viewstate, viewstate_generator, eventvalidation, from_date, to_date, page=page)
        transactions.extend(parse_transactions(html_content))
    
    # Print total number of transactions
    print(f"Total number of transactions: {len(transactions)}")
    
    # Sort transactions by date in ascending order
    transactions = sorted(transactions, key=lambda x: datetime.datetime.strptime(x['date'], '%d/%m/%Y'))
    
    return transactions

def print_transactions(transactions):
    table = PrettyTable()
    table.field_names = ["Date", "Period Dates", "Description", "Due", "Paid", "Running Balance"]
    
    for transaction in transactions:
        table.add_row([transaction['date'], transaction['period_dates'], transaction['description'], transaction['due'], transaction['paid'], transaction['running_balance']])
    
    print(table)

if __name__ == "__main__":
    login()
    transactions = fetch_all_transactions()
    
    if transactions:
        print_transactions(transactions)
    else:
        print("No transactions found.")