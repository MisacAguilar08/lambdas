import json
from datetime import datetime
import pytz

def lambda_handler(event, context):
    # Get current time in UTC
    tz = pytz.timezone('UTC')
    current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Hello World!',
            'timestamp': current_time
        })
    }