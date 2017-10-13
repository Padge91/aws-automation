import credentials
import boto3


# read AWS credentials
def read_AWS_credentials():
        try:
                return credentials.aws_region, credentials.aws_access_key, credentials.aws_secret_key
        except Exception as e:
                print("Error reading AWS credentials: " + str(e))
                exit(1)

# read second AWS credentials
def read_AWS_credentials_alt():
        try:
                return credentials.aws_region_2, credentials.aws_access_key_2, credentials.aws_secret_key_2
        except Exception as e:
                print("Error reading alternate AWS credentials: " + str(e))
                exit(1)


# get regions
def get_region():
	aws_region, aws_access_key, aws_secret_key = read_AWS_credentials()
	return aws_region


def get_region_alt():
	aws_region, aws_access_key, aws_secret_key = read_AWS_credentials_alt()
	return aws_region


# connect to Route53 service
def connect_route53():
	aws_region, aws_access_key, aws_secret_key = read_AWS_credentials()
	return connect_to_service("route53", aws_region, aws_access_key, aws_secret_key)


# connect to second Route53 service
def connect_route53_alt():
        aws_region, aws_access_key, aws_secret_key = read_AWS_credentials_alt()
        return connect_to_service("route53", aws_region, aws_access_key, aws_secret_key)


# connect to S3 service
def connect_s3():
        aws_region, aws_access_key, aws_secret_key = read_AWS_credentials()
        return connect_to_service("s3", aws_region, aws_access_key, aws_secret_key)


# connect to second S3 service
def connect_s3_alt():
        aws_region, aws_access_key, aws_secret_key = read_AWS_credentials_alt()
        return connect_to_service("s3", aws_region, aws_access_key, aws_secret_key)


# connect to EC2 service
def connect_ec2():
	aws_region, aws_access_key, aws_secret_key = read_AWS_credentials()
	return connect_to_service("ec2", aws_region, aws_access_key, aws_secret_key)


# connect to second EC2 service
def connect_ec2_alt():
	aws_region, aws_access_key, aws_secret_key = read_AWS_credentials_alt()
	return connect_to_service("ec2", aws_region, aws_access_key, aws_secret_key)


# connect to IAM service
def connect_iam():
        aws_region, aws_access_key, aws_secret_key = read_AWS_credentials()
        return connect_to_service("iam", aws_region, aws_access_key, aws_secret_key)


# connect to second IAM service
def connect_iam_alt():
        aws_region, aws_access_key, aws_secret_key = read_AWS_credentials_alt()
        return connect_to_service("iam", aws_region, aws_access_key, aws_secret_key)


# connect to arbitrary service
def connect_to_service(service_name, region, access_key, secret_key):
        try:
                # authenticate
                client = boto3.client(service_name, region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
                return client
        except Exception as e:
                print("Error connecting to AWS: " + str(e))
                exit(1)
