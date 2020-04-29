import cv2
import base64
import numpy as np

class VideoCamera(object):
    def __init__(self):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture(0)
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        self.video = cv2.VideoCapture('video.mp4')
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        ret, jpeg = cv2.imencode('.jpg', image)
        #jpeg = cv2.GaussianBlur(jpeg, (15,15), 0)
        jpeg = base64.b64encode(jpeg).decode('utf8')
        return jpeg
    
    def stop(self):
        self.video.release() 

    def montion_detection(self):
        fgbg = cv2.createBackgroundSubtractorMOG2(50, 200, True) #history, trashold, detectShadows
        FrameCount = 0
        while True:
            ret, frame = self.video.read()
            if not ret:
                break
            FrameCount += 1
            resizedFrame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            fgmask = fgbg.apply(resizedFrame)

            count = np.count_nonzero(fgmask)

            #print('Frame: %d, Pixel count %d' %(FrameCount, count))
            
            if(FrameCount > 1 and count > 700):
                print('Detected motion!!!')
                #cv2.putText(resizedFrame, 'Someone is moving', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)
            cv2.imshow('frame', resizedFrame)
            cv2.imshow('mask', fgmask)

            k = cv2.waitKey(1) & 0xff
            if k == 27:
                break
            self.video.release()
            cv2.destroyAllWindows()

VideoCamera().montion_detection()