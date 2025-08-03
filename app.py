from flask import Flask, send_from_directory, jsonify, request
from data_provider import get_fear_and_greed_data, get_aaii_sentiment_data, get_ssi_data, get_overall_analysis_data
from subscribers import add_subscriber, remove_subscriber, get_subscriber_stats

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
    ssi_data = get_ssi_data()
    overall = get_overall_analysis_data()

    # The getter functions will return a dictionary with an 'error' key if they fail
    if "error" in fng_data or "error" in aaii_data:
        # We can optionally log the specific errors here
        return jsonify({"error": "Failed to load market data from cache."}), 500

    combined_data = {
        "fear_and_greed": fng_data,
        "aaii_sentiment": aaii_data,
        "bank_of_america_ssi": ssi_data,
        "overall_analysis": overall
    }
    
    return jsonify(combined_data)


@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    """Subscribe to daily email alerts."""
    try:
        # Get email from request
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({
                "success": False,
                "message": "Email address is required"
            }), 400
        
        email = data['email']
        
        # Add subscriber
        result = add_subscriber(email)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "An error occurred while processing your subscription"
        }), 500


@app.route('/api/unsubscribe', methods=['POST'])
def unsubscribe():
    """Unsubscribe from daily email alerts."""
    try:
        # Get email from request
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({
                "success": False,
                "message": "Email address is required"
            }), 400
        
        email = data['email']
        
        # Remove subscriber
        result = remove_subscriber(email)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "An error occurred while processing your unsubscription"
        }), 500


@app.route('/api/subscribers/stats', methods=['GET'])
def subscriber_stats():
    """Get subscriber statistics (for admin use)."""
    try:
        stats = get_subscriber_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve subscriber statistics"
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001) 