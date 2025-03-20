import json
from pathlib import Path
import sys
import time
import cv2
import depthai as dai
import ConfigManager as cm

scaleFactor = 1     # Scale factor for the image to reduce processing time


class CameraPipeline:

    # Set up openvino for the NN  
    openvinoVersions = dai.OpenVINO.getVersions()
    openvinoVersionMap = {}
    for v in openvinoVersions:
        openvinoVersionMap[dai.OpenVINO.getVersionName(v)] = v

    openvinoVersionMap[""] = dai.OpenVINO.DEFAULT_VERSION

    
    # devInfo: dai.DeviceInfo    # The device info object
    # useDepth: bool             # True: use depth if available, False: use RGB only
    # nnFile: str                # The neural network config file.  None if no NN is to be used

    def __init__(self, name: str, devInfo : dai.DeviceInfo, useDepth : bool, nnFile : str, monoResolution : str, rgbResolution : str):
        self.name = name
        device: dai.Device = dai.Device(devInfo)
        self.devInfo = devInfo
        self.hasDepth = useDepth and len(device.getConnectedCameras()) > 1
        self.hasLaser = len(device.getIrDrivers()) > 0
        
        # TODO move these to config file

        # We might not have a mono camera, but this cannot hurt
        self.monoResolution = monoResolution
        # self.monoWidth = 1280 UNNEEDED
        # self.monoHeight = 720 UNNEEDED

        self.rgbResolution = rgbResolution
        # self.rgbWidth = 1920 UNNEEDED
        # self.rgbHeight = 1080 UNNEEDED

        self.ispScale = (2, 3)

        self.bbfraction = 0.2 # The size of the inner bounding box as a fraction of the original

        self.NN_FILE = nnFile # "/boot/nn.json"
        self.LABELS = None

        self.pipeline = dai.Pipeline()

        self.frame = None
        self.depthFrame = None
        # self.ispFrame = None
        self.detections = None
        self.depthFrameColor = None
        self.cameraIntrinsics = None
        self.calibData = None

        return
    
    def parse_error(self, mess):
        """Report parse error."""
        print("config error in '" + self.NN_FILE + "': " + mess, file=sys.stderr)

    def read_nn_config(self):
        try: # Try to open the NN config file
            with open(self.NN_FILE, "rt", encoding="utf-8") as f:
                j = json.load(f) # Load in json format
        except OSError as err: # If file doesn't exist then throw an error
            print("could not open '{}': {}".format(self.NN_FILE, err), file=sys.stderr)
            return {}

        # top level must be an object
        if not isinstance(j, dict):
            self.parse_error("must be JSON object")
            return {}

        return j # Return the config json


    def setupSDN(self):

