#!/usr/bin/env python3

import cv2
import depthai as dai
import time

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
monoLeft = pipeline.create(dai.node.MonoCamera)
aprilTag = pipeline.create(dai.node.AprilTag)

xoutMono = pipeline.create(dai.node.XLinkOut)
xoutAprilTag = pipeline.create(dai.node.XLinkOut)

xoutMono.setStreamName("mono")
xoutAprilTag.setStreamName("aprilTagData")

# Properties
monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)

aprilTag.initialConfig.setFamily(dai.AprilTagConfig.Family.TAG_36H11)

# Linking
aprilTag.passthroughInputImage.link(xoutMono.input)
monoLeft.out.link(aprilTag.inputImage)
aprilTag.out.link(xoutAprilTag.input)
# always take the latest frame as apriltag detections are slow
aprilTag.inputImage.setBlocking(False)
aprilTag.inputImage.setQueueSize(1)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    # Output queue will be used to get the mono frames from the outputs defined above
    monoQueue = device.getOutputQueue("mono", 8, False)
    aprilTagQueue = device.getOutputQueue("aprilTagData", 8, False)

    color = (0, 255, 0)

    startTime = time.monotonic()
    counter = 0
    fps = 0

    while(True):
        inFrame = monoQueue.get()

        counter+=1
        current_time = time.monotonic()
        if (current_time - startTime) > 1 :
            fps = counter / (current_time - startTime)
            counter = 0
            startTime = current_time

        frame = inFrame.getCvFrame()

        aprilTagData = aprilTagQueue.get().aprilTags
        for aprilTag in aprilTagData:
            xmin = int(aprilTag.points.x)
            ymin = int(aprilTag.points.y)
            xmax = xmin + int(aprilTag.points.width)
            ymax = ymin + int(aprilTag.points.height)

            idStr = "ID: " + str(aprilTag.id)
            cv2.putText(frame, idStr, (xmin + 10, ymin + 35), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)

            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, cv2.FONT_HERSHEY_SIMPLEX)


        cv2.putText(frame, "Fps: {:.2f}".format(fps), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, (255,255,255))

        cv2.imshow("mono", frame)

        if cv2.waitKey(1) == ord('q'):
            break
