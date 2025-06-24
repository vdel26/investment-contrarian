.PHONY: run test update-cache clean

# ====================================================================================
#  Development Tasks
# ====================================================================================

run:
	@echo "Starting Flask server on http://127.0.0.1:5001"
	@python app.py

test:
	@echo "Running tests..."
	@python -m unittest discover -s tests -p 'test_*.py'

update-cache:
	@echo "Updating data cache..."
	@python update_cache.py

# ====================================================================================
#  Housekeeping
# ====================================================================================

clean:
	@echo "Cleaning up..."
	@rm -rf cache
	@rm -f aaii_response.html aaii_page_scrape_test.html
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete 