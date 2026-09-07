import glob
import json
from pathlib import Path

folder_path = './results'
pattern = '*_raw.json'

# Method 1: Using glob with specific pattern
def read_pattern_json_files(folder_path, pattern):
    """
    Read JSON files matching a specific pattern
    Example patterns:
    - "data_2023*.json" - files starting with "data_2023"
    - "user_[0-9]*.json" - files starting with "user_" followed by numbers
    - "*_backup.json" - files ending with "_backup"
    """
    json_data = []
    # Construct the full pattern path
    pattern_path = str(Path(folder_path) / pattern)
    
    for file_path in glob.glob(pattern_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                json_data.append({
                    'filename': Path(file_path).name,
                    'data': data
                })
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {file_path}")
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
    
    return json_data

# Usage examples:
# Example 1: Read all JSON files starting with 'flight_'
flight_data = read_pattern_json_files(folder_path, pattern)

result = []
no_data_cnt = 0
for item in flight_data:
    journey = item['filename']
    # An offer price covers the whole itinerary for both adults
    offers = (item['data'].get('best_flights') or []) + (item['data'].get('other_flights') or [])
    prices = [offer['price'] for offer in offers if offer.get('price')]
    if len(prices) == 0:
        # print(f"Skip {journey} because no data")
        no_data_cnt += 1
        continue
    price = min(prices) / 2
    result.append({
        'price': price,
        'journey': journey
    })

result.sort(key=lambda x: x['price'])
for item in result[0:200]:
    print(item['price'], item['journey'])

print("# no data:", no_data_cnt)
# Example 2: Read JSON files with specific date pattern
# pattern = 'data_2023_[0-9][0-9].json'
# dated_data = read_pattern_json_files(folder_path, pattern)

