.PHONY: run test update-cache clean email-preview email-test email-test-service

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
#  Email Testing
# ====================================================================================

email-preview:
	@echo "Generating email preview..."
	@python email_content_generator.py preview
	@echo "Preview files created: email_preview.html and email_preview.txt"

email-test:
	@echo "Email testing requires an email address"
	@echo "Usage: make email-test EMAIL=your@email.com"
	@if [ -z "$(EMAIL)" ]; then \
		echo "Error: EMAIL parameter required"; \
		exit 1; \
	fi
	@echo "Sending test email to $(EMAIL)..."
	@python email_content_generator.py test $(EMAIL)

email-test-service:
	@echo "Email service testing requires an email address"
	@echo "Usage: make email-test-service EMAIL=your@email.com"
	@if [ -z "$(EMAIL)" ]; then \
		echo "Error: EMAIL parameter required"; \
		exit 1; \
	fi
	@echo "Testing email service with $(EMAIL)..."
	@python email_service.py test $(EMAIL)

# ====================================================================================
#  Housekeeping
# ====================================================================================

clean:
	@echo "Cleaning up..."
	@rm -rf cache
	@rm -f aaii_response.html aaii_page_scrape_test.html
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete 