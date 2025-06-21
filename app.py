from flask import Flask, send_from_directory, jsonify
from data_provider import get_fear_and_greed_data, get_aaii_sentiment_data, get_overall_analysis_data

app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def serve_index():
    # The root now serves static files, so we can't have a specific route for it.
    # Instead, we rely on Flask to automatically serve 'index.html' from the static folder.
    # If a user goes to '/', Flask will look for 'index.html' in the static_folder.
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/market-data')
def get_market_data():
    fng_data = get_fear_and_greed_data()
    aaii_data = get_aaii_sentiment_data()
    overall = get_overall_analysis_data()

    # The getter functions will return a dictionary with an 'error' key if they fail
    if "error" in fng_data or "error" in aaii_data:
        # We can optionally log the specific errors here
        return jsonify({"error": "Failed to load market data from cache."}), 500

    combined_data = {
        "fear_and_greed": fng_data,
        "aaii_sentiment": aaii_data,
        "overall_analysis": overall
    }
    
    return jsonify(combined_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 