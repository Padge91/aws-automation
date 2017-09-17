import boto3
import credentials


# read AWS credentials
def read_AWS_credentials():
	try:
		return credentials.aws_region, credentials.aws_access_key, credentials.aws_secret_key	
	except Exception as e:
		print("Error reading AWS credentials: " + str(e))
		exit(1)


# connect to Route53 service
def connect_route53(region, access_key, secret_key):
	try:
		client = boto3.client("route53", region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
		return client
	except Exception as e:
		print("Error connecting to AWS: " + str(e))
		exit(1)


# list hosted zones
def list_hosted_zones(route53_client, marker=None):
	response_metadata = "ResponseMetadata"
	status_code_field = "HTTPStatusCode"
	truncated_field = "IsTruncated"
	marker_field = "Marker"
	body_field = "HostedZones"
	all_zones=[]
	
	try:
		if marker is None:
			response = route53_client.list_hosted_zones(
				MaxItems='100'
				)
		else:
			response = route53_client.list_hosted_zones(
				Marker=marker,
                                MaxItems='100'
                                )

		if response_metadata not in response or status_code_field not in response[response_metadata] or response[response_metadata][status_code_field] != 200:
			raise Exception("Response not returned successfully.")
		if response[truncated_field]:
			next_list = response(route53_client, response[marker_field])
			all_zones = all_zones + next_list

		all_zones = all_zones + response[body_field]
		return all_zones
	except Exception as e:
		print("Error listing hosted zones: " + str(e))
		exit(1)


# list records of one hosted zone
def list_record_sets(route53_client, hosted_zone_id, next_record_name=None, next_record_type=None):
	response_metadata = "ResponseMetadata"
	status_code_field = "HTTPStatusCode"
	truncated_field = "IsTruncated"
	next_record_name_field = "NextRecordName"
	next_record_type_field = "NextRecordType"
	body_field = "ResourceRecordSets"
	all_records = []

	try:
		if next_record_name is None or next_record_type is None:
			response = route53_client.list_resource_record_sets(HostedZoneId = hosted_zone_id, MaxItems="1")
		else:
			response = route53_client.list_resource_record_sets(HostedZoneId = hosted_zone_id, StartRecordType=next_record_type,StartRecordName=next_record_name, MaxItems="1")
		if response_metadata not in response or status_code_field not in response[response_metadata] or response[response_metadata][status_code_field] != 200:
			raise Exception("Response not returned successfully.")

		if response[truncated_field]:
			next_records = list_record_sets(route53_client, hosted_zone_id, response[next_record_name_field], response[next_record_type_field])
			all_records = all_records + next_records   
    
		all_records = all_records + response[body_field]
		return all_records
	except Exception as e:
		print("Error listing record sets: " + str(e))
		exit(1)


# list record sets
def list_all_record_sets(route53_client, hosted_zones, next_record=None):
	record_set_id_field = "Id"
	record_sets = []

	try:
		for i in range(0, len(hosted_zones)):
			hosted_zone_id = hosted_zones[i][record_set_id_field]
			records = list_record_sets(route53_client, hosted_zone_id)
			record_sets = record_sets + records
		return record_sets
	except Exception as e:
		print("Error listing record sets per hosted zone: " + str(e))
		exit(1)


# main method
if __name__=="__main__":	
	region, access_key, secret_key = read_AWS_credentials()
	client = connect_route53(region, access_key, secret_key)
	hosted_zones = list_hosted_zones(client)
	record_sets = list_all_record_sets(client, hosted_zones)
	print(record_sets)
