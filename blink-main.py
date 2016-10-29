#!/usr/local/bin/python3

##########################################################
# Author: Luciano Vargas Santos - lv.santos@poli.ufrj.br #
# Date: 30/09/2016                                       #
##########################################################

import sys
import os
from threading import Thread
import threading
import cv2
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets, Qt
from ui import Ui_MainWindow
import random
import time
from datetime import datetime

video_src = 'media\\video.mov'
cam_src = 'output.avi'
cam_src = 0
images = [cv2.imread('media\\' + s) for s in os.listdir('media') if s.endswith('.JPG')]


fourcc = cv2.VideoWriter_fourcc(*'XVID')
#out = cv2.VideoWriter('media\\output.avi',fourcc, 20.0, (640,480))

delay_short = 0.04
delay_medium = 1.5*delay_short
delay_long = 2.5*delay_short
delay = [delay_short, delay_medium, delay_long]
time_among_blinks_limit = 0.1

globalFrame = 0

class videoStream(Thread):
    def __init__(self, src, lock):
        # initialize the video camera stream and read the first frame
        Thread.__init__(self)
        self.src = src
        self.lock = lock
        self.capture = cv2.VideoCapture(src)
        (self.grabbed, self.currentFrame) = self.capture.read()
        self.stopped = False
    
    def captureNextFrame(self):       
        #capture frame and reverse RBG BGR and return opencv image                                      
        ret, self.currentFrame = self.capture.read()
        if (ret == 0): 
            self.capture.set(cv2.CAP_PROP_POS_AVI_RATIO , 0);
    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self
 
    def update(self):
        # keep looping infinitqely until the thread is stopped
        frame_counter = 0
        while True:
            # if the thread indicator variable is set, stop the thread
            time.sleep(0.02)
            if self.stopped:
                return
            # otherwise, read the next frame from the stream
            self.captureNextFrame()
            
    def read(self):
        # return the frame most recently read
        return self.frame

 
    def stop(self):
        # indicate that the thread should be stopped
        
        self.stopped = True
        
