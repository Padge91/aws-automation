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


#copy image to region
def copy_image(ec2_client, image, old_region):
	ami=image["ImageId"]
	image_name=image["Name"]
	image_description=image["image_description"]

	try:
		print(ami)
		print(image_name)
		print(image_description)
		print(image)
		exit()
		response = ec2_client.copy_image(Name=image_name, Description=image_description, SourceImageId=ami, SourceRegion=old_region, DryRun=False)

		#get new AMI from response
		if "ImageId" not in response:
			raise Exception("Malformed response.")

		new_ami = response["ImageId"]

		#tag image
		if "Tags" in image:
			tag_image(ec2_client, new_ami, image["Tags"])

	except Exception as e:
		print("Unable to copy AMI: " + ami + " (" + image_name + ").\nError: " + str(e))
		error_ids.append("Unable to copy AMI " + ami)

	
# copy all images
def copy_all_images(ec2_client, all_images, old_region):
	for i in range(0, len(all_images)):
		copy_image(ec2_client, all_images[i], old_region)
		if trial_run:
			return
	

# get source region
def confirm_regions():
	valid_regions=["us-east-1", "us-east-2", "us-west-1", "us-west-2", "ca-central-1", "eu-west-1", "eu-central-1", "eu-west-2", "ap-northeast-1", "ap-northeast-2", "ap-southeast-1", "ap-southeast-2", "sa-east-1", "ap-south-1"]
	print("This script PULLs in AMIs from other regions. Thus, you must specify a source region to copy the AMI from.")
	print("Valid regions:" + "\n".join(valid_regions))
	region = ""
	while region not in valid_regions:
		region = input("What is the source region?")

	current_region = authenticate.read_AWS_credentials()[0]
	user_input = "Escape"
	while user_input != "Y" and user_input != "N":
		user_input =input("You are copying AMIs from " + region + " to " + current_region + ". Is this correct? (Y/N)")
		user_input = user_input.upper()

	if user_input == "N":
		print("Exiting...")
		exit()

	return region	


# main method
if __name__=="__main__":
	source_region = confirm_regions()

	source_ec2_client = authenticate.connect_ec2()
	source_iam_client = authenticate.connect_iam()

	# collect image ids and share them to target client
	print("Getting list of images...")
	client_id = get_client_info(source_iam_client)
	images_info = list_images(source_ec2_client, client_id)

	# run copy operation from old region
	print("Copying images...")	
	copy_all_images(source_ec2_client, images_info, source_region)

