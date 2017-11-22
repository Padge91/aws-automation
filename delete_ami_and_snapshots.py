import authenticate
import sys



error_ids = []
testing = False

# process cmd-line args
def process_cmd_args():
	if len(sys.argv) == 1:
		print("No AMI's specified. Exiting...")
		exit(1)

	amis = []
	for i in range(1, len(sys.argv)):
		amis.append(sys.argv[i])
	return amis


# get_snapshot_for_amis
def get_snapshots_for_amis(ec2_client, ami_list):
	try:
		images_field="Images"
		device_array_field="BlockDeviceMappings"
		ebs_field="Ebs"
		snapshot_id_field="SnapshotId"


		snapshots = []
		response = ec2_client.describe_images(ImageIds=ami_list, ExecutableUsers=[], DryRun=False)
		
		for i in range(0, len(response[images_field])):
			for i2 in range(0, len(response[images_field][i][device_array_field])):
				if ebs_field not in response[images_field][i][device_array_field][i2]:
					print("No EBS field: " + str(response[images_field][i][device_array_field][i2]))
					continue
				snapshots.append(response[images_field][i][device_array_field][i2][ebs_field][snapshot_id_field])
	
		return snapshots	
	
	except Exception as e:
		print("Could not get snapshots for ami list.\nError: " + str(e))
		exit(1)
		

#confirm option
def confirm(type):
	user_input = "Escape"
	while user_input != "Y" and user_input != "N":
		user_input = input("Are you sure you want to delete all " + str(type) + "? This action is irreversible (Y/N)")
		user_input = user_input.upper()

	if user_input == "N":
		print("Exiting...")
		exit()


# error output
def output_errors():
	print("\nNumber of errors: " + str(len(error_ids)))
	if len(error_ids) > 0:
		print("These Ids could have failed when getting snapshots, deleting the amis, or deleting the snapshots.")
		print("The full list of IDs follows:\n"+"\n".join(error_ids))


#delete images
def delete_images(ec2_client, ami_list):
	if testing:
		return
	
	for i in range(0, len(ami_list)):
		try:
			ec2_client.deregister_image(ImageId=ami_list[i], DryRun=False)
		except Exception as e:
			print("Error deleting image " + ami_list[i] + ".\nError: " + str(e))
			error_ids.append("Error deleting AMI: " + ami_list[i])


#delete snapshots
def delete_snapshots(ec2_client, snapshots_list):
	if testing:
		return

	for i in range(0, len(snapshots_list)):
		try:
			ec2_client.delete_snapshot(SnapshotId=snapshots_list[i], DryRun=False)
		except Exception as e:
			print("Error deleting snapshot " + snapshots_list[i] + ".\nError: " + str(e))
			error_ids.append("Error deleting snapshot: " + snapshots_list[i])

# main method
if __name__=="__main__":
	# read in ami id from cmd line
	ami_list = process_cmd_args()
	
	#connect to ec2
	ec2_client = authenticate.connect_ec2()

	# get snapshots of amis
	print("Getting snapshots for AMIs")
	snapshots_list = get_snapshots_for_amis(ec2_client, ami_list)

	# delete ami
	confirm("AMIs")
	delete_images(ec2_client, ami_list)

	# delete snapshots
	confirm("snapshots")
	delete_snapshots(ec2_client, snapshots_list)

	output_errors()


