import ntcore # type: ignore
import time

ntinst = ntcore.NetworkTableInstance.getDefault()

print("Setting up NetworkTables client for team {}".format(2635))
ntinst.startClient4("Eclipse")
ntinst.setServerTeam(2635)
ntinst.startDSClient()

sd = ntinst.getTable("MonsterVision")
fps = 1

while True:
    time.sleep(0.001)

    res = sd.putString("ObjectTracker-fps", "fps : {:.2f}".format(fps))
    ntinst.flush() # Puts all values onto table immediately

    fps+=1

