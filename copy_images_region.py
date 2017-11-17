import authenticate
import os
import time


target_region="us-east-1"


error_images=[]
trial_run=True


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


#copy image to region
def copy_image():

	
# copy all images
def copy_all_images():
	
	



# main method
if __name__=="__main__":
	# get list of images in region

	# run copy operation to new region

	# once copied, need to tag them again

