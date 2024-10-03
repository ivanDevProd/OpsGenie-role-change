import requests
import pandas as pd
from datetime import datetime
import pytz  # To handle timezone conversion

pd.set_option('display.max_columns', None)  # None means unlimited
pd.set_option('display.expand_frame_repr', False)  # Prevents line wrapping

# Your OpsGenie API key
api_key = '623a40f4-7c85-4259-a463-ce1553567154'
schedule_id = 'c4eb4a79-7398-460a-aa3d-5dd1bde5126f'
url = f'https://api.opsgenie.com/v2/schedules/{schedule_id}/timeline?interval=3&intervalUnit=months&expand=finalSchedule'

# Set headers
headers = {
    'Authorization': f'GenieKey {api_key}',
    'Content-Type': 'application/json'
}

# Make the API request
response = requests.get(url, headers=headers)
data = response.json()

# Initialize a list to hold the results
rows = []

# Extract schedule name
schedule_name = data['data']['_parent']['name']

# Loop through the rotations and periods to extract relevant data
for rotation in data['data']['finalTimeline']['rotations']:
    rotation_name = rotation['name']
    for period in rotation['periods']:
        recipient = period['recipient']

        # Only include periods with a recipient name
        if recipient['type'] == 'user' and 'name' in recipient:
            row = {
                'schedule_name': schedule_name,
                'rotation_name': rotation_name,
                'recipient_name': recipient['name'],
                'startDate': period['startDate'],
                'endDate': period['endDate']
            }
            rows.append(row)

# Create a DataFrame from the rows
df = pd.DataFrame(rows)

# Convert 'startDate' and 'endDate' to datetime for filtering
df['startDate'] = pd.to_datetime(df['startDate']).dt.tz_convert('UTC')  # Ensure UTC timezone
df['endDate'] = pd.to_datetime(df['endDate']).dt.tz_convert('UTC')  # Ensure UTC timezone

# Define the date range for filtering
start_range = datetime.strptime("2024-10-01", "%Y-%m-%d").replace(tzinfo=pytz.UTC)  # Convert to UTC
end_range = datetime.strptime("2024-12-31", "%Y-%m-%d").replace(tzinfo=pytz.UTC)  # Convert to UTC

# Filter the DataFrame based on the date range
filtered_df = df[(df['startDate'] <= end_range) & (df['endDate'] >= start_range)]

# Print the DataFrame
print(filtered_df)
filtered_df.to_csv('schedule_data.csv', index=False)  # Change the filename as needed

# Create a list of unique recipient names
unique_recipients = filtered_df['recipient_name'].unique().tolist()
print(f"Users in schedlue for defined period {len(unique_recipients)}: {unique_recipients}")
