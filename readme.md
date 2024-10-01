# Shotgun Spread Geocoder App

## Description:
The Shotgun Spread Geocoder App (built on Streamlit) allows users to upload a JSON file containing store location data. The outputted file is compatible with [jQuery-Store-Locator-Plugin](https://github.com/bjorn2404/jQuery-Store-Locator-Plugin)'s expected input. Upload a JSON file with store location data, and the app will automatically retrieve each store’s address details, including latitude, longitude, website, and other relevant information. It then generates a downloadable updated_locations.json file with the enhanced data for easy use.

## Features
Upload a JSON file with store location data.
Automatically assigns missing store IDs.
Uses the Google Maps API to retrieve missing latitudes, longitudes, and additional details.
Updates store data with address, phone number, website, and hours of operation.
Provides a downloadable updated_locations.json file.

## Requirements
- Streamlit: The app uses Streamlit for its web interface.
- Google Maps API: Requires an API key for geocoding and retrieving place details. Store the API key in the Streamlit secrets (st.secrets).

## Logging
The app uses Python's logging module to output logs to the console for actions like:
- Successfully updated location information.
- Geocoding or place lookup errors.

## Installation

### Start up you virtual environment (optional)
`source venv/bin/activate`

### Install dependencies
`pip install -r requirements.txt`

### Create a .streamlit directory
Place a secrets.toml file inside of it containing:
```[general]``` 
```google_maps_api_key = "YOURAPIKEY"```

## Running the app

### Start it up
`streamlit run app.py`

### Upload source data file
There is a locations.json in the app's root directory that contains a starter/test schema. Just replace the info contained therin with your own locations.

### Download your data
Once your source file is uploaded the app will process your data and output a new updated_locations.json in a directory of your choice. This file is compatible with [https://github.com/bjorn2404/jQuery-Store-Locator-Plugin](jQuery-Store-Locator-Plugin)'s expected input.

## Demo
[https://www.youtube.com/watch?v=6vxSPwmrpGQ](https://www.youtube.com/watch?v=6vxSPwmrpGQ)