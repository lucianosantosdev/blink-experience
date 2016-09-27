import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import random
import time
from datetime import datetime

##################### Images sources #####################
video = cv2.VideoCapture('media\\video.avi')

images = [cv2.imread('media\\' + s,cv2.IMREAD_GRAYSCALE) for s in os.listdir('media') if s.endswith('.JPG')]

print(images)

cap = cv2.VideoCapture(0)
eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

## Image Window fullscreen
cv2.namedWindow("video", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("video",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
#########################################################:

############## Global Variables #########
debug = False
rotate = False

scale = 1.5
eyes_state = True # Open
threshold = 1
blink_time_limit = 0.3
time_among_blinks_limit = 0.2

eyes_close_initial_time = datetime.now()
eyes_open_initial_time = datetime.now()
last_blink_time = datetime.now()
num_blinks = 0

filter_window = 5
delay_short = 0.5
delay_medium = 2*delay_short
delay_long = 3*delay_short
delay = [delay_short, delay_medium, delay_long]

list_index = []
list_delay = []
#########################################

def drawMask(cap, x1,y1,x2,y2):
	ret, img = cap.read()
	img = cv2.resize(img,None,fx=scale, fy=scale, interpolation = cv2.INTER_LINEAR)
	rows,cols,channels = img.shape
	mask_eyes = np.zeros((rows,cols), np.uint8)
	cv2.rectangle(mask_eyes, (x1,y1),(x2, y2),(255,255,255),-1)
	return mask_eyes

def throwImages(blinks):
	if blinks == 1:
		cv2.imshow("video",images[0])
		time.sleep(delay[0])
		random.shuffle(delay)
	else:
		if blinks == 2:
			list_images = [images[0], images[0]]
			list_delay = [delay_short, delay_medium]
		if blinks == 3:
			list_images = [images[0], images[0], images[1]]
			list_delay = [delay_short, delay_short, delay_medium]
		if blinks == 4:
			list_images = [images[0], images[0], images[1], images[1]]
			list_delay = [delay_short, delay_short, delay_short, delay_short]
		if blinks == 5:
			list_images = [images[0], images[0], images[0], images[1], images[1]]
			list_delay = [delay_short, delay_short, delay_short, delay_short, delay_short]
		if blinks == 6:
			list_images = [images[0], images[0], images[1], images[1], images[1], images[2]]
			list_delay = [delay_short, delay_short, delay_short, delay_short, delay_short, delay_medium]
		for i in range(0,blinks - 1):
			cv2.imshow("video",list_images[i])
			print(list_delay[i])
			time.sleep(list_delay[i])		
	random.shuffle(images)

def plotGraph(value,ydata, line):
	ydata.append(value)
	del ydata[0]
	line.set_xdata(np.arange(len(ydata)))
	line.set_ydata(ydata)
	plt.pause(0.0000001)

if __name__ == "__main__":
	##### Plot parameters ###############
	if debug == True:
		plt.ion() # set plot to animated
		max_y = 3
		plt.ylim([0,max_y]) # set the y-range to 10 to 40
		ydata = [0] * 50
		line, = plt.plot(ydata)
	#####################################
	
	mask_eyes = drawMask(cap,200,400,900,600)

	########## Main Loop #################
	while True:
		############ Play Video ###########
		ret_video, frame = video.read()
		cv2.imshow('video',frame)
		###################################

		############ Image Treatment ######
		ret_cap, img = cap.read()
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

		#gray = cv2.bitwise_and(gray, gray, mask=mask_eyes) # Apply mask to only get interested image
		
		gray = cv2.resize(gray,None,fx=scale, fy=scale, interpolation = cv2.INTER_LINEAR)
		gray = cv2.medianBlur(gray,5)
		## Rotate image (only because camera in my application is upside down) ##
		if rotate == True:
			rows, cols = gray.shape
			M = cv2.getRotationMatrix2D((cols/2, rows/2),180,1)
			gray = cv2.warpAffine(gray, M, (cols,rows))
		##
		###################################

		############ Eyes detection #######
		eyes = eye_cascade.detectMultiScale(gray,1.3,15)
		y_val = len(eyes)
		###################################
	
		############ Blink test ###########
		if(y_val == 0): #Both eyes are closed
			if (eyes_state == True):
				eyes_close_initial_time = datetime.now()
				eyes_state = False
		else:
			if (eyes_state == True):
				if ((datetime.now() - last_blink_time).total_seconds() > time_among_blinks_limit and num_blinks != 0): # No su
					throwImages(num_blinks)
					num_blinks = 0

			if (eyes_state == False):
				eyes_open_time = datetime.now()
				blink_time = (eyes_open_time - eyes_close_initial_time).total_seconds()
				if (blink_time < blink_time_limit): # blinked
					num_blinks += 1
				else: # The eyes stayed closed to much time - not blink
					num_blinks = 0
				
				eyes_state = True
				last_blink_time = eyes_open_time
		###################################
	
		############ DEBUG ################
		if debug == True:
			plotGraph(y_val, ydata, line)
			pass
		
		if debug == True:
			cv2.imshow('img',gray)
			pass
		###################################
		
		# Press q to exit program
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
		######################################

	cv2.waitKey(0)
	cap.release()
	cv2.destroyAllWindows()
