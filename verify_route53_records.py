from platform import system
import authenticate
import os

# Set credentials in credentials.py file. Sample file is provided
# Requires servers to be ping-able to work correctly - must do this because of variety of ports applications use
# Run with 'python verify_route53_records.py
# Output will be list of dictionaries indicating whether host was reachable or not


# list hosted zones
def get_hosted_zones(route53_client, marker=None):
	response_metadata = "ResponseMetadata"
	status_code_field = "HTTPStatusCode"
	truncated_field = "IsTruncated"
	marker_field = "Marker"
	body_field = "HostedZones"
	all_zones=[]
	
	try:
		# get initial list of hosted zones or next 
		if marker is None:
			response = route53_client.list_hosted_zones(MaxItems='100')
		else:
			response = route53_client.list_hosted_zones(Marker=marker, MaxItems='100')

		# check response codes
		if response_metadata not in response or status_code_field not in response[response_metadata] or response[response_metadata][status_code_field] != 200:
			raise Exception("Response not returned successfully.")

		# check if response is paginated
		if response[truncated_field]:
			next_list = get_hosted_zones(route53_client, response[marker_field])
			all_zones = all_zones + next_list

		all_zones = all_zones + response[body_field]
		return all_zones
	except Exception as e:
		print("Error listing hosted zones: " + str(e))
		exit(1)


# list records of one hosted zone
def get_record_sets(route53_client, hosted_zone_id, next_record_name=None, next_record_type=None):
	response_metadata = "ResponseMetadata"
	status_code_field = "HTTPStatusCode"
	truncated_field = "IsTruncated"
	next_record_name_field = "NextRecordName"
	next_record_type_field = "NextRecordType"
	body_field = "ResourceRecordSets"
	all_records = []

	try:
		# get initial record sets, or get next record set
		if next_record_name is None or next_record_type is None:
			response = route53_client.list_resource_record_sets(HostedZoneId = hosted_zone_id)
		else:
			response = route53_client.list_resource_record_sets(HostedZoneId = hosted_zone_id, StartRecordType=next_record_type,StartRecordName=next_record_name)

		# check for response code
		if response_metadata not in response or status_code_field not in response[response_metadata] or response[response_metadata][status_code_field] != 200:
			raise Exception("Response not returned successfully.")

		# see if results are paginated
		if response[truncated_field]:
			next_records = get_record_sets(route53_client, hosted_zone_id, response[next_record_name_field], response[next_record_type_field])
			all_records = all_records + next_records   
    
		all_records = all_records + response[body_field]
		return all_records
	except Exception as e:
		print("Error listing record sets: " + str(e))
		exit(1)


# list record sets
def get_all_record_sets(route53_client):
	record_set_id_field = "Id"
	record_sets = []

	# get hosted zones
	hosted_zones = get_hosted_zones(route53_client)

	# iterate through osted zones listing all records
	try:
		for i in range(0, len(hosted_zones)):
			hosted_zone_id = hosted_zones[i][record_set_id_field]
			records = get_record_sets(route53_client, hosted_zone_id)
			record_sets = record_sets + records
		return record_sets
	except Exception as e:
		print("Error listing record sets per hosted zone: " + str(e))
		exit(1)


# send ping request to server
def ping(host, hostname_field):
	hostname = host[hostname_field]
	
	# test to see what flags to use
	if system().lower()=="windows":
		postfix = ">nul 2>&1"
		params = "-n 1"
	else:
		postfix = ">/dev/null 2>&1" 
		params = "-c 1"

	# execute ping command and see what result is
	return_code = os.system("ping " + params + " " + hostname + " " + postfix)
	if return_code != 0:
		print("Unable to reach host: " + hostname)
	else:
		print("Host reached successfully: " + hostname)
	
	return {"hostname":hostname, "success":(return_code == 0)}


# send pings to all servers
def ping_all(hosts, hostname_field):
	all_responses = []

	for i in range(0, len(hosts)):
		all_responses.append(ping(hosts[i], hostname_field))

	return all_responses


# run all commands, same as main method
def verify_all_records():
        hostname_field = "Name"
        client = authenticate.connect_route53()
        record_sets = get_all_record_sets(client)
        return ping_all(record_sets, hostname_field)


# main method
if __name__=="__main__":	
	verify_all_records()


