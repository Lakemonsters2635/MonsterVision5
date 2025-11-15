# MonsterVision Documentation

This should run on RPI5. No testing done on RPI4 yet

## How to set up Raspberry Pi 5 with WPILibPi and MonsterVision5 (FOR SETUP ON ROBOT)
1. Run `git clone https://github.com/Lakemonsters2635/MonsterVision5.git`
1. Run `tar -czvf MonsterVision5.tar.gz MonsterVision5` (remove the v if verbosity is not desired)

1. Download most recent WPILibPi image from [here](https://github.com/wpilibsuite/WPILibPi/releases) (scroll down to "Assets" and select WPILibPi, not Romi)
1. Extract downloaded .zip file
1. Download and install Raspberry Pi Imager from [here](https://www.raspberrypi.com/software/)
1. Insert a micro SD card
9000. Select the device you have, "Use Custom" under Operating System, and the micro SD card in Raspberry Pi Imager
1. Insert SD card into Pi and plug into an Aux port in your radio on the robot (make sure you turn the robot on and give the pi power)
1. May need to wait 2-5 minutes for pi to boot for the first time
1. ssh into the Raspberry Pi with `ssh pi@wpilibpi.local` (you may need to run `ssh-keygen -R wpilibpi.local -f <your known_hosts file path>`)
2. Navigate to [wpilibpi.local](http://wpilibpi.local) and click "Writable" at the top of the page
1. Navigate to the "Application" tab on wpilibpi.local and click "choose file" then select your MonsterVision5.tar.gz file and click "Upload" (Do not check extract)
1. In the ssh run these commands:
```shell
tar -xzf MonsterVision5.tar.gz
rm MonsterVision5.tar.gz
cd MonsterVision5
dos2unix *
sudo sh resize.sh
sudo sh setup.sh <TEAM NUMBER>
```
_____________________________________________________________________________________________________________
## Illustration for Pi setup on robot:
<img width="526" height="333" alt="VisionElectricalSetup (1)" src="https://github.com/user-attachments/assets/84e886ce-f4fe-4824-93ad-49ff164bd785" />


_____________________________________________________________________________________________________________
## How to use Pi's for MV Development
This document covers installing MonsterVision5 on a Raspberry Pi development machine.

It is recommended (but not required) that you use an SSD rather than an SD card on your Pi.  If you do, you may need to enable your Pi to boot from the SSD.  This only needs to be done once.  [Follow these instructions.](https://peyanski.com/how-to-boot-raspberry-pi-4-from-ssd/#:~:text=To%20boot%20Raspberry%20Pi%204%20from%20SSD%20you,USB%20to%20boot%20raspberry%20Pi%204%20from%20SSD.)
At this time it is important to note that SSDs are not competition legal for FRC.

Once you've gotten your Pi up and running, follow this procedure:

### 1. Start with installing Visual Studio Code (which should also install CMake):
You can skip this step if you just want to install CMake on your own but I haven't tested if that works.
Visual Studio Code is the preferred development environment for consistency with our general FRC code development.  It is officially distributed via the Raspberry Pi OS APT repository in both 32- and 64-bit versions:  Install via:
```shell
sudo apt update
sudo apt install code
```
It can be launched with from a terminal via `code` or via the GUI under the **Programming** menu.

### 2. Start a Terminal session:
Within the session:

Clone the MonsterVision5 repo:
```shell
git clone https://github.com/Lakemonsters2635/MonsterVision5.git
```

For development, it is best to use a Python virtual environment to keep from descending into "version hell."  Create the virtual environment and activate it. This also prevents the package managers from clashing and can make the process of installing smoother

Change to the MonsterVision5 directory:
```shell
cd MonsterVision5
```
_____________________________________________________________________________________________________________

## The various configuration files

| File | Description |
| --- | --- |
| /boot/mv.json | Contains MonsterVision-specific configuration data. |
| /boot/frc.json | Contains configuration data maintained by the WPILibPi web interface.  There is no need to modify this file manually. |
| /boot/nn.json | Contains model-specific configuration data for the NN.  Copy this file from the appropriate JSON file found in the `model` direactory. |

## mv.json
example of what `mv.json` may look like: 
```json
{
    "cameras" : [
        { "mxid" : "18443010E1176A1200", "name" : "Front", "invert" : 0, "monoResolution" : "THE_400_P", "rgbResolution" : "THE_720_P" },
        { "mxid" : "18443010A162011300", "name" : "Rear", "invert" : 0, "monoResolution" : "THE_400_P", "rgbResolution" : "THE_1080_P" },
        { "mxid" : "1944301001564D1300", "name" : "Eclipse", "invert" : 0, "monoResolution" : "THE_400_P", "rgbResolution" : "THE_800_P" }
    ],
    "tagFamily" : "tag36h11",
    "tagSize" : 0.1651,
    "CAMERA_FPS" : 25,
    "DS_SUBSAMPLING" : 4,
    "PREVIEW_WIDTH" : 200,
    "PREVIEW_HEIGHT" : 200,
    "DS_SCALE" : 0.5,
    "showPreview" : true
}
```

### `cameras` configures how a camera is used on the robot.

`cameras` is an array of dictionaries, each containing:

| Field | Description |
| --- | --- |
|`mxid`| matches the unique identifier of the OAK camera. |
|`name`| allows you to assign a "friendly" name to the camera (usually named by location on robot). |
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

## frc.json
example of what `frc.json` may look like: 
```json
{
    "cameras": [
        {
            "fps": 30,
            "height": 120,
            "name": "rPi Camera 0",
            "path": "/dev/video0",
            "pixel format": "mjpeg",
            "stream": {
                "properties": []
            },
            "width": 160
        }
    ],
    "ntmode": "client",
    "switched cameras": [],
    "team": 2635,
    "LaserDotProjectorCurrent": 765.0
}
```

|Entry|Values||
|---|---|---|
|`cameras`|Standard camera stream thing||
|`ntmode`|**client**|Network tables server hosted remotely|
||**server**|Network tables server hosted locally|
|`team`|Team number||
|`hasDisplay`|**0**|Host is headless|
||**1**|Host has attached display - depth and annotation windows will be displayed|
|`LaserDotProjectorCurrent`|Desired Current|This is for an OAK-D Pro and if you don't have one you can remove it. 765 mA is the most efficent value but you can put in any value (don't go above 1000.0)|

## nn.json
example of what `nn.json` may look like: 
```json
{
    "model": {
        "xml": "2025.xml",
        "bin": "2025.bin"
    },
    "nn_config": {
        "blob": "2025.blob",
        "output_format": "detection",
        "NN_family": "YOLO",
        "input_size": "512x512",
        "NN_specific_metadata": {
            "classes": 2,
            "coordinates": 4,
            "anchors": [],
            "anchor_masks": {},
            "iou_threshold": 0.5,
            "confidence_threshold": 0.5
        }
    },
    "mappings": {
        "labels": [
            "algae",
            "coral"
        ]
    },
    "version": 1
}
```

### `model` configures model data.

`model` is a json of file names:

| Field | Description |
| --- | --- |
|`xml`| Contains the XML data |
|`bin`| Contains the bin data |

### `nn_config` configures neural network parameters.

`nn_config` is a json of strings:

| Field | Description |
| --- | --- |
|`blob`| Contains the blob file, may need to add manually |
|`output_format`| Contains the format type of the output |
|`NN_FAMILY`| Neural network *adrien brain word* |
|`input_size`| Contains neural network input image dimensions |

### `NN_specific_metadata` contains important metadata.

`NN_specfic_metadata` is a json in `nn_config` that contains integers:

| Field | Description |
| --- | --- |
|`classes`| Number of classes to detect |
|`coordinates`| YOLO-specific parameter |
|`anchors`| List of YOLO-specific anchors |
|`anchor_masks`| Json of lists of indices for YOLO masks |
|`iou_threshold`| Intersection over Union threshold for YOLO masks |
|`confidence_threshold`| Minimum confidence for output detection |

### `mappings` contains label names.
`mappings` is a json of a list of labels

| Field | Description |
| --- | --- |
|`labels`| A list of class names |

### Remaining fields in `nn.json`

| Field | Description |
| --- | --- |
|`version`| Neural network version number, has no effect |

_____________________________________________________________________________________________________________

## How to toggle the camera server
1. Open command prompt
2. `ssh pi@wpilibpi` or `ssh pi@wpilibpi.local`
3. Go to [wpilibpi.local webserver](http://wpilibpi.local/) and change it to writable
4. `sudo nano /boot/mv.json`
5. Change the `'showPreview'` key to `false` or `true` depending on whether or not you need it
6. Restart MonsterVision

How to Restart MonsterVision:
1. Go to [wpilibpi.local webserver](http://wpilibpi.local/) and go to Vision Status
2. Click the red Kill button

IF KILL/TERMINATE doesn't seem to work then you have to go into htop and SIGKILL the main MonsterVision4.5.py:
1. Open command prompt
2. `ssh pi@wpilibpi` or `ssh pi@wpilibpi.local`
3. Go to [the wpilibpi.local webserver](http://wpilibpi.local/) and change it to writable
4. `htop` in terminal to view all processes
5. Click on the `python3 ./MonsterVision4.5.py` (should be in green)
6. Type `fn+f9` and then '9' to execute the SIGKILL command to kill the process
7. Hit enter to execute the command

## How to Disable Network Adapters for Competition
Laptop network wifi needs to be disabled for competition. Also secondary ethernet besides the one on the adapter for hardwiring needs to be disabled
1. Type `windows+r` to open up Windows command Runner
2. Run `ncpa.cpl`
3. Disable Wifi and any secondary ethernet connector (likely the highest number adapter)

_____________________________________________________________________________________________________________
## How to change model used
1. Open command prompt
2. `ssh pi@wpilibpi` or `ssh pi@wpilibpi.local`
3. Go to [wpilibpi.local webserver](http://wpilibpi.local/) and change it to writable
4. Type `cd ./<path to MonsterVision>/models`
6. Type `sudo cp ./<desired model .json file> /boot/nn.json`
7. Type `mv ./<latest best.blob> ./<appropriate name for .blob given season>`
8. Type `sudo nano /boot/nn.json`
9. Add between lines 6 and 7 (6.5) `"blob": "<chosen appropriate name given season>", `

6 7?
_____________________________________________________________________________________________________________
## How to do remote development on Pi
Create a git repo and have it synced with GitHub.

Commands may need to be ran through `sudo`

### Edit code through Pi:
1. Go to [wpilibpi.local webserver](http://wpilibpi.local/) and change it to writable
2. Open VSCode
3. Navigate to Remote Explorer extension on left-hand menu
4. Make sure the dropdown menu at the top has `Remotes (Tunnels/SSH)` selected
5. Under `SSH`, select the desired server (probably wpilibpi) and open in current window or new window by clicking on icons next to server name
6. Enter password multiple times in the top menu bar
7. Click on the Explorer icon in far top-left corner in VSCode
8. Enter password (if needed)
9. Click Open Folder and hit enter to select the default directory (probably /home/pi)


### How to transfer initial repo from laptop to pi:
Assume local repo is in c:/dev/MonsterVision5
Assume /home/pi/MonsterVision5 exists and is empty
Assume wpilibpi.local is the server you want to push code to
1. Open Command Prompt
2. Type `scp -rp c:/dev/MonsterVision5/. pi@wpilibpi.local:/home/pi/MonsterVision5/` (If this doesn't work, use Admin Command Prompt)


### How to transfer updated code to computer and GitHub from Pi:
1. Ensure all saves have been committed on remote server
2. ssh into remote server
3. Zip up contents of MonsterVision file using `zip -r <name of zip file to be created> <directory you want to zip>`
4. Get laptop IP it from `ifconfig` or `ip a` on Linux laptop or `ipconfig` on Windows laptop
5. From the pi: `scp -p <name zip file> <host user name>@<laptop ip>:<directory where you want it on laptop>`
6. Unzip on laptop
7. Copy into MonsterVision5 directory connected to GitHub on laptop (overwriting in the process)
8. Commit and push to GitHub

### OLD STEPS (for transfer of updated code):
1. Ensure all saves have been committed on remote server
2. ssh into remote server
3. Zip up contents of MonsterVision file using `zip -r <name of zip file to be created> <directory you want to zip>`
4. Run `ipconfig` on the laptop computer and find the correct ip address (will make more specific later)"legacy command`scp -rp pi@wpilibpi.local:/home/pi/MonsterVision5/. c:/dev/MonsterVision5/`"
5. sudo scp -rp /home/pi/MonsterVision5/. <pc ip address>:c:/dev/MonsterVision5/6. Open VSCode7. Git pull and push as required
