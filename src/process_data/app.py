import json
import pandas as pd
import numpy as np

def lambda_handler(event, context):
    try:
        # Ejemplo de procesamiento de datos con pandas
        data = {
            'numbers': np.random.randn(5).tolist()
        }
        
        df = pd.DataFrame(data)
        stats = {
            'mean': df['numbers'].mean(),
            'std': df['numbers'].std(),
            'min': df['numbers'].min(),
            'max': df['numbers'].max()
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data processed successfully',
                'statistics': stats
            }, default=str)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }