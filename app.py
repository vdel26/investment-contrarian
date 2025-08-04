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
    try:
        fng_data = get_fear_and_greed_data()
        aaii_data = get_aaii_sentiment_data()
        ssi_data = get_ssi_data()
        overall = get_overall_analysis_data()

        # Log the data status for debugging
        print(f"F&G data: {'error' in fng_data if isinstance(fng_data, dict) else 'loaded'}")
        print(f"AAII data: {'error' in aaii_data if isinstance(aaii_data, dict) else 'loaded'}")
        print(f"SSI data: {'error' in ssi_data if isinstance(ssi_data, dict) else 'loaded'}")
        print(f"Overall data: {'error' in overall if isinstance(overall, dict) else 'loaded'}")

        # Check if we have any data at all
        has_fng = isinstance(fng_data, dict) and "error" not in fng_data
        has_aaii = isinstance(aaii_data, dict) and "error" not in aaii_data
        has_ssi = isinstance(ssi_data, list) or (isinstance(ssi_data, dict) and "error" not in ssi_data)
        has_overall = isinstance(overall, dict) and "error" not in overall

        # If no cache files exist, return a helpful message
        if not (has_fng or has_aaii or has_ssi or has_overall):
            return jsonify({
                "error": "Market data is currently being updated. Please try again in a few minutes.",
                "status": "initializing",
                "message": "This appears to be the first deployment. Cache files are being generated."
            }), 503  # Service Unavailable
        
        # If some data is missing, log but continue with what we have
        if (isinstance(fng_data, dict) and "error" in fng_data) or (isinstance(aaii_data, dict) and "error" in aaii_data):
            error_details = []
            if isinstance(fng_data, dict) and "error" in fng_data:
                error_details.append(f"F&G: {fng_data['error']}")
            if isinstance(aaii_data, dict) and "error" in aaii_data:
                error_details.append(f"AAII: {aaii_data['error']}")
            
            print(f"Market data errors (proceeding with available data): {'; '.join(error_details)}")
            # Don't return error - proceed with whatever data we have

        combined_data = {
            "fear_and_greed": fng_data,
            "aaii_sentiment": aaii_data,
            "bank_of_america_ssi": ssi_data,
            "overall_analysis": overall
        }
        
        return jsonify(combined_data)
    
    except Exception as e:
        print(f"Unexpected error in get_market_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error loading market data"}), 500


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


@app.route('/debug/paths', methods=['GET'])
def debug_paths():
    """Debug endpoint to check file paths and permissions."""
    import os
    from pathlib import Path
    from config import CACHE_DIR, DATA_DIR, LOGS_DIR, IS_PRODUCTION
    
    debug_info = {
        'is_production': IS_PRODUCTION,
        'current_working_directory': str(Path.cwd()),
        'config_paths': {
            'cache_dir': str(CACHE_DIR),
            'data_dir': str(DATA_DIR),
            'logs_dir': str(LOGS_DIR)
        },
        'directory_status': {
            'cache_exists': CACHE_DIR.exists(),
            'data_exists': DATA_DIR.exists(),
            'logs_exists': LOGS_DIR.exists()
        },
        'cache_files': {},
        'environment_vars': {
            'FLASK_ENV': os.environ.get('FLASK_ENV'),
            'has_openai_key': bool(os.environ.get('OPENAI_API_KEY')),
            'has_serpapi_key': bool(os.environ.get('SERPAPI_KEY')),
            'has_resend_key': bool(os.environ.get('RESEND_API_KEY'))
        }
    }
    
    # Check cache files
    cache_files = ['fng_cache.json', 'aaii_cache.json', 'ssi_cache.json', 'overall_cache.json']
    for cache_file in cache_files:
        file_path = CACHE_DIR / cache_file
        debug_info['cache_files'][cache_file] = {
            'exists': file_path.exists(),
            'path': str(file_path)
        }
        if file_path.exists():
            try:
                stat = file_path.stat()
                debug_info['cache_files'][cache_file]['size'] = stat.st_size
                debug_info['cache_files'][cache_file]['modified'] = stat.st_mtime
            except Exception as e:
                debug_info['cache_files'][cache_file]['error'] = str(e)
    
    return jsonify(debug_info)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    import os
    from datetime import datetime
    
    try:
        # Check if cache files exist
        cache_files = {
            'fng_cache': os.path.exists('cache/fng_cache.json'),
            'aaii_cache': os.path.exists('cache/aaii_cache.json'),
            'ssi_cache': os.path.exists('cache/ssi_cache.json'),
            'overall_cache': os.path.exists('cache/overall_cache.json')
        }
        
        # Check subscriber data
        subscribers_exist = os.path.exists('data/subscribers.json')
        
        # Check environment variables
        required_env_vars = ['OPENAI_API_KEY', 'SERPAPI_KEY', 'RESEND_API_KEY', 'FROM_EMAIL']
        env_vars_ok = all(os.environ.get(var) for var in required_env_vars)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'cache_files': cache_files,
            'subscribers_file': subscribers_exist,
            'environment_configured': env_vars_ok,
            'version': '1.0.0'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


if __name__ == '__main__':
    import os
    from config import validate_production_config, IS_PRODUCTION
    
    try:
        # Validate production configuration
        validate_production_config()
        
        # Production configuration
        port = int(os.environ.get('PORT', 5001))
        debug = not IS_PRODUCTION
        
        print(f"Starting Flask app in {'production' if IS_PRODUCTION else 'development'} mode on port {port}")
        
        app.run(host='0.0.0.0', port=port, debug=debug)
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please set the required environment variables and try again.")
        exit(1)
    except Exception as e:
        print(f"Failed to start application: {e}")
        exit(1) 