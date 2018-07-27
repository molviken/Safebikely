#!/bin/bash

git clone --recursive https://github.com/Azure/azure-iot-sdk-python.git azure-iot-sdk-python
sudo apt-get update
sudo apt-get install -y cmake build-essential curl libcurl4-openssl-dev libssl-dev uuid-dev

PYTHON2_VER=`python --version 2>&1 | cut -d" " -f2`
PYTHON3_VER=`python3 --version 2>&1 | cut -d" " -f2`
PYTHON_INPUT=0

if [[ $PYTHON3_VER == 0 ]]
then
	sudo add-apt-repository ppa:jonathonf/python-3.6
	sudo apt-get update
	sudo apt-get install python3.6
fi

if [[ $PYTHON3_VER == 3.6* ]]
then
	PYTHON_INPUT=3.6
	echo "using python3 ver $PYTHON3_VER"
elif [[ $PYTHON3_VER == 3.5* ]]
then
	PYTHON_INPUT=3.5
	echo "using python3 ver  $PYTHON3_VER"
elif [[ $PYTHON2_VER == 2.7* ]]
then
	PYTHON_INPUT=2.7
	echo "using python ver $PYTHON2_VER"
else
	echo "didn't find valid python version, installing 2.7.13"
	wget --no-check-certificate https://www.python.org/ftp/python/2.7.13/Python-2.7.13.tgz
	tar -xzf Python-2.7.13.tgz
	cd Python-2.7.13
	./configure
	make
	sudo make install
	cd ..
fi
CMAKE_VER=`cmake --version | head -n1 | cut -d" " -f3`
GCC_VER=`gcc --version | head -n1 | cut -d" " -f4`
echo "$CMAKE_VER"
echo "$GCC_VER"


chmod u+x ./azure-iot-sdk-python/build_all/linux/setup.sh
./azure-iot-sdk-python/build_all/linux/setup.sh --python-version $PYTHON_INPUT
./azure-iot-sdk-python/build_all/linux/build.sh
chmod 777 ./single_lock/appTest.py
touch /var/log/safebikely.log
chown molviken /var/log/safebikely.log
mv IMS.service /etc/systemd/system/
systemctl enable IMS.service
systemctl start IMS.service

