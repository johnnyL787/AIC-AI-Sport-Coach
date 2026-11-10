import cv2
import numpy as np

video = cv2.VideoCapture("")
if not video.isOpened():
    print("Error: Could not open video file.")
    exit()
while True:
    ret, frame = video.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (11, 11), 0)

    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp =1.2, minDist = 30, param1 = 50, param2 = 30, minRadius = 10, maxRadius = 60)
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            cv2.circle(frame, (x, y), r, (0, 255, 0), 4)
    cv2.imshow("Ball Tracking", frame)
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break
video.release()
cv2.destroyAllWindows()

