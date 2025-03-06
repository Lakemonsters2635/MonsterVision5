# Notes on MonsterVision4.5

This should run on either RPi4 or RPI5.  I haven't tested on a RPi4.

## The various configuration files

| File | Description |
| --- | --- |
| /boot/frc.json | Contains configuration data maintained by the WPILibPi web interface.  There is no need to modify this file manually. |
| /boot/nn.json | Contains model-specific configuration data for the NN.  Copy this file from the appropriate JSON file found in the `model` direactory. |
| /boot/mv.json | Contains MonsterVision-specific configuration data. |

## mv.json

```
{
    "cameras" : [
        { "mxid" : "18443010E1176A1200", "name" : "Front", "invert" : 0, "useDepth" : 1, "nnFile" : "/boot/nn.json" },
        { "mxid" : "18443010A162011300", "name" : "Rear", "invert" : 0, "useDepth" : 1, "nnFile" : "/boot/nn.json" },
        { "mxid" : "1944301001564D1300", "name" : "Eclipse", "invert" : 0, "useDepth" : 0, "nnFile" : "/boot/nn.json" }
    ],
    "tagFamily" : "tag36h11",
    "tagSize" : 0.1651,
    "CAMERA_FPS" : 25,
    "DS_SUBSAMPLING" : 4,
    "PREVIEW_WIDTH" : 200,
    "PREVIEW_HEIGHT" : 200,
    "DS_SCALE" : 0.5,
    "showPreview" : 1
}
```

### `cameras` configures how a camera is used on the robot.

`cameras` is an array of dictionaries, each containing:

| Field | Description |
| --- | --- |
|`mxid`| matches the unique identifier of the OAK camera. |
|`name`| allows you to assign a "friendly" name to the camera. |
|`invert`| specifies that the camera is mounted upside down on the robot |
|`useDepth`| set to 1 if you want the camera to compute depth using stereo disparity.  Has no effect on April Tag depth calculation. |
|`nnFile`| Specifies the path to the NN configuration file to be used with this camera. |

### Remaining fields in `mv.json`

| Field | Description |
| --- | --- |
|`tagFamily`| The April Tag family such as `tag36h11` or `tag16h5`|
|`tagSize`| The overall size of the tag in meters.|
|`CAMERA_FPS`| The desired frame rate for image capture. |
|`DS_SUBSAMPLING`| To reduce the bandwidth between the drivers station on the Raspberry Pi, you can have MonsterVision send only a subset of frames to the DS.  This allows you to specify a subset of frame to be sent. |
|`PREVIEW_WIDTH`| currently not used. |
|`PREVIEW_HEIGHT`| currently not used. |
|`DS_SCALE`| another way to reduce bandwidth.  Tha RGB camera image (with annotations) is scaled by this factor before being sent to the drivers station. |
|`showPreview`| If True, the `preview` output of the RGB camera is sent to an XLinkOut for eventual display on systems running a GUI. |