# If no neural network config is given, assume we are depth-only on an OAK-D
# On an OAK-1, I guess this means we're using an overly-expensive webcam :-)
        
        if self.NN_FILE is None:
            return None
        
        nnJSON = self.read_nn_config()
        self.LABELS = nnJSON['mappings']['labels']
        nnConfig = nnJSON['nn_config']
    
        # Get path to blob

        blob = nnConfig['blob']
        nnBlobPath = str((Path(__file__).parent / Path('models/' + blob)).resolve().absolute())

        if not Path(nnBlobPath).exists():
            import sys

            raise FileNotFoundError(f'Required file/s not found, please run "{sys.executable} install_requirements.py"') # CHANGE

        try:
            self.openvinoVersion = nnConfig['openvino_version']
        except KeyError:
            self.openvinoVersion = ''

        if self.openvinoVersion != '':
            self.pipeline.setOpenVINOVersion(self.openvinoVersionMap[self.openvinoVersion])
        
        try:
            self.inputSize = tuple(map(int, nnConfig.get("input_size").split('x')))
        except KeyError:
            self.inputSize = (300, 300)

        family = nnConfig['NN_family']
        if family == 'mobilenet':
            if self.hasDepth: detectionNodeType = dai.node.MobileNetSpatialDetectionNetwork
            else: detectionNodeType = dai.node.MobileNetDetectionNetwork
        elif family == 'YOLO':
            if self.hasDepth: detectionNodeType = dai.node.YoloSpatialDetectionNetwork
            else: detectionNodeType = dai.node.YoloDetectionNetwork
        else:
            raise Exception(f'Unknown NN_family: {family}')

        try:
            self.bbfraction = nnConfig['bb_fraction']
        except KeyError:
            self.bbfraction = self.bbfraction			# No change from default



        # Create the spatial detection network node - either MobileNet or YOLO (from above)

        spatialDetectionNetwork = self.pipeline.create(detectionNodeType)

        # Set the NN-specific stuff

        if family == 'YOLO':
            spatialDetectionNetwork.setNumClasses(nnConfig['NN_specific_metadata']['classes'])
            spatialDetectionNetwork.setCoordinateSize(nnConfig['NN_specific_metadata']['coordinates'])
            spatialDetectionNetwork.setAnchors(nnConfig['NN_specific_metadata']['anchors'])
            spatialDetectionNetwork.setAnchorMasks(nnConfig['NN_specific_metadata']['anchor_masks'])
            spatialDetectionNetwork.setIouThreshold(nnConfig['NN_specific_metadata']['iou_threshold'])
            x = nnConfig['NN_specific_metadata']['confidence_threshold'] # why?
            spatialDetectionNetwork.setConfidenceThreshold(x)
        else:
            x = nnConfig['confidence_threshold'] # why?
            spatialDetectionNetwork.setConfidenceThreshold(x)
        
        spatialDetectionNetwork.setBlobPath(nnBlobPath)
        spatialDetectionNetwork.setConfidenceThreshold(0.5) # Why even assign it above if we just set it to 0.5 down here
        spatialDetectionNetwork.input.setBlocking(False)

        if self.hasDepth:
            spatialDetectionNetwork.setBoundingBoxScaleFactor(self.bbfraction)
            spatialDetectionNetwork.setDepthLowerThreshold(100)
            spatialDetectionNetwork.setDepthUpperThreshold(5000)

        return spatialDetectionNetwork
    


    def buildPipeline(self, spatialDetectionNetwork, invert : bool = False):

        # Linking      
        try:
            lensPosition = dai.Device(self.devInfo).readCalibration2().getLensPosition(dai.CameraBoardSocket.RGB)
            if lensPosition:
                self.camRgb.initialControl.setManualFocus(lensPosition)
        except:
            pass

        # Define sources and outputs

        self.camRgb = self.pipeline.create(dai.node.ColorCamera)
        self.xoutRgb = self.pipeline.create(dai.node.XLinkOut)
        self.xoutRgb.setStreamName("rgb")

        if self.hasDepth:
            self.monoLeft = self.pipeline.create(dai.node.MonoCamera)
            self.monoRight = self.pipeline.create(dai.node.MonoCamera)
            self.stereo = self.pipeline.create(dai.node.StereoDepth)
            if scaleFactor != 1:
                # self.ispScaleNode = self.pipeline.create(dai.node.ImageManip)
                self.depthScaleNode = self.pipeline.create(dai.node.ImageManip)
            self.xoutDepth = self.pipeline.create(dai.node.XLinkOut)
            # self.xoutIsp = self.pipeline.create(dai.node.XLinkOut)
            self.xoutDepth.setStreamName("depth")

        if spatialDetectionNetwork is not None:
            self.xoutNN = self.pipeline.create(dai.node.XLinkOut)
            self.xoutNN.setStreamName("detections")
            self.camRgb.setPreviewSize(self.inputSize[0],self.inputSize[1]) # Probably don't need below preview size since now this

        # Properties

        self.camRgb.setResolution(self.rgbResolution)
        # self.camRgb.setPreviewSize(self.inputSize[0], self.inputSize[1]) # Added 1/28/25 because it threw an error (this affects nn input size? why?) (original 640, 640)
        self.camRgb.setInterleaved(False)
        self.camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        self.camRgb.setFps(cm.mvConfig.CAMERA_FPS)
        self.camRgb.setIspScale(self.ispScale[0], self.ispScale[1])

        if invert:
            self.camRgb.setImageOrientation(dai.CameraImageOrientation.ROTATE_180_DEG) 
        else:
            self.camRgb.setImageOrientation(dai.CameraImageOrientation.NORMAL) 

        print("Camera FPS: {}".format(self.camRgb.getFps()))

        if self.hasDepth:
            self.monoLeft.setResolution(self.monoResolution)
            self.monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
            self.monoRight.setResolution(self.monoResolution)
            self.monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

            # Setting node configs

            self.stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
            self.stereo.setLeftRightCheck(True)
            self.stereo.setDepthAlign(dai.CameraBoardSocket.RGB)
            self.stereo.setOutputSize(self.monoLeft.getResolutionWidth(), self.monoLeft.getResolutionHeight())

            if scaleFactor != 1:
                w = self.monoLeft.getResolutionWidth()
                h = self.monoLeft.getResolutionHeight()

                self.ispScaleNode.setResize(int(w/scaleFactor), int(h/scaleFactor))
                self.depthScaleNode.setResize(int(w/scaleFactor), int(h/scaleFactor))

            # Linking

            self.monoLeft.out.link(self.stereo.left)
            self.monoRight.out.link(self.stereo.right)
            sizeForIntrinsic = self.camRgb.getIspSize()


            if spatialDetectionNetwork is not None:
                self.camRgb.preview.link(spatialDetectionNetwork.input) # Why preview???
                self.camRgb.isp.link(self.xoutRgb.input)

                spatialDetectionNetwork.out.link(self.xoutNN.input)

                self.stereo.depth.link(spatialDetectionNetwork.inputDepth)

                if scaleFactor == 1:
                    spatialDetectionNetwork.passthroughDepth.link(self.xoutDepth.input)
                    # self.camRgb.isp.link(self.xoutIsp.input)
                else:
                    # self.camRgb.isp.link(self.ispScaleNode.inputImage)
                    # self.ispScaleNode.out.link(self.xoutIsp.input)
                    spatialDetectionNetwork.passthroughDepth.link(self.depthScaleNode.inputImage)
                    self.depthScaleNode.out.link(self.xoutDepth.input)
            else:
                self.camRgb.isp.link(self.xoutRgb.input)
                sizeForIntrinsic = self.camRgb.getIspSize()
                self.stereo.depth.link(self.xoutDepth.input)
                # if scaleFactor == 1:
                #     self.camRgb.isp.link(self.xoutIsp.input)
                # else:
                #     self.camRgb.isp.link(self.ispScaleNode.inputImage)
                #     self.ispScaleNode.out.link(self.xoutIsp.input)

            # self.xoutIsp.setStreamName("isp")
        else:
            self.camRgb.isp.link(self.xoutRgb.input) # If not using a NN then link the camera output directly to the xLink rgb output node
            sizeForIntrinsic = self.camRgb.getIspSize()
            if spatialDetectionNetwork is not None:
                self.camRgb.preview.link(spatialDetectionNetwork.input) # Link camera's preview output to the input of the NN node
                spatialDetectionNetwork.out.link(self.xoutNN.input) # Link NN output to the xLink detections output node

        self.device = dai.Device(self.pipeline, self.devInfo)

        self.cameraIntrinsics = self.device.readCalibration().getCameraIntrinsics(dai.CameraBoardSocket.CAM_A, sizeForIntrinsic[0], sizeForIntrinsic[1])
        
        return
    

    def serializePipeline(self):
        serialized = self.pipeline.serializeToJson()

        with open("pipeline_config.json", "w") as f:
            json.dump(serialized, f, indent=4)
        return

    def startPipeline(self):

        self.queues = []
        self.lastFrameTime = time.time_ns() / 1.0e9
        self.fps = 0

        if self.NN_FILE is not None:
            detectionNNQueue = self.device.getOutputQueue(name="detections", maxSize=4, blocking=False) # Get the NN data from the queue
            self.queues.append((detectionNNQueue, "detectionNN"))

        # For now, RGB needs fixed focus to properly align with depth.
        # This value was used during calibration
            # Try to calibrate the camera
        if self.hasDepth:
            try:
                self.calibData = self.device.readCalibration2()
                print(f"Calibration Data: {self.calibData}")
                lensPosition = self.calibData.getLensPosition(dai.CameraBoardSocket.RGB)
                if lensPosition:
                    self.camRgb.initialControl.setManualFocus(lensPosition)
            except:
                print("Camera calibration failed!")
                pass

            # Output queues will be used to get the rgb frames and nn data from the outputs defined above
            previewQueue = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            self.queues.append((previewQueue, "preview"))

            depthQueue = self.device.getOutputQueue(name="depth", maxSize=4, blocking=False)
            self.queues.append((depthQueue, "depth"))

            # ispQueue = self.device.getOutputQueue(name="isp", maxSize=4, blocking=False)
            # self.queues.append((ispQueue, "isp"))

            if self.hasLaser:
                if not self.device.setIrLaserDotProjectorBrightness(cm.frcConfig.LaserDotProjectorCurrent):
                    print("Projector Fail")

        else:
            rgbQueue = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            self.queues.append((rgbQueue, "rgb"))

        # # Start the pipeline
        # self.device.startPipeline(self.pipeline)

    def processNextFrame(self):
        anyChanges = False
        depthChanged = False

        for q, name in self.queues:
            if q.has():
                anyChanges = True
                match name:
                    case "preview":
                        self.frame = q.get().getCvFrame()
                        #print("Preview:", self.frame.shape)
                    case "depth":
                        self.depthFrame = q.get().getFrame()
                        #print("depth")
                        depthChanged = True
                    case "isp":
                        q.get().getCvFrame()            # TODO get rid of this completely
                    case "rgb":
                        self.frame = q.get().getCvFrame()
                        #print("RGB:", self.frame.shape)
                    case "detectionNN":
                        self.detections = q.get().detections
        
        if anyChanges:
            now = time.time_ns() / 1.0e9
            self.fps = int(1/(now - self.lastFrameTime))
            self.lastFrameTime = now



        if depthChanged:
            self.depthFrameColor = cv2.normalize(self.depthFrame, None, 255, 0, cv2.NORM_MINMAX, cv2.CV_8UC1)
            self.depthFrameColor = cv2.equalizeHist(self.depthFrameColor)
            self.depthFrameColor = cv2.applyColorMap(self.depthFrameColor, cv2.COLORMAP_RAINBOW)

        return anyChanges
    