class webCamProcessing(videoStream):
    def __init__(self, src, lock):
        # initialize the video camera stream and read the first frame
        Thread.__init__(self)
        self.src = src
        self.lock = lock
        self.blinked = False
        self.currentImage = 0
        self.capture = cv2.VideoCapture(src)
        (self.grabbed, self.frame) = self.capture.read()
        self.stopped = False
        
    def update(self):
        scale = 1.3 
        eyes_state = True # Open
        threshold = 1
        blink_time_limit = 0.8
        blink_time_min = 0.04
        
        eyes_close_initial_time = datetime.now()
        eyes_open_initial_time = datetime.now()
        last_blink_time = datetime.now()
        num_blinks = 0

        eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')
        
        has_eyes = False
        has_eyes_time = 0


        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return
 
            # otherwise, read the next frame frameom the stream
            (self.grabbed, frame) = self.capture.read()
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = gray[110:150,230:400]
            
            ## Rotate image (only because camera in my application is upside down) ##
            rows, cols = gray.shape
            M = cv2.getRotationMatrix2D((cols/2, rows/2),180,1)
            gray = cv2.warpAffine(gray, M, (cols,rows))
           
            ############ Eyes dethreshold/2tection #######
            scaled_gray = cv2.resize(gray,None,fx=2, fy=2, interpolation = cv2.INTER_LINEAR)
            
            
            if(has_eyes == False):
                eyes = eye_cascade.detectMultiScale(scaled_gray,1.05,8)
                if(len(eyes) != 0 ):
                    has_eyes = True
                    has_eyes_time = datetime.now()    
                else:
                    continue
            else:
                if (datetime.now() - has_eyes_time).total_seconds() > 1:
                    has_eyes = False
        
            y_val = 0
            cv2.rectangle(gray, (70,0),(100, 80),(0,0,0),-1)
            gray = cv2.resize(gray,None,fx=1.8, fy=1.8, interpolation = cv2.INTER_LINEAR)
            gray = cv2.medianBlur(gray,3)
            threshold = 150

            cimg = cv2.Canny(gray,threshold/2,threshold)
            
            y_val = 0
            
            cimg = cv2.cvtColor(cimg,cv2.COLOR_GRAY2BGR)
            
            circles = cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,1,150,
                param1=threshold,param2=7,minRadius=5,maxRadius=30)

            if circles is not None:
                circles = np.uint16(np.around(circles))
                y_val = len(circles[0,:])
                for i in circles[0,:]:
                	# draw the outer circle
                    cv2.circle(cimg,(i[0],i[1]),i[2],(0,255,0),2)
                    # draw the center of the circle
                    cv2.circle(cimg,(i[0],i[1]),2,(0,0,255),3)
            #cv2.imshow("eyes", cimg)
            '''
            gray = cimg
            '''
            #time.sleep(0.05)
            
            
            
			
            ############ Blink test ###########
            
            if(y_val == 0): #Both eyes are closedq
                if (eyes_state == True):
                    eyes_close_initial_time = datetime.now()
                    eyes_state = False
            else:
                if (eyes_state == True):
                    if ((datetime.now() - last_blink_time).total_seconds() > time_among_blinks_limit and num_blinks != 0): # No su
                        self.throwImages(num_blinks)
                        num_blinks = 0

                if (eyes_state == False):
                    eyes_open_time = datetime.now()
                    blink_time = (eyes_open_time - eyes_close_initial_time).total_seconds()
                    print(blink_time)
                    if (blink_time < blink_time_limit and blink_time > blink_time_min): # blinked
                        num_blinks += 1
                    else: # The eyes stayed closed to much time - not blink
                        num_blinks = 0
                    
                    eyes_state = True
                    last_blink_time = eyes_open_time
                ###################################
                			
                #out.write(frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            self.currentFrame = gray

    def throwImages(self,blinks):
        if blinks == 0:
            self.blinked = False
        else:
            
            if blinks == 1:
                self.blinked = True
                with self.lock:
                    self.currentImage = images[0]
                    time.sleep(delay[0])
            else:
                list_delay = []
                list_delay = []
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
                if blinks <= 6:
                    for i in range(0,blinks):
                        with self.lock:
                            self.blinked = True
                            self.currentImage = list_images[i]
                            time.sleep(list_delay[i])
                            self.blinked = False
                            time.sleep(delay_short)

            random.shuffle(images)
            random.shuffle(delay)
            
            self.blinked = False
    def stop(self):
        # indicate that the thread should be stopped
        self.capture.release()
        self.stopped = True

class Gui(QtWidgets.QMainWindow):
    def __init__(self, video, eyes, parent=None):
        QtWidgets.QWidget.__init__(self,parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
       
        self.video = video
        self.eyes = eyes
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.play)
        self._timer.start(27)
        self.update()
 
    def play(self):
        try:      
            if(self.eyes.blinked == True):
                self.ui.videoFrame.setPixmap(self.convertFrame(self.eyes.currentImage))
            else:
                self.ui.videoFrame.setPixmap(self.convertFrame(self.video.currentFrame))
            self.ui.videoFrame.setScaledContents(True)
        except TypeError:
            print("No frame")
    
    def closeEvent(self, event):
        self.video.stop()
        self.eyes.stop()
        
    def convertFrame(self, frame):
        """     converts frame to format suitable for QtGui            """
        try:
            self.currentFrame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

            height,width=self.currentFrame.shape[:2]
            img=QtGui.QImage(self.currentFrame,
                              width,
                              height,
                              QtGui.QImage.Format_Grayscale8)

            img=QtGui.QPixmap.fromImage(img)
            self.previousFrame = self.currentFrame
            return img
        except:
            return None
    def keyPressEvent(self, QKeyEvent):
        super(Gui, self).keyPressEvent(QKeyEvent)
        if 'q' == QKeyEvent.text():
            self.video.stop()
            self.eyes.stop()
            sys.exit(app.exec_())

def main():
    lock = threading.Lock()

    eyesThread = webCamProcessing(cam_src,lock)
    eyesThread.start()
    
    videoThread = videoStream(video_src,lock)
    videoThread.start()

    app = QtWidgets.QApplication(sys.argv)
    ex = Gui(videoThread,eyesThread)
    ex.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()