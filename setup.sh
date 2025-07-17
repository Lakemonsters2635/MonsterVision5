#!/bin/bash
rm -r $HOME/examples
rm -r $HOME/zips
sed -i '5c \exec ./MonsterVision5/MonsterVision4.5.py' $HOME/runCamera
pip install ./deps/* --break-system-packages
cp ./mv.json /boot/mv.json
sed -i '16,$c \    "team": '"$1"',\n    "LaserDotProjectorCurrent": 765.0\n}' /boot/frc.json
sed -i '75c \set linenumbers' /etc/nanorc
sed -i '98c \set mouse' /etc/nanorc
sed -i '174c \set tabsize 4' /etc/nanorc
sed -i '177c \set tabstospaces' /etc/nanorc
cp ./models/best.json /boot/nn.json
chmod +x ./MonsterVision4.5.py
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666"' | sudo tee /etc/udev/rules.d/80-movidius.rules
udevadm control --reload-rules && udevadm trigger
rm $HOME/MonsterVision5.tar.gz