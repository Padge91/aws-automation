import authenticate
import os 
import time

error_images=[]

trial_run=True


# get image attribute
def get_image_description(ec2_client, ami):
	value_field="Value"

	try:
		response_field = "Description"
		response = ec2_client.describe_image_attribute(Attribute="description", ImageId=ami, DryRun=False)
		if response_field not in response or value_field not in response[response_field]:
			raise Exception("Description response is malformed.")
		else:
			return response[response_field][value_field]
	except Exception as e:
		print("Could not get description of AMI: " + ami + ".\nError: " + str(e))
		error_images.append("Could not get image description from image: " + ami)
		return "Default description."


# list images
def list_images(ec2_client,user_id):
	owner_field="OwnerId"
	public_field="Public"
	images_field="Images"
	image_id_field="ImageId"
	image_name_field="Name"
	tags_field="Tags"
	type_field="VirtualizationType"

	required_fields = [image_id_field, image_name_field, tags_field, type_field]

	images_info = []	
	
	try:
		images = ec2_client.describe_images(ImageIds=[], ExecutableUsers=[],DryRun=False)

		if images_field not in images:
			raise Exception("Image field not found. Response is malformed")

		for image in images[images_field]:
			# dont care if the image is already pubic, it can be moved easily in that case
			if owner_field in image and image[owner_field] == "143148225560":
				image_info={}
				for field in required_fields:
					if field in image:
						image_info[field] = image[field]
				image_info["image_description"] = get_image_description(ec2_client, image_info[image_id_field])
				images_info.append(image_info)
		
		return images_info
	except Exception as e:
		print("Unable to list EC2 images on client\nError: " + str(e))
		exit(1)


# get instance tags
def get_instance_tags(ec2_client, instance_id):
	try:
		reservations_field="Reservations"
		instances_field="Instances"
		tags_field = "Tags"
		tags = []

		response = ec2_client.describe_instances(InstanceIds=[instance_id], DryRun=False)

		#if reservations_field not in response or len(response[reservations_field]) == 0 or instances_field not in response[reservations_field][0] or len(response[reservations_field][0][instances_field]) == 0 or tags_field not in response[reservations_field][0][instances_field][0]:
		#	return []
		#else:
		return response[reservations_field][0][instances_field][0][tags_field]
	except Exception as e:
		return []


# get instance state
def get_instance_state(ec2_client, instance_id):
	try:
		reservations_field="Reservations"
		instances_field="Instances"
		state_field="State"
		name_field="Name"

		response = ec2_client.describe_instances(InstanceIds=[instance_id], DryRun=False)

		# get instance state
		return response[reservations_field][0][instances_field][0][state_field][name_field]
	except Exception as e:
		print("Can not determine instance state (this might be okay).\nError: " + str(e))
		return None
		


# create image for running instance
def create_image(ec2_client, instance_id, image_name="Default", image_description="Default"):
	try:
		image_field="ImageId"

		response = ec2_client.create_image(Name=image_name, Description=image_description, InstanceId=instance_id, DryRun=False, NoReboot=False)
	
		if image_field not in response:
			raise Exception("Repsonse is malformed.")

		return response[image_field]

	except Exception as e:
		print("Error creating image for instance " + str(instance_id) + ".\nError: "+str(e))
		error_images.append("Could not create image from instance " + instance_id + " based on image: " + image_name)


