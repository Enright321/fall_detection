#import packages
import cv2
import time
from datetime import datetime
import imutils
from imutils.video import VideoStream
import sys
import argparse
import ctypes

# Globals
start_alert_timer = 0
default_timer = 10
current_alert_timer = default_timer
alert_timer_threshold = default_timer
status_text = "No movement detected."
previous_status_text = "NULL"
prev_prev_status_text = "Null"
alert_sent = False
fall_detected = False
person_in_frame = False

# This function inizilizes the program


def initializeProgram():
    try:
        createLogFile()
        ap = argparse.ArgumentParser()
        ap.add_argument("-a", "--min-area", type=int,
                        default=4000, help="minimum area size")
        args = vars(ap.parse_args())
        first_frame = None
        capture = startCapture()
        writeToLog("Program fully initilized!")
        frame_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return args, first_frame, capture, frame_width, frame_height
    except:
        writeToLog("ERROR: Initilization failed!")
        sys.exit()

# This function trys to create a log file


def createLogFile():
    try:
        log_file = open("Test_Event_Log.txt", "a+")
        log_file.write(
            "********************New Initialization********************\n\n")
        log_file.close()
        writeToLog("Event Log Initialized!")
    except:
        print("Log File failed to generate. Terminating program...")
        sys.exit()

# This function is called when an event is needed to be written to a log


def writeToLog(strEvent):
    log_file = open("Test_Event_Log.txt", "a+")
    log_file.write("["+getTimeStamp()+"] - "+strEvent+"\n")
    log_file.close()

# This function acquires a timestamp


def getTimeStamp():
    now = datetime.now()
    now = now.strftime("%d%b%Y %H%M%S")
    return now

# This function trys to initialized the camera feed


def startCapture():
    try:
        capture = cv2.VideoCapture(0)
        #capture = cv2.VideoCapture("test.mp4")
        #capture = cv2.VideoCapture("Demo - Normal.mp4")
        #capture = cv2.VideoCapture("Demo - Lowthreshold.mp4")

        writeToLog("Camera feed sucessfully acquired!")
        return capture
    except:
        writeToLog("No camera detected. Closing Program...")
        sys.exit()

# This function processes the video


def processVideo(frame, args, first_frame):
    global status_text, previous_status_text, prev_prev_status_text
    prev_prev_status_text = previous_status_text
    previous_status_text = status_text
    status_text = "No movement detected."
    frame = imutils.resize(frame, width=500)
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    frame_blur = cv2.GaussianBlur(frame_gray, (21, 21), 5)
    if first_frame is None:
        first_frame = frame_blur
    frame_delta = cv2.absdiff(first_frame, frame_blur)
    frame_thresh = cv2.threshold(frame_delta, 20, 255, cv2.THRESH_BINARY)[1]
    frame_dilate = cv2.dilate(frame_thresh, None, iterations=15)
    contours_find = cv2.findContours(
        frame_dilate.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_grab = imutils.grab_contours(contours_find)
    for c in contours_grab:
        if cv2.contourArea(c) < args["min_area"]:
            continue
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        monitorSubject(w, h)
    enterExit()
    return frame, first_frame

# This function monitors a subject when in frame


def monitorSubject(x_axis, y_axis):
    x = int(x_axis)
    y = int(y_axis)
    global status_text, alert_sent, alert_timer_threshold, current_alert_timer, start_alert_timer
    if alert_sent == True:
        status_text = "Alert has been Sent. Awaiting help..."
    elif x > y:
        if current_alert_timer <= 0:
            writeToLog("Alert has been Sent. Awaiting help...")
            start_alert_timer = 0
            current_alert_timer = alert_timer_threshold
            alert_sent = True
        elif start_alert_timer != 0:
            status_text = "Subject appears to have fallen."
            current_alert_timer = alert_timer_threshold - \
                (time.time() - start_alert_timer)
        else:
            status_text = "Subject appears to have fallen."
            start_alert_timer = time.time()
            writeToLog(
                "Suspected fall has occured. An alert will be sent if subject does not stand back up within 10 seconds.")
    elif x < y:
        if current_alert_timer < alert_timer_threshold:
            start_alert_timer = 0
            current_alert_timer = alert_timer_threshold
            writeToLog("Subject has returned to an upright position.")
            status_text = "Subject is safe."
        elif current_alert_timer == alert_timer_threshold:
            status_text = "Subject is safe."

# Entry/Exit logging. Designed misread frames don't incorrectly log


def enterExit():
    global prev_prev_status_text, status_text
    if prev_prev_status_text == "No movement detected." and previous_status_text == "No movement detected." and status_text == "Subject is safe.":
        writeToLog("Subject has entered the camera's view.")
    elif prev_prev_status_text == "Subject is safe." and previous_status_text == "No movement detected." and status_text == "No movement detected.":
        writeToLog("Subject has left the camera's view.")

# This function sends an alert


def sendAlert():
    status_text = "Awaiting Response..."

# This is the code for the alert box


def alertBox(title, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

# This function displays the Video


def displayVideo(frame):
    # Add timestamp to the video then display
    frame = cv2.putText(frame, "Date/Time: {}".format(getTimeStamp()),
                        (5, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.putText(frame, "Room Status: {}".format(status_text),
                (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.imshow("Fall Alert Detection System", frame)

# This function closes the program


def closeProgram(capture):
    writeToLog("Terminating Program...\n\n\n")
    capture.release()
    cv2.destroyAllWindows()
    sys.exit()

# This is the main function of the program


def main():
    args, first_frame, capture, frame_width, frame_height = initializeProgram()
    while (True):
        ret, frame = capture.read()
        if frame is None:
            break
        frame, first_frame = processVideo(frame, args, first_frame)
        displayVideo(frame)
        time.sleep(0.05)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    closeProgram(capture)


# Script
if __name__ == "__main__":
    main()
