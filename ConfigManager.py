import json
import sys

ROMI_FILE = "/boot/romi.json"   # used when running on a Romi robot
FRC_FILE = "/boot/frc.json"     # Some camera settings incuding laser power
NN_FILE = "/boot/nn.json"       # NN config file
MV_FILE = "/boot/mv.json"       # MonsterVision Configuration file

# The purpase a ComputedValue object is to allow the value to be set in the ConfigManager class
# and then read in the derived class.  This is a way to get around the fact that Python does not
# have pointers.  The value in the ComputedValue object is set in the ConfigManager class and then
# read in the derived class.

class ComputedValue:
    def __init__(self, value):
        self.value = value

# ConfigManager is a class that reads a JSON file and sets the values of a set of variables
# __init__ takes a file name and a list of dictionaries.
# Each dictionary has three keys:
#   name: the name of the variable to set
#   value: a ComputedValue object that will be set to the value in the JSON file
#   mess: a ComputedValue object that will be set to a message if the value is not found in the JSON file

class ConfigManager:

    def __init__(self, file: str, configTable, drillDown : str = None):
        self.file = file
        self.success = False

        try:
            with open(self.file, "rt", encoding="utf-8") as f:
                j = json.load(f)
        except OSError as err:
            raise Exception("could not open '{}': {}".format(self.file, err))

        # top level must be an object
        if not isinstance(j, dict):
            raise Exception("must be JSON object")

        if drillDown is not None:
            j = j[drillDown]

        for entry in configTable:

            try:
                entry['value'].value = j[entry['name']]
            except:
                if entry['mess'] is not None:
                    raise Exception("config error in '" + self.file + "': " + entry['mess'].value)
                pass

        self.success = True

# Derive a new class from ConfigManager

class FRCConfig (ConfigManager):

    __team = ComputedValue(0)
    __hasDisplay = ComputedValue(False)
    __ntmode = ComputedValue("client")
    __LaserDotProjectorCurrent = ComputedValue(0)

    __table = [
        { "name" : "team", "value" : __team, "mess" : "Could not read team number"},
        { "name" : "hasDisplay", "value" : __hasDisplay, "mess" : None},
        { "name" : "ntmode", "value" : __ntmode, "mess" : None},
        { "name" : "LaserDotProjectorCurrent", "value" : __LaserDotProjectorCurrent, "mess" : None}
    ]

    def __init__(self, file: str):
        super().__init__( file, self.__table)

        if self.success:
            if self.__ntmode.value == "client":
                self.server = False
            elif self.__ntmode.value == "server":
                self.server = True
            else:
                success = False
                raise Exception(f"could not understand ntmode value '{self.__ntmode.value}'")
            self.team = self.__team.value
            self.hasDisplay = self.__hasDisplay.value
            self.LaserDotProjectorCurrent = self.__LaserDotProjectorCurrent.value * 1.0


class NNConfig(ConfigManager):

    __bb_fraction = ComputedValue("bb_fraction")
    __inputSize = ComputedValue((300, 300))
    __NNFamily = ComputedValue("")

    __table = [
        { "name" : "bb_fraction", "value" : __bb_fraction, "mess" : None},
        { "name" : "input_size", "value" : __inputSize, "mess" : None},
        { "name" : "NN_family", "value" : __NNFamily, "mess" : None}
    ]

    def __init__(self, file: str):
        super().__init__( file, self.__table, "nn_config")

        if self.success:
            self.bb_fraction = self.__bb_fraction.value
            self.inputSize = tuple(map(int, self.__inputSize.value.split('x')))
            self.NNFamily = self.__NNFamily.value


class MVConfig(ConfigManager):

    __tagFamily = ComputedValue("tag36h11")
    __tagSize = ComputedValue(0.1651) # meters
    __CAMERA_FPS = ComputedValue(25)
    __DS_SUBSAMPLING = ComputedValue(4)
    __PREVIEW_WIDTH = ComputedValue(200)
    __PREVIEW_HEIGHT = ComputedValue(200)
    __DS_SCALE = ComputedValue(0.5)
    __cameras = ComputedValue([])
    __showPreview = ComputedValue(False)
    __table = [
        { "name" : "cameras", "value" : __cameras, "mess" : None},
        { "name" : "tagFamily", "value" : __tagFamily, "mess" : None},
        { "name" : "tagSize", "value" : __tagSize, "mess" : None}, # meters
        { "name" : "CAMERA_FPS", "value" : __CAMERA_FPS, "mess" : None},
        { "name" : "DS_SUBSAMPLING", "value" : __DS_SUBSAMPLING, "mess" : None},
        { "name" : "PREVIEW_WIDTH", "value" : __PREVIEW_WIDTH, "mess" : None},
        { "name" : "PREVIEW_HEIGHT", "value" : __PREVIEW_HEIGHT, "mess" : None},
        { "name" : "DS_SCALE", "value" : __DS_SCALE, "mess" : None},
        { "name" : "showPreview", "value" : __showPreview, "mess" : None}
    ]

    def __init__(self, file: str):
        super().__init__( file, self.__table)
        if self.success:
            self.cameras = self.__cameras.value
            self.tagFamily = self.__tagFamily.value
            self.tagSize = self.__tagSize.value # meters
            self.CAMERA_FPS = self.__CAMERA_FPS.value
            self.DS_SUBSAMPLING = self.__DS_SUBSAMPLING.value
            self.PREVIEW_WIDTH = self.__PREVIEW_WIDTH.value
            self.PREVIEW_HEIGHT = self.__PREVIEW_HEIGHT.value
            self.DS_SCALE = self.__DS_SCALE.value
            self.showPreview = self.__showPreview.value

    def getCamera(self, mxid) -> dict:
        for cam in self.cameras:
            if cam['mxid'] == mxid:
                return cam
        print(f"CAMERA MXID({mxid}) NOT FOUND IN mv.json")
        return None


frcConfig = FRCConfig(FRC_FILE)
mvConfig = MVConfig(MV_FILE)
nnConfig = NNConfig(NN_FILE)