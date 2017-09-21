import credentials
import boto3


# read AWS credentials
def read_AWS_credentials():
        try:
                return credentials.aws_region, credentials.aws_access_key, credentials.aws_secret_key
        except Exception as e:
                print("Error reading AWS credentials: " + str(e))
                exit(1)


# connect to Route53 service
def connect_route53():
	aws_region, aws_access_key, aws_secret_key = read_AWS_credentials()
	return connect_to_service("route53", aws_region, aws_access_key, aws_secret_key)


# connect to S3 service
def connect_s3():
        aws_region, aws_access_key, aws_secret_key = read_AWS_credentials()
        return connect_to_service("s3", aws_region, aws_access_key, aws_secret_key)


# connect to arbitrary service
def connect_to_service(service_name, region, access_key, secret_key):
        try:
                # authenticate
                client = boto3.client(service_name, region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
                return client
        except Exception as e:
                print("Error connecting to AWS: " + str(e))
                exit(1)
