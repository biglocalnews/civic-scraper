# Scraper Testing Setup

This README provides step-by-step instructions for setting up and running tests for civic_scraper platform scrapers.

## Prerequisites

Make sure you have the following:

- Python environment with `pytest` and `google-api-python-client` packages installed
- Access to the Google Sheet containing meeting data
- The scraper you want to test

## Setup Instructions

This README contains the information needed to run tests for new scrapers.

### 1. Create Required Folders

Create the following folders in the root directory:

```bash
mkdir env 
mkdir logs
```
Ensure that these folders are listed in the gitignore.

### 2. Set Up Google Credentials
Contact Aïcha Camara @necabotheking for `GOOGLE_APPLICATION_CREDENTIALS.json` file needed to programmatically access the main_meetings_list Google Sheet. Please put in the file in the env folder.

### 3. Create .env File
Create a `.env` file with the `SPREADSHEET_ID` variable.  (The `SPREADSHEET_ID` can be found in the main_meetings_list Google Sheet URL after `/d/` and before `/edit`.)

Your .env file should look like this:

```env
SPREADSHEET_ID=meeting-id
```

### 4. Generate Base Test Configuration
Run the following script to generate the base test config:
```python
python create_test_config.py
```
After running the script, manually edit the generated test_config file to populate the committees list based on the main_meetings list.

### 5. Create Test File
Make a copy of ```base_test_file.py``` and rename it based on the current scraper you are testing (e.g., test_escribe_site.py). Import the scraper module you want to test into the new file.


### 6. **Run Tests**
Run the new test file with pytest
```python
pytest test_scraper_site.py
```
Test output will be logged to ```logs/test_scraper_log.txt```
