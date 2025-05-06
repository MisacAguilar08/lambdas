import boto3

ssm = boto3.client('ssm')

def get_parameter(name, with_decryption=False):
    response = ssm.get_parameter(
        Name=name,
        WithDecryption=with_decryption
    )
    return response['Parameter']['Value']

def get_parameters_by_path(path, recursive=True):
    response = ssm.get_parameters_by_path(
        Path=path,
        Recursive=recursive
    )
    return {param['Name']: param['Value'] for param in response['Parameters']}
    