# create images for all running instances
def create_all_images(ec2_client, all_instances):
	for i in range(0, len(all_instances)):
		# wait for instance to be in running state
		print("Waiting for instance " + all_instances[i] + " to be in running state.")
		while True:
			new_state = get_instance_state(ec2_client, all_instances[i])
			if new_state is not None and new_state == "running":
				break
			time.sleep(5)
		
		#get instance tags
		instance_tags = get_instance_tags(ec2_client, all_instances[i])
		collapsed_tags = {}
		for item in instance_tags:
			collapsed_tags[item["Key"]] = item["Value"]

		# get name and description
		image_name = collapsed_tags["ami_name"]
		del collapsed_tags["ami_name"]

		image_description = collapsed_tags["ami_description"]
		del collapsed_tags["ami_description"]

		# expand tags, what a pain
		image_tags=[]
		for key in collapsed_tags.keys():
			image_tags.append({"Key":key, "Value":collapsed_tags[key]})
	
		# create image
		print("Creating image for instance " + all_instances[i] + " (" + image_name + ").")
		ami_id = create_image(ec2_client, all_instances[i], image_name, image_description)

		#tag image
		print("Tagging new image " + ami_id+" (" + image_name + ").")
		tag_image(ec2_client, ami_id, image_tags)

		if trial_run:
			return


# tag an image
def tag_image(ec2_client, ami_id, tags):
	try:
		if tags is None or len(tags) == 0:
			return
		ec2_client.create_tags(Resources=[ami_id], Tags=tags, DryRun=False)
	except Exception as e:
		print("Unable to tag image " + ami_id + ".\nError: " + str(e))
		error_images.append("Could not add tags to image: " + ami_id)
		return


# get configured user info
def get_client_info(client):
	user_field="User"
	user_id_field="Arn"
	
	try:
		# egt user info of currently logged in user
		response = client.get_user()
		if user_field not in response:
			raise Exception("User field not found. Response is malformed.")
		if user_id_field not in response[user_field]:
			raise Exception("User ID field not found. Response is malformed.")
	
		return response[user_field][user_id_field].strip().split(":")[4]
	except Exception as e:
		print("Unable to access client information. Ensure your IAM policies allow your target user to run the IAM:GetUser operation.\nError: " + str(e))
		exit(1)


# modify ami permissions with another AWS account
def modify_image_permissions(source_client, target_client, image_id, mode):
	try:
		# get user id for target
		target_id = get_client_info(target_client)
		launch_permission_body = {}
		launch_permission_body[mode] = [{"UserId":target_id}]
		response = source_client.modify_image_attribute(Attribute="launchPermission", ImageId=image_id, LaunchPermission=launch_permission_body, UserIds=[target_id], DryRun=False)
	except Exception as e:
		print("Unable to "+mode+" permissions to AMI: " + str(image_id) + ". Error: " + str(e))
		error_images.append("Could not " + mode + " image permissions: " + image_id)


# share image with another AWS account
def share_image_permissions(source_client, target_client, image):
	add_key="Add"
	id_field="ImageId"
	name_field="Name"	

	image_id=image[id_field]
	image_name=image[name_field]
	print("Sharing AMI: " + image_id + " (" + image_name + ")")
	modify_image_permissions(source_client, target_client, image_id, add_key)


# share all images with another AWS account
def share_all_images_permissions(source_client, target_client, images):
	print("Sharing image permissions.")
	for i in range(0, len(images)):
		share_image_permissions(source_client, target_client, images[i])
		if trial_run:
			return


# revoke image from another AWS account
def revoke_image_permissions(source_client, target_client, image):
	removal_key="Remove"
	id_field="ImageId"
	name_field="Name"

	image_id=image[id_field]
	image_name=image[name_field]
	print("Revoking AMI: " + image_id + " (" + image_name+")")
	modify_image_permissions(source_client, target_client, image_id, removal_key)


# revoke all images from another AWS account
def revoke_all_images_permissions(source_client, target_client, images):
	print("Revoking image permissions.")
	for i in range(0, len(images)):
		revoke_image_permissions(source_client, target_client, images[i])


# get subnet IDs
def get_subnet_id(client):
	subnets_field="Subnets"
	subnet_id_field="SubnetId"

	try:
		response = client.describe_subnets(DryRun=False)
		if subnets_field not in response:
			raise Exception("Subnets field not found. Response is malformed.")

		if len(response[subnets_field]) == 0:
			raise Exception("No subnets found. There must exists at least one subnet to use.")
			
		#return the first subnet id cuz we don't really care if it's accessible, just want to make an image from it
		if subnet_id_field not in response[subnets_field][0]:
			raise Exception("Subnet ID field not found. Response is malformed.")
		
		return response[subnets_field][0][subnet_id_field]

	except Exception as e:
		print("Error retrieving Subnet Ids. These are required before proceeding.\nError: " + str(e))	
		exit(1)


