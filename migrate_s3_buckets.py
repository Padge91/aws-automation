import authenticate
import os 


migrated_bucket_suffix="-s3m"


# list all s3 buckets
def get_s3_buckets(s3_client):
	buckets_field = "Buckets"
	buckets_name_field = "Name"

	try:
		buckets_response = s3_client.list_buckets()
		bucket_names = []
	
		if buckets_field not in buckets_response:
			raise Exception("Response not listed successfully.")
	
		for bucket in buckets_response[buckets_field]:
			if buckets_name_field not in bucket:
				print("Malformed bucket: " + bucket)
				continue			
			bucket_names.append(bucket[buckets_name_field])
	
		return bucket_names
	except Exception as e:
		print("Error receiving buckets list: " + str(e))


# get all S3 files in list of buckets
def get_all_s3_files_and_folders(s3_client, all_buckets):
	all_content = []
	for i in range(0, len(all_buckets)):
		bucket = all_buckets[i]
		content = get_s3_bucket_contents(s3_client, bucket)
		all_content.append({"bucket":bucket, "content":content})	
	return all_content


# get all standard files in the bucket
def get_s3_bucket_contents(s3_client, bucket_name):
	contents_field="Contents"
	bucket_contents = []

	try:
		response = s3_client.list_objects(Bucket = bucket_name)
		if contents_field not in response:
			# means it's not a file bucket
			return bucket_contents

		contents = response[contents_field]
		for i in range(0, len(contents)):
			bucket_contents.append(contents[i]["Key"])
		return bucket_contents
			
	except Exception as e:
		print("Error listing all files in bucket: " + bucket_name + " - " + str(e))
		return []


# create s3 buckets using a prefix - since s3 buckets need to be unique
def create_s3_buckets_with_prefix(s3_client, bucket_names, suffix):
	new_bucket_names = []
	for i in range(0, len(bucket_names)):
		new_bucket_names.append(bucket_names[i] + suffix)

	create_s3_buckets(s3_client, new_bucket_names)

# create s3 buckets in list
def create_s3_buckets(s3_client, bucket_names):
	for i in range(0, len(bucket_names)):
		bucket_name = bucket_names[i]
		bucket_location = authenticate.get_region_alt()
		try:
			s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': bucket_location })
		except Exception as e:
			print("Error creating bucket: " + bucket_name + " - " + str(e))
			

# download file from bucket
def download_s3_file(s3_client, bucket_name, file_name):
	try:
		make_file_path(file_name)

		with open(file_name, 'wb') as data:
			s3_client.download_fileobj(bucket_name, file_name, data)
		return True
	except Exception as e:
		print("Failed to download file: " + bucket_name + " - " + file_name + " - " + str(e))
		return False


# make a local directory for file if required
def make_file_path(file_name):
	if not os.path.exists(os.path.dirname(file_name)):
		try:
			os.makedirs(os.path.dirname(file_name))
		except Exception as e: # Guard against race condition
			return


# download file from bucket
def upload_s3_file(s3_client, bucket_name, file_name):
	try:
		with open(file_name, 'rb') as data:
			s3_client.upload_fileobj(data, bucket_name, file_name)
		return True
	except Exception as e:
		print("Failed to upload file: " + bucket_name + " - " + file_name + " - " + str(e))
		return False


# download files from bucket
def download_s3_files(s3_client, bucket_name, file_names):
	for i in range(0, len(file_names)):
		download_s3_file(s3_client, bucket_name, file_names[i])



# upload file
def upload_s3_files(s3_client, bucket_name, file_names):
	for i in range(0, len(file_names)):
		upload_s3_file(s3_client, bucket_name, file_names[i])


# main method
def migrate_all_files():
	source_client = authenticate.connect_s3()
	destination_client = authenticate.connect_s3_alt()

	# create s3 buckets
	all_buckets = get_s3_buckets(source_client)
	create_s3_buckets_with_prefix(destination_client, all_buckets, migrated_bucket_suffix)

	# get all files
	s3_paths = get_all_s3_files_and_folders(source_client, all_buckets)

	# download all relevant files
	for i in range(0, len(s3_paths)):
		download_s3_files(source_client, s3_paths[i]["bucket"], s3_paths[i]["content"])
	
	# upload all relevant files
	for i in range(0, len(s3_paths)):
		s3_paths[i]["bucket"] = s3_paths[i]["bucket"] + migrated_bucket_suffix
		upload_s3_files(destination_client, s3_paths[i]["bucket"], s3_paths[i]["content"])
	


# main method
if __name__=="__main__":
	migrate_all_files()

