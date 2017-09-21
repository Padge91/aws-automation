import authenticate



def get_s3_buckets(s3_client):
	buckets_field = "Buckets"
	buckets_name_field = "Name"

	buckets_response = s3_client.list_buckets()
	bucket_names = []
	for bucket in buckets_response[buckets_field]:
		bucket_names.append(bucket[buckets_name_field])

	return bucket_names

#def get_s3_files_and_folders():


#def create_s3_bucket():



#def download_s3_file():


#def upload_s3_file():



def migrate_all_files():
	client = authenticate.connect_s3()
	print(get_s3_buckets(client))


# main method
if __name__=="__main__":
	migrate_all_files()