# start an instance from an image
def start_instance_from_image(client, image, subnet_id):
	try:
		name_field="Name"
		ami_field="ImageId"
		tags_field="Tags"
		vm_type_field="VirtualizationType"
		description_field="Description"

		ami_id=image[ami_field]
		name=image[name_field]
		description=image["image_description"]

		if tags_field in image:
			tags=image[tags_field]
		else:
			tags = []
		tags.append({"Key":"ami_name", "Value":name})
		tags.append({"Key":"ami_description", "Value":description})

		if vm_type_field not in image:
			type="t2.micro"
		else:
			if image[vm_type_field]=="paravirtual":
				type="t1.micro"
			else:
				type="t2.micro"

		print("Starting instance for AMI " + ami_id + " ("+name+")")	
		response = client.run_instances(ImageId=ami_id, MaxCount=1, MinCount=1, InstanceType=type, NetworkInterfaces=[{"SubnetId":subnet_id, "DeviceIndex":0}], TagSpecifications=[{"ResourceType":"instance", "Tags":tags}])
			
		return response["Instances"][0]["InstanceId"]
	except Exception as e:
		print("Error starting EC2 instance from image " + str(image) + ".\nError: " + str(e))
		error_images.append("Could not start instance from image: " + image)
		

# start intances from all images
def start_instances_from_images(client, all_images, subnet_id):
	instance_ids = []
	for i in range(0, len(all_images)):
		instance_id = start_instance_from_image(client, all_images[i], subnet_id)
		instance_ids.append(instance_id)
		if trial_run:
			return [instance_id]
	return instance_ids


# terminate an instance
def terminate_instance(ec2_client, instance_id):
	try:
		print("Terminating instance: " + instance_id)
		response = ec2_client.terminate_instances(InstanceIds=[instance_id], DryRun=False)

	except Exception as e:
		print("Unable to terminate instance " + instance_id + ". Please don't forget to shut it off.\nError: " + str(e))	


# terminate all instances
def terminate_all_instances(ec2_client, instance_ids):
	for i in range(0, len(instance_ids)):
		terminate_instance(ec2_client, instance_ids[i])


# print out errors encountered
def output_errors():
	print("\nNumber of errors with images: " + str(len(error_images)))
	if len(error_images) > 0:
		print("These images could have either failed when being created from an instance, failed when starting an instance from the image, when the image can't be shared, when the image can't be tagged, or when the image description could not be found.")
		print("The full list of images follows:\n"+"\n".join(error_images))


# main method
if __name__=="__main__":
	if not authenticate.compare_regions():
		print("EC2 images can only be migrated to the same region. To move the images to a new region, please use the copy script.")
		exit(1)

	source_ec2_client = authenticate.connect_ec2()
	destination_ec2_client = authenticate.connect_ec2_alt()
	source_iam_client = authenticate.connect_iam()
	destination_iam_client = authenticate.connect_iam_alt()

	# collect image ids and share them to target client
	print("Getting list of images")
	client_id = get_client_info(source_iam_client)
	images_info = list_images(source_ec2_client, client_id)

	# soure client share launch permissions	
	share_all_images_permissions(source_ec2_client, destination_iam_client, images_info)

	# destination client start instance from each ami
	# need to get subnet ID to launch
	subnet_id = get_subnet_id(destination_ec2_client)
	instance_ids = start_instances_from_images(destination_ec2_client, images_info, subnet_id)

	# destination client make images from each instance started
	create_all_images(destination_ec2_client, instance_ids)

	# source client revoke launch permissions
	revoke_all_images_permissions(source_ec2_client, destination_iam_client, images_info)

	# destination client terminate all instances
	terminate_all_instances(destination_ec2_client, instance_ids)

	output_errors()


