import os

def is_admin(id):
	"""
	This fuction opens bot_admin file
	Then returns 1 if id is in the file (is admin)
	Returns 0 otherwise
	"""
	with open('bot_admin', 'r') as myfile:
		if id in myfile.read():
			return 1
	return 0

def check_user_del(user):
	"""
	This function Opens the Tracked users file
	And checks if the given user is in the file
	returns 1 on success
	returns 0 if user not found
	"""
	with open('tracked_users', 'r') as myfile:
		if user in myfile.read():
			return 1
	return 0

def del_user(user):
	"""
	This function opens Tracked users file to delete a given user
	And deletes the data of the given user
	returns 1 on success
	return -1 and prints content of the file on fail for recovery purpose
	"""
	try:
		myfile = open('tracked_users', 'r')
		lines = myfile.readlines()
		myfile.close()
		myfile = open('tracked_users', 'w')
		for line in lines:
			if line != user+'\n':
				myfile.write(line)
		myfile.close()
		os.remove('data/'+user)
		return 1
	except Exception as e:
		fd = open('tracked_users', 'r')
		print(fd.read())
		fd.close()
		print(e)
		return -1
