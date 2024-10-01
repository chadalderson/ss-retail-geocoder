import streamlit as st
import os
import json
import time
import logging
import googlemaps
from googlemaps.exceptions import ApiError, TransportError, Timeout
from collections import OrderedDict

# Initialize Google Maps client
API_KEY = st.secrets["general"]["google_maps_api_key"]
gmaps = googlemaps.Client(key=API_KEY)

# Rate limiting parameters
API_DELAY = 0.1  # 100 milliseconds delay between API calls

# Define expected fields for each location
EXPECTED_FIELDS = [
    'id', 'name', 'lat', 'lng', 'category', 'address', 'address2',
    'city', 'state', 'postal', 'phone', 'web', 'hours1', 'hours2',
    'hours3', 'featured', 'features', 'date'
]

# Configure logging to output to the console
logging.basicConfig(level=logging.INFO)

def log_info(message):
    logging.info(message)

def log_warning(message):
    logging.warning(message)

def log_error(message):
    logging.error(message)

def main():
    st.title("Shotgun Spread Geocoder App")
    st.write("Upload a JSON file with store location data, and the app will automatically retrieve each store’s address details, including latitude, longitude, website, and other relevant information. It then generates a downloadable updated_locations.json file with the enhanced data for easy use.")

    # File uploader widget
    uploaded_file = st.file_uploader("Choose a JSON file", type="json")

    if uploaded_file is not None:
        try:
            # Read and parse the uploaded file
            locations_data = json.load(uploaded_file)
            locations = preprocess_locations(locations_data)
            st.success(f"Loaded {len(locations)} locations from the uploaded file.")

            # Assign IDs to locations if missing
            assign_ids(locations)

            # Option to start processing
            if st.button("Update Locations"):
                updated_locations = process_locations(locations)
                st.success("Location data has been updated successfully.")

                # Provide a download button for the updated JSON
                output_json = json.dumps(updated_locations, indent=4)
                st.download_button(
                    label="Download Updated Locations",
                    data=output_json,
                    file_name="updated_locations.json",
                    mime="application/json",
                )
        except json.JSONDecodeError as e:
            st.error(f"Error decoding JSON: {e}")
    else:
        st.info("Awaiting file upload.")

def preprocess_locations(locations_data):
    # Initialize list of locations
    locations = []

    # Ensure each location has all expected fields in the desired order
    for loc_data in locations_data:
        location = OrderedDict()
        for field in EXPECTED_FIELDS:
            location[field] = loc_data.get(field, '')
        locations.append(location)
    return locations

def assign_ids(locations):
    # Assign IDs to locations if missing
    existing_ids = set()
    max_id = 0

    # First pass to collect existing IDs and find the maximum ID
    for location in locations:
        id_str = location.get('id', '')
        if id_str.isdigit():
            id_num = int(id_str)
            existing_ids.add(id_num)
            max_id = max(max_id, id_num)
        else:
            log_warning(f"Non-integer or missing ID found: {id_str}")

    # Second pass to assign new IDs to locations missing IDs
    next_id = max_id + 1
    for location in locations:
        if not location.get('id', '').isdigit():
            location['id'] = str(next_id)
            log_info(f"Assigned new ID {next_id} to location {location.get('name', '')}")
            next_id += 1

def process_locations(locations):
    updated_locations = []
    total_locations = len(locations)
    progress_bar = st.progress(0)
    status_text = st.empty()  # Create a placeholder for status messages

    for idx, location in enumerate(locations):
        updated_location = update_location_info(location)
        updated_locations.append(updated_location)
        progress = (idx + 1) / total_locations
        progress_bar.progress(progress)
        status_text.text(f"Processing {idx + 1}/{total_locations}: {location.get('name', 'Unknown')}")
        time.sleep(API_DELAY)  # Rate limiting

    status_text.text("Processing complete.")
    return updated_locations

