# Dynamic Market Sentiment Dashboard - Implementation Plan

This document outlines the architecture and step-by-step plan to convert the static `index.html` mockup into a dynamic, data-driven web application.

---

### 1. Architecture Overview

We will implement a simple client-server architecture to ensure the application is robust, maintainable, and scalable.

*   **Backend (Python & Flask):**
    *   **Purpose:** A lightweight server responsible for serving API requests. The core data fetching is handled by a separate background process.
    *   **Caching Strategy:** A proactive, file-based caching strategy is used. A separate background script (`update_cache.py`), triggered by cron jobs, will periodically fetch data from the external sources and store it in local JSON files. The Flask server reads directly from these files, ensuring fast and reliable responses.
    *   **Implementation Note:** The Flask application itself will remain stateless. It will read the cache file from the filesystem on *every* API request, rather than caching the contents in a long-lived global variable. This leverages the operating system's highly efficient file caching and guarantees that the app always serves the most up-to-date data written by the background job, avoiding stale data bugs.
    *   **Data Sources:**
        1.  **CNN Fear & Greed Index:** Fetched from the official JSON endpoint: `https://production.dataviz.cnn.io/index/fearandgreed/graphdata`
        2.  **AAII Sentiment Survey:** Processed from the weekly Excel file.
    *   **API:** It will expose a single, simple API endpoint: `/api/market-data`.

*   **Frontend (HTML, CSS, JavaScript):**
    *   **Purpose:** The user interface. It will be responsible for rendering the data provided by the backend.
    *   **Logic:** On page load, it will make a single call to the backend's `/api/market-data` endpoint. Once the data is received, JavaScript will dynamically populate the dashboard's components, updating values, colors, and charts.
    *   **Structure:** We will separate the HTML structure, CSS styling, and JavaScript logic into their own files (`index.html`, `style.css`, `app.js`) for better organization.

---

### 2. Step-by-Step Implementation Plan

We will build the application in two main phases.

#### Phase 1: Core Dashboard Implementation

**Step 1: Project Scaffolding & Basic Server**
- [ ] Set up the initial project structure (`app.py`, `data_provider.py`, `requirements.txt`, `static/`).
- [ ] In `app.py`, set up a minimal Flask server to serve the static `index.html` file.

**Step 2: Implement Data Providers**
- [ ] In `data_provider.py`, create a function `fetch_fear_and_greed()` to get and parse data from the CNN JSON endpoint.
- [ ] In `data_provider.py`, create a function `fetch_aaii_sentiment()` to get and parse data from the AAII Excel file.

**Step 3: Implement Proactive Caching**
- [ ] Refactor `data_provider.py` to create a clear two-layer architecture:
    -   **Fetcher Layer:** Functions that make the external API calls.
    -   **Getter Layer:** Functions that read data from local JSON cache files (e.g., `fng_cache.json`).
- [ ] Create an `update_cache.py` script that uses the "Fetcher" functions to generate the JSON cache files.
- [ ] Test the `update_cache.py` script from the command line.
- [ ] **Note:** The AAII data fetching is a manual process. The `sentiment.xls` file must be downloaded weekly from the AAII website and placed in the project root, as their server blocks automated downloads.

**Step 4: Create the API Endpoint**
- [ ] In `app.py`, create the `/api/market-data` endpoint.
- [ ] This endpoint will use the "Getter" functions from `data_provider.py` to read from the cache and return the combined data.
- [ ] Test this endpoint directly in the browser.

**Step 5: Refactor and Prepare Frontend**
- [ ] Reorganize frontend files (`static/index.html`, `static/style.css`, `static/js/app.js`).
- [ ] In `index.html`, replace all hardcoded data values with placeholder elements that have unique `id` attributes.

**Step 6: Implement Dynamic Frontend**
- [ ] In `static/js/app.js`, use the `fetch()` API to call `/api/market-data` on page load.
- [ ] Create JavaScript functions to take the fetched data and render it on the page by updating the placeholder elements.
- [ ] Ensure the `updateSignalRecommendation()` function uses the live data to generate its recommendation.

**Step 7: Production Deployment**
- [ ] Set up a hosting provider like Render or Fly.io.
- [ ] Configure the web service to run `app.py`.
- [ ] Configure a cron job to run `update_cache.py` on a daily/weekly schedule.

---

#### Phase 2: Email Notifications (Future Feature)

This phase focuses on adding a premium feature for paid subscribers: periodic email notifications with the latest market sentiment data.

**Architecture Overview:**
- **Email Service:** A third-party, developer-focused email service like Resend will be used to manage subscribers and handle email delivery. This offloads the complexities of deliverability and scaling.
- **User Management:** The main web application will be responsible for adding/removing subscribers from the email service's audience list via API calls.
- **Trigger Mechanism:** A cron job, configured on the hosting platform, will trigger the email sending process on a defined schedule.

**Step 8: Integrate with Email Service**
- [ ] Set up an account with a service like Resend.
- [ ] Create an "Audience" or "Contact List" to hold the email addresses of paid subscribers.
- [ ] Design an email template within the service for the daily/weekly reports.

**Step 9: Implement the Email Sending Worker**
- [ ] Create a new script, `send_emails.py`.
- [ ] This script will be executed by the cron job.
- [ ] Its logic will be:
    1.  Fetch the list of subscribers from the email service's API.
    2.  Fetch the *live* data from the CNN and AAII endpoints (using the "Fetcher" functions).
    3.  Loop through the subscribers and make an API call to the email service for each one, passing the data to populate the template.

**Step 10: Update the Web App for Subscriptions**
- [ ] Add a (conceptual) user account or subscription page to the web application.
- [ ] When a user subscribes, the backend will make an API call to add their email to the appropriate audience in the email service.
- [ ] When a user cancels, their email will be removed. 