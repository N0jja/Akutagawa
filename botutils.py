import os
import asyncio
from PIL import Image
import aiohttp

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
		userfile = myfile.read()
		if user.lower() in userfile.lower():
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
			if line.lower() != user.lower()+'\n':
				myfile.write(line.lower())
		myfile.close()
		os.remove('data/'+user.lower())
		return 1
	except Exception as e:
		fd = open('tracked_users', 'r')
		print(fd.read())
		fd.close()
		print(e)
		return -1

def av_color(file):
	"""
	This function process an image
	and returns the most present pixel in it
	as an hex int
	if fail, it returs default color
	"""
	try:
		image = Image.open(file)
		w, h = image.size
		pixels = image.getcolors(w * h)
		most_frequent_pixel = pixels[0]
		for count, colour in pixels:
			if count > most_frequent_pixel[0]:
				most_frequent_pixel = (count, colour)
		dbg = int('0x%02x%02x%02x' % most_frequent_pixel[1], 16)
		print(dbg)
		return dbg
	except Exception as e:
		print('[!Error!] in AV COLOR')
		print(e)
		return 0xB46BCF

async def dl_image(url, filename):
	"""
	Used to download a picture
	Returns 1 on succes
	Ro -1 on fail
	"""
	try:
		with aiohttp.ClientSession() as session:
			async with session.get(url) as resp:
				test = await resp.read()
				with open('data/tmp/'+filename.lower(), "wb") as f:
					f.write(test)
				return 0
	except Exception as e:
		print('[!ERROR!] in Get image')
		print(e)
		return -1


def flag(code):
	"""
	Returns the Unicode flag symbol 
	For a given ISO 3166-1 alpha-2 Coutry code
	"""
	OFFSET = ord('🇦') - ord('A')
	if not code:
		return u''
	points = list(map(lambda x: ord(x) + OFFSET, code.upper()))
	try:
		return chr(points[0]) + chr(points[1])
	except ValueError:
		return ('\\U%08x\\U%08x' % tuple(points)).decode('unicode-escape')