def update_location_info(location):
    # Update a single location's information using Google Maps API.
    location_id = location.get('id', 'Unknown ID')
    name = location.get('name', '')
    city = location.get('city', '')
    state = location.get('state', '')
    postal = location.get('postal', '')
    country = 'USA'  # Assuming all locations are in the USA

    log_info(f"Processing location ID: {location_id} - {name}")

    # If latitude or longitude are missing, use the Geocoding API to find them
    if not location.get('lat') or not location.get('lng'):
        full_address = ', '.join(filter(None, [location.get('address', ''), city, state, postal, country]))
        try:
            geocode_result = gmaps.geocode(full_address)
            time.sleep(API_DELAY)  # Rate limiting

            if geocode_result:
                geocoded_location = geocode_result[0]['geometry']['location']
                lat = geocoded_location['lat']
                lng = geocoded_location['lng']
                
                # Ensure precision to at least 10 decimal places
                location['lat'] = round(lat, 10)
                location['lng'] = round(lng, 10)
                
                log_info(f"Geocoded coordinates for ID {location_id}: ({location['lat']}, {location['lng']})")

            else:
                log_warning(f"Geocoding failed for location ID: {location_id}. No results returned.")
        except (ApiError, TransportError, Timeout) as e:
            log_error(f"API error during geocoding for location ID {location_id}: {e}")
        except Exception as e:
            log_error(f"Unexpected error during geocoding for location ID {location_id}: {e}")

    # Proceed with further updates (address, phone, etc.)
    place = find_place(name, city, state)
    time.sleep(API_DELAY)  # Rate limiting

    if place:
        place_id = place.get('place_id')
        if place_id:
            # Retrieve detailed place information
            details = get_place_details(place_id)
            if details:
                # Parse address components
                address_components = details.get('address_components', [])
                street_number = ''
                route = ''
                city = ''
                state = ''
                postal = ''
                for component in address_components:
                    types = component.get('types', [])
                    if 'street_number' in types:
                        street_number = component.get('long_name', '')
                    elif 'route' in types:
                        route = component.get('long_name', '')
                    elif 'locality' in types:
                        city = component.get('long_name', '')
                    elif 'administrative_area_level_1' in types:
                        state = component.get('short_name', '')
                    elif 'postal_code' in types:
                        postal = component.get('long_name', '')

                # Combine street_number and route to get street address
                street_address = ' '.join(filter(None, [street_number, route]))
                location['address'] = street_address or location.get('address', '')
                location['city'] = city or location.get('city', '')
                location['state'] = state or location.get('state', '')
                location['postal'] = postal or location.get('postal', '')

                # Update phone
                location['phone'] = details.get('formatted_phone_number', location.get('phone', ''))

                # Update website
                location['web'] = details.get('website', location.get('web', ''))

                # Update hours
                opening_hours = details.get('opening_hours', {})
                weekday_text = opening_hours.get('weekday_text', [])
                if isinstance(weekday_text, list):
                    location['hours1'] = "\n".join(weekday_text)
                else:
                    location['hours1'] = location.get('hours1', '')

                log_info(f"Updated location ID: {location_id} with data from Place Details API.")
            else:
                log_warning(f"No details found for place_id {place_id} for location ID: {location_id}.")
        else:
            log_warning(f"No place_id found in Find Place results for location ID: {location_id}.")
    else:
        log_warning(f"No place found using Find Place API for location ID: {location_id}.")

    # Ensure lat and lng are strings before returning the location
    location['lat'] = str(location.get('lat', ''))
    location['lng'] = str(location.get('lng', ''))

    # Set 'featured' to 'no' if it's missing or empty
    if not location.get('featured'):
        location['featured'] = 'no'

    # Reconstruct location as an OrderedDict with fields in the desired order
    ordered_location = OrderedDict()
    for field in EXPECTED_FIELDS:
        ordered_location[field] = location.get(field, '')
    return ordered_location

def find_place(location_name, city, state):
    # Use Google Maps Find Place API to locate the place based on name and location.
    # Returns the place details if found, else None.
    query = f"{location_name} in {city}, {state}"
    try:
        response = gmaps.find_place(
            input=query,
            input_type='textquery',
            fields=['place_id', 'formatted_address', 'opening_hours']
        )
        if response.get('candidates'):
            return response['candidates'][0]
        else:
            return None
    except (ApiError, TransportError, Timeout) as e:
        log_error(f"API error during find_place for '{query}': {e}")
        return None
    except Exception as e:
        log_error(f"Unexpected error during find_place for '{query}': {e}")
        return None

def get_place_details(place_id):
    # Retrieve detailed information about a place using its place_id.
    # Returns the place details if found, else None.
    try:
        place_details = gmaps.place(
            place_id=place_id,
            fields=['formatted_address', 'address_component', 'formatted_phone_number', 'website', 'opening_hours']
        )
        time.sleep(API_DELAY)  # Rate limiting
        return place_details.get('result', {})
    except (ApiError, TransportError, Timeout) as e:
        log_error(f"API error during place_details for place_id {place_id}: {e}")
        return {}
    except Exception as e:
        log_error(f"Unexpected error during place_details for place_id {place_id}: {e}")
        return {}

if __name__ == "__main__":
    main()