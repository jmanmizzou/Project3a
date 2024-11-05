from flask import Flask, render_template, request
import requests
import pygal
from datetime import datetime
import os

app = Flask(__name__)
API_KEY = 'K3EMMNZ5OI92KFCA' 

# Function to fetch and validate stock data
def get_stock_data(symbol, api_key, time_series_choice):
    time_series_functions = {
        '1': 'TIME_SERIES_INTRADAY',
        '2': 'TIME_SERIES_DAILY',
        '3': 'TIME_SERIES_WEEKLY',
        '4': 'TIME_SERIES_MONTHLY'
    }
    function = time_series_functions.get(time_series_choice, 'TIME_SERIES_DAILY')
    url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={api_key}'
    
    if function == 'TIME_SERIES_INTRADAY':
        url += '&interval=60min'  # Set interval if using intraday data

    try:
        response = requests.get(url)
        data = response.json()
        print("Full API Response:", data)

        # Check if the API request was successful and the symbol is valid
        if 'Error Message' in data:
            return False, "Invalid stock symbol. Please try again."
        elif 'Note' in data:
            return False, "API limit reached. Please wait before trying again."
        elif function == 'TIME_SERIES_INTRADAY' and 'Time Series (60min)' not in data:
            return False, "Intraday data not available. Please try again."
        elif function == 'TIME_SERIES_DAILY' and 'Time Series (Daily)' not in data:
            return False, "Daily data not available. Please try again."
        elif function == 'TIME_SERIES_WEEKLY' and 'Weekly Time Series' not in data:
            return False, "Weekly data not available. Please try again."
        elif function == 'TIME_SERIES_MONTHLY' and 'Monthly Time Series' not in data:
            return False, "Monthly data not available. Please try again."
        else:
            return True, data # Return the data itself when successful
    
    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {str(e)}")
        return False, f"Error fetching data: {str(e)}"

# Function to fetch and plot stock data  
def fetch_and_plot_stock_data(symbol, start_date, end_date, chart_type, api_key, time_series_choice):
    is_valid, data = get_stock_data(symbol, api_key, time_series_choice)
    if not is_valid:
        return None, data  # Return error message for display

    time_series_data = get_time_series(data, time_series_choice)
    date_format = '%Y-%m-%d %H:%M:%S' if time_series_choice == '1' else '%Y-%m-%d'

    # Filter data by date range
    filtered_data = {date: values for date, values in time_series_data.items()
                     if start_date <= datetime.strptime(date, date_format) <= end_date}

    if not filtered_data:
        return None, "No data available for the selected date range."

    # Prepare data for plotting
    dates = list(filtered_data.keys())
    open_prices = [float(data['1. open']) for data in filtered_data.values()]
    high_prices = [float(data['2. high']) for data in filtered_data.values()]
    low_prices = [float(data['3. low']) for data in filtered_data.values()]
    close_prices = [float(data['4. close']) for data in filtered_data.values()]

    if not dates or not open_prices:
        return None, "No data available for the selected date range."

    # Set chart title and labels
    chart = pygal.Line(x_label_rotation=45) if chart_type == 'line' else pygal.Bar(x_label_rotation=45)
    chart.title = f'{symbol} Stock Data from {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}'
    chart.x_labels = dates

    # Add each series to the chart (Open, High, Low, Close)
    chart.add('Open', open_prices)
    chart.add('High', high_prices)
    chart.add('Low', low_prices)
    chart.add('Close', close_prices)

    if not os.path.exists('static'):
        os.makedirs('static')

    chart_path = f'static/{symbol}_stock_data_chart.svg'
    chart.render_to_file(chart_path)
    return chart_path, None

# Function to get time series data
def get_time_series(data, time_series):
    if time_series == '1':
        return data.get('Time Series (60min)', {})
    elif time_series == '2':
        return data.get('Time Series (Daily)', {})
    elif time_series == '3':
        return data.get('Weekly Time Series', {})
    elif time_series == '4':
        return data.get('Monthly Time Series', {})
    else:
        return data.get('Time Series (Daily)', {})

# Define a route for the root URL and allow both GET and POST requests
@app.route("/", methods=["GET", "POST"])
def index():
    chart_path = None
    error = None

    # Check if the request method is POST 
    if request.method == "POST":
        symbol = request.form["symbol"]
        chart_type = request.form["chart_type"]
        time_series_choice = request.form["time_series"]

        # Try to parse the start and end dates from the form inputs
        try:
            start_date = datetime.strptime(request.form["start_date"], '%Y-%m-%d')
            end_date = datetime.strptime(request.form["end_date"], '%Y-%m-%d')
        except ValueError:
            error = "Please enter valid start and end dates in YYYY-MM-DD format."
            return render_template("index.html", chart_path=chart_path, error=error)
        
        # Call function to fetch and plot stock data, store chart path or error message
        chart_path, error = fetch_and_plot_stock_data(symbol, start_date, end_date, chart_type, API_KEY, time_series_choice)

    #render the index.html 
    return render_template("index.html", chart_path=chart_path, error=error)

# Run flask app with debuggin enabled
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
