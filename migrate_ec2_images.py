import authenticate
import os 


create_images_from_instances_bool = False


# list images
def list_images(ec2_client):
	public_field="Public"
	images_field="Images"
	image_id_field="ImageId"

	image_ids = []	
	
	try:
		images = ec2_client.describe_images(ExecutableUsers=[],DryRun=False)
		if images_field not in images:
			raise Exception("Image field not found. Response is malformed")

		for image in images[images_field]:
			# dont care if the image is already pubic, it can be moved easily in that case
			if public_field in image and image_id_field in image and image[public_field]==False:
				image_ids.append(image[image_id_field])
		
		return image_ids
	except Exception as e:
		print("Unable to list EC2 images on source.\nError: " + str(e))
		exit(1)


# create image for running instance
def create_image():
	return 


# create images for all running instances
def create_all_images():
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
		launch_permission_body[mode] = [{"UserId":target_id, "Group":"all"}]
		response = source_client.modify_image_attribute(Attribute="launchPermission", ImageId=image_id, LaunchPermission=launch_permission_body, UserIds=[target_id], DryRun=False)
	except Exception as e:
		print("Unable to "+mode+" permissions to AMI: " + str(image_id) + ".\nError: " + str(e))


# share image with another AWS account
def share_image_permissions(source_client, target_client, image_id):
	add_key="Add"
	modify_image_permissions(source_client, target_client, image_id, add_key)


# share all images with another AWS account
def share_all_images_permissions(source_client, target_client, image_ids):
	for i in range(0, len(image_ids)):
		share_image_permissions(source_client, target_client, image_ids[i])


# revoke image from another AWS account
def revoke_image_permissions(source_client, target_client, image_id):
	removal_key="Remove"
	modify_image_permissions(source_client, target_client, image_id, removal_key)


# revoke all images from another AWS account
def revoke_all_images_permissions(source_client, target_client, image_ids):
	for i in range(0, len(image_ids)):
		revoke_image_permissions(source_client, target_client, image_ids[i])


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
def start_instance_from_image(client, image_id, subnet_id):
	try:
		response = client.run_instances(ImageId=image_id, MaxCount=1, MinCount=1, InstanceType="t2.micro", NetworkInterfaces=[{"SubnetId":subnet_id, "DeviceIndex":0}])
		print(response)
	except Exception as e:
		print("Error starting EC2 instance from AMI " + str(image_id) + ".\nError: " + str(e))
		


# start intances from all images
def start_instances_from_images(client, all_image_ids, subnet_id):
	for i in range(0, len(all_image_ids)):
		start_instance_from_image(client, all_image_ids[i], subnet_id)


# terminate an instance
def terminate_instance():
	return


# terminate all instances
def terminal_all_instances():
	return


# main method
if __name__=="__main__":
	source_ec2_client = authenticate.connect_ec2()
	destination_ec2_client = authenticate.connect_ec2_alt()
	source_iam_client = authenticate.connect_iam()
	destination_iam_client = authenticate.connect_iam_alt()

	# collect image ids and share them to target client
	image_ids = list_images(source_ec2_client)
	share_all_images_permissions(source_ec2_client, destination_iam_client, image_ids)

	# destination client start instance from each ami
	# need to get subnet ID to launch
	subnet_id = get_subnet_id(destination_ec2_client)
	start_instances_from_images(destination_ec2_client, image_ids, subnet_id)

	# destination client make images from each instance started
	

	# source client revoke launch permissions


	# destination client terminate all instances



