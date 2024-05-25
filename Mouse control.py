import time
import cv2
from cvzone.HandTrackingModule import HandDetector
import cvzone
import pyautogui
import numpy as np
import mouse
from pynput.keyboard import Controller

# Define screen resolution and frame reduction for processing
wCam, hCam = 640, 480
frameR = 100  # Frame Reduction

# Initialize video capture and hand detector
cap = cv2.VideoCapture(0)
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Get screen width and height
wScr, hScr = pyautogui.size()

# Smoothing factor for cursor movement
smoothening = 7

# Initialize variables for tracking previous and current cursor positions
pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0

# Define keyboard layout
keyboard_controller = Controller()
keyboard = [['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
            ]

# Set initial mode (mouse or keyboard)
mode = 'mouse'


def draw_all(img, button_list):
    """Draws all buttons on the screen."""
    for button in button_list:
        x, y = button.pos
        w, h = button.size
        cv2.rectangle(img, button.pos, (x + w, y + h), (255, 0, 255), cv2.FILLED)
        cv2.putText(img, button.text, (x + 7, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
    return img


class Button:
    """Represents a button on the screen."""

    def __init__(self, pos, text, size=None):
        if size is None:
            size = [45, 45]
        self.pos = pos
        self.text = text
        self.size = size


# Create a list of buttons for the keyboard layout
buttons_list = []
for i in range(1, len(keyboard) + 1):
    for index, letter in enumerate(keyboard[i - 1]):
        buttons_list.append(Button(pos=[680 + 60 * index, 70 * i], text=letter))

while True:
    # Capture frame from video stream
    ret, img = cap.read()

    # Create a full-screen image with space for side-by-side display
    full_screen = np.zeros((480, 1281, 3), np.uint8)
    full_screen[0:480, 0: 640] = img
    full_screen[0:480, 641:(641 + 640)] = img

    # Detect hands in the frame
    hands, img = detector.findHands(img, draw=True)

    # Define region of interest for hand tracking (excluding borders)
    x1 = frameR
    y1 = frameR
    x2 = wCam - frameR
    y2 = hCam - frameR
    w = x2 - x1
    h = y2 - y1

    # Draw rectangle based on current mode (mouse or keyboard)
    if mode == 'mouse':
        cvzone.cornerRect(full_screen, (x1, y1, w, h))
    elif mode == 'keyboard':
        draw_all(full_screen, buttons_list)

        # Process hand detection results if hands are found
    if hands:
        lmList, bbBox = hands[0].get('lmList'), hands[0].get('bbox')
        fingers = detector.fingersUp(hands[0])

        # Switch between mouse and keyboard mode based on finger gestures
        if fingers[0:] == [1, 1, 1, 1, 1]:
            if mode == 'mouse':
                mode = 'keyboard'
            elif mode == 'keyboard':
                mode = 'mouse'
            time.sleep(0.3)  # Debounce to avoid accidental switching

        if mode == 'mouse':
            # Check if hand is within the designated tracking area
            if x1 < lmList[8][0] < x2:
                if y1 < lmList[8][1] < y2:

                    # Check for mouse move gesture (index finger up, middle finger down)
                    if fingers[1] == 1 and fingers[2] == 0:
                        x = int(lmList[8][0])  # Get x-coordinate of index fingertip
                        y = int(lmList[8][1])  # Get y-coordinate of index fingertip
                        cv2.circle(img=full_screen, center=(x, y), radius=30, color=(0, 255, 255))

                        # Map hand position to screen coordinates (considering frame borders)
                        x3 = int(np.interp(x, (frameR, wCam - frameR), (0, wScr)))
                        y3 = int(np.interp(y, (frameR, hCam - frameR), (0, hScr)))

                        # Smooth cursor movement for better control
                        clocX = plocX + (x3 - plocX) / smoothening
                        clocY = plocY + (y3 - plocY) / smoothening

                        # Move mouse cursor to the mapped screen position
                        mouse.move(wScr - clocX, clocY)

                        # Update previous cursor position for smooth tracking
                        plocX, plocY = clocX, clocY

                        # Check for click gesture (both index and middle finger up)
                    elif fingers[1] == 1 and fingers[2] == 1:
                        cv2.circle(img=full_screen, center=(lmList[8][0], lmList[8][1]), radius=30, color=(0, 255, 255))
                        cv2.circle(img=full_screen, center=(lmList[12][0], lmList[12][1]), radius=30,
                                   color=(0, 255, 255))
                        if detector.findDistance(lmList[8][0:2], lmList[12][0:2])[0] < 25:
                            pyautogui.click()
                            time.sleep(0.2)
        elif mode == 'keyboard':
            for button in buttons_list:
                x, y = button.pos
                w, h = button.size
                if x < lmList[8][0] + 640 < x + w and y < lmList[8][1] < y + h:
                    cv2.rectangle(full_screen, button.pos, (x + w, y + h), (0, 0, 255), cv2.FILLED)
                    cv2.putText(full_screen, button.text, (x + 7, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                    if fingers[1] == 1 and fingers[2] == 1:
                        cv2.circle(img=full_screen, center=(lmList[8][0], lmList[8][1]), radius=30, color=(0, 255, 255))
                        cv2.circle(img=full_screen, center=(lmList[12][0], lmList[12][1]), radius=30,
                                   color=(0, 255, 255))
                        if detector.findDistance(lmList[8][0:2], lmList[12][0:2])[0] < 25:
                            keyboard_controller.press(button.text)
                            keyboard_controller.release(button.text)
                            time.sleep(0.3)
    cv2.imshow('Window', full_screen)

    if not ret:
        break
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
