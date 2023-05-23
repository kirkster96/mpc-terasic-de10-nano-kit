# Develop and Deploy a Container Application for Image Capture and Upload on the DE10-Nano


This is part 6 of a tutorial series that covers the basics of managing the Terasic DE10-Nano with Azure IoT Edge. This design example will use container-based virtualization to enable image upload and telemetry with a USB Video Class (UVC) camera.

- [Develop and Deploy a Container Application for Image Capture and Upload on the DE10-Nano](#develop-and-deploy-a-container-application-for-image-capture-and-upload-on-the-de10-nano)
  - [About this tutorial](#about-this-tutorial)
    - [Audience](#audience)
    - [Objectives](#objectives)
  - [Prerequisites](#prerequisites)
  - [Software Installation](#software-installation)
    - [Python3.7](#python37)
    - [Azure IoT Explorer](#azure-iot-explorer)
    - [FFMPEG](#ffmpeg)
- [Reference Design Architecture](#reference-design-architecture)
  - [Block Diagram](#block-diagram)
  - [File Structures](#file-structures)
- [Step 1: Software Development Phase](#step-1-software-development-phase)
  - [Create a new Project in VSCode](#create-a-new-project-in-vscode)
  - [Copy the reference files to VSCode](#copy-the-reference-files-to-vscode)
  - [Run Unit Test with USB Webcam](#run-unit-test-with-usb-webcam)
    - [Connection of USB Webcam to DE10-Nano](#connection-of-usb-webcam-to-de10-nano)
    - [Running FFMPEG](#running-ffmpeg)
    - [Running FFMPEG-PYTHON](#running-ffmpeg-python)
  - [Setup the Azure Blob Storage Account](#setup-the-azure-blob-storage-account)
  - [Bind Azure Blob Storage Account into Azure IoT Hub](#bind-azure-blob-storage-account-into-azure-iot-hub)
  - [Azure D2C/C2D message validation](#azure-d2cc2d-message-validation)
  - [Run the Blob Upload Test to Azure](#run-the-blob-upload-test-to-azure)
- [Step 2: Azure Container Development](#step-2-azure-container-development)
- [Step 3: Azure IoT Edge Module Enablement Phase](#step-3-azure-iot-edge-module-enablement-phase)
  - [Push a Container Image to ACR](#push-a-container-image-to-acr)
  - [Azure IoT Module Setting](#azure-iot-module-setting)
  - [Run IoT Edge Service](#run-iot-edge-service)
- [Step 4: Azure IoT Central Application Development Phase](#step-4-azure-iot-central-application-development-phase)
  - [Create Azure IoT Central Application in Browser](#create-azure-iot-central-application-in-browser)
  - [Create the Device Template](#create-the-device-template)
    - [Copy or Customize the interfaces for your application](#copy-or-customize-the-interfaces-for-your-application)
    - [Customize Views](#customize-views)
  - [Deploy the Device from a template](#deploy-the-device-from-a-template)
  - [Security considerations:](#security-considerations)

## About this tutorial

This tutorial provides instructions on how to capture images with a UVC Camera and upload the images to the Azure Blob as telemetry data that can be monitored with an Azure IoT Central Application.
### Audience

Engineers that plan to develop Azure IoT Edge Modules on Intel® Cyclone® V SoC FPGA.
This tutorial covers the development and deployment flow for an Azure IoT Edge Module that demonstrates image capture from a USB Video Class device (e.g. most USB Webcams), 
and upload to Azure Cloud. The design example runs in software on the Integrated ARM* Cortex*-A9 MPCore* Processor in the Cyclone V SoC FPGA and does not use the FPGA logic fabric.

### Objectives

In this tutorial, you will learn how to:

- Develop Azure IoT Edge functions that run on Intel Cyclone V SoC FPGA
- Use the Azure Blob Storage API for image upload
- Integrate FFMPEG libraries for UVC Camera control and image capture
- Migrate Azure IoT Hub Modules to Azure IoT Central Application
- **WIP** Test in each step of development flow

## Prerequisites

In this tutorial you will need the following:

+ Download [Ubuntu 18.04 Image][LINK_Ubuntu_18_04] from Terasic or use the [Ubuntu 16.04 image][LINK_Ubuntu_16_04] and following [this link][LINK_Ubuntu_16_Upgrade] to upgrade Ubuntu 18.04.

+ Documentation
    + [Quick Start Resources][LINK_MS_Tutorial]  
    Valuable resources, videos, and source code, including this design example.
    
    + [Build an Azure* Container-based Application using Visual Studio Code][LINK_Build_an_Azure_Container-based_Application_using_Visual_Studio_Code]  
    This module explains how to set up Visual Studio Code for developing an IoT Edge container application and deploy a container application.
    
    + [Reconfigure an FPGA from the Azure* Cloud using a Container Application][LINK_Develop_and_Deploy_Container_Reconfiguring_FPGA_Circuit_of_DE10-Nano_from_Azure_Cloud]  
    This module demonstrates how to build a device tree overlay file and how to use it to re-configure the FPGA from a Container.

+ Example Code on GitHub

    + [Terasic-de10-nano-kit][LINK_DE10_DEVKIT_LINK] This GitHub repository has many tutorials, documentation and sample code, and this tutorial uses `azure-de10nano-document/module06-uvc-enablement-guide`

+ IP address on DE10-Nano  
    You will need to copy files to DE10-Nano during development, and we suggest using SSH. To check DE10-Nano's IP Address, open the DE10-Nano console and find the DE10-Nano IP address.
   
    Input:
    ```
    ip addr
    ```

    Output:
    ```
    2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
        link/ether f2:36:44:ac:08:7b brd ff:ff:ff:ff:ff:ff
        inet 192.168.100.145/24 brd 192.168.100.255 scope global dynamic eth0
        valid_lft 600184sec preferred_lft 600184sec
    ```
    In this case, the IP address is "192.168.100.145".

+ These are development tools required in this tutorial:

    + Software Development
        + VSCode is the recommended editor and installation is already covered in [Module 2][LINK_Build_an_Azure_Container-based_Application_using_Visual_Studio_Code].
        + Install [dmr-client][LINK_Dmr_Client_Installation] tool to check Plug and Play(PnP) statements.
        + Python 3.7 in DE10-Nano  
            In this application, the language in the host application is Python3 and in order to run it as native, Python3 
        + The Azure IoT Explorer is a graphical tool for interacting with and devices connected to your IoT hub and can be used to test PnP functions.

    + Azure Development
        + Azure Container Registry(ACR)
        + Azure IoT Edge
        + Azure IoT Central
        + Azure Blob Storage

## Software Installation
### Python3.7

Python 3.7 isn't installed in Ubuntu 18.04 by default.
Ubuntu 18.04 has Python3.8 repos that can be installed. Pyenv may be used as an alternative.

The pip package installer for python can be used.
```
sudo apt install -y python3.7 python3.7-dev
python3.7 get-pip.py
```

### Azure IoT Explorer

Follow [Azure IoT Explorer Installation Guide][LINK_Install_Azure_IoT_Explorer] to install the latest version. This tutorial uses 0.14.5 and the GUI/View may be updated in the future versions.

When opening Azure IoT Explorer, Click `Add connection` and paste IoT Hub connection string.
You can get this string from VSCode by clicking `...` in `AZURE IOT HUB` window and selecting `Copy IoT Hub Connection String`.

![](pics/copy-device-string-in-vscode.png)

When successful, you can see devices connected to the IoT Hub. Also, it is recommended to create a new device to be used for native tests.
```
Device ID: test
```

![](pics/new-device-create-in-iot-explorer.png)

### FFMPEG

FFMPEG isn't installed in Ubuntu 18.04 by default, please install FFMPEG with the commands below:
```
sudo apt update && sudo apt install -y ffmpeg
pip3.7 install ffmpeg-python
```
Once installation is complete, validate the installation by running:
```
ffmpeg -version
```
The output should be as following:
```
ffmpeg version 3.4.8-0ubuntu0.2 Copyright (c) 2000-2020 the FFmpeg developers
built with gcc 7 (Ubuntu/Linaro 7.5.0-3ubuntu1~18.04)
configuration: --prefix=/usr --extra-version=0ubuntu0.2 --toolchain=hardened --libdir=/usr/lib/arm-linux-gnueabihf --incdir=/usr/include/arm-linux-gnueabihf --enable-gpl --disable-stripping --enable-avresample --enable-avisynth --enable-gnutls --enable-ladspa --enad
libavutil      55. 78.100 / 55. 78.100
libavcodec     57.107.100 / 57.107.100
libavformat    57. 83.100 / 57. 83.100
libavdevice    57. 10.100 / 57. 10.100
libavfilter     6.107.100 /  6.107.100
libavresample   3.  7.  0 /  3.  7.  0
libswscale      4.  8.100 /  4.  8.100
libswresample   2.  9.100 /  2.  9.100
libpostproc    54.  7.100 / 54.  7.100

```

# Reference Design Architecture
This section describes the overall design architecture specification.

## Block Diagram

![](pics/architecture-overview.png)

The design has four functions, all implemented by software running on Host Processor System (HPS):
+ Connect to USB Camera through HPS USB Port
+ Capturing image by interval
+ Uploading image to Azure Blob Storage
+ Sending URI path as telemetry to Azure IoT Hub

Developers can communicate with devices in three ways:
+ Serial or Ethernet for debugging with DE10-Nano
+ IoT Hub for debugging Azure IoT Edge Modules

## File Structures
```
phase2-uvc
│
└── sw
    ├── PnP
    │   └── dtmi
    │       └── terasic
    │           └── fcc
    │               ├── de10_nano-2.json
    │               ├── de10_nano_sensor-1.json
    │               ├── de10_nano_threshold-1.json
    │               ├── rfs-1.json
    │               └── uvc-1.json
    └── software-code
        ├── Dockerfile.arm32v7 # Dockerfile to run the python application on ARM (DE10-Nano)
        ├── deployment.template.json # CreateOption and PnP Setting Example
        ├── main.py # Main body of the python application
        ├── package
        │   ├── library.py # Azure Blob Storage API
        │   └── utility.py # Utility Functions
        └── test
            ├── test_main.sh # Environment Script as Azure Device Client
            └── ffmpeg_test.py # FFMPEG-Python Test
```
# Step 1: Software Development Phase
## Create a new Project in VSCode

To make it easy to migrate to an Azure IoT Central Application, create another VSCode project following the same steps in [Module 2 Step 4][LINK_Build_an_Azure_Container-based_Application_using_Visual_Studio_Code], but this time we will choose a Python Module for the Solution Template.

Here's solution template that we will create:
```
Solution Name: UvcSolution
Module Template: Python Module
Module Name: UvcModule
```
When complete, you will see the file structure as below.

![](pics/default-python-project-structure-in-vscode.png)

`main.py` is a sample how to connect to Azure generated by VSCode, and may be helpful for reference.

## Copy the reference files to VSCode

Copy and replace the following folders and files from [Software Codes](#file-structures) to the project like below.
```
Folders:
- package
- test

Files:
- Dockerfile.arm32v7
- main.py
- requirement.txt
```

![](pics/modified-python-project-structure-in-vscode.png)


## Run Unit Test with USB Webcam

### Connection of USB Webcam to DE10-Nano
The image below shows the connection of a USB webcam to a USB hub. The USB hub is then connected to the micro-USB OTG port on DE10-Nano using a micro-USB to USB-A Female adapter.

![](pics/uvc-usb-hub-connectivity-de10-nano.png)

With the USB Webcam connected and DE10-Nano booted, the device will be detected and its driver will be loaded automatically.

To confirm the USB Webcam is detected and driver loaded correctly:
```
dmesg | grep uvcvideo
```
Output:
```
[   24.902371] uvcvideo: Found UVC 1.00 device V380 FHD Camera (0380:2006)
[   24.907560] uvcvideo 1-1.3:1.0: Entity type for entity Processing 2 was not initialized!
[   24.907575] uvcvideo 1-1.3:1.0: Entity type for entity Camera 1 was not initialized!
[   24.908608] usbcore: registered new interface driver uvcvideo
```

### Running FFMPEG
The installation of FFMPEG was done and validated earlier. After the USB Webcam has been attached, proceed to verify the end-to-end stack involving Linux's UVC Stack as well as Linux's Video4Linux2(V4L2) stack in processing image buffers.

Run the following command to trigger a single frame capture on the USB Webcam and save the file as `capture.jpg`
```
ffmpeg -f v4l2 -input_format mjpeg -i /dev/video0 -vframes 1 -y capture.jpg
```
Output from the command in terminal:
```
ffmpeg version 3.4.8-0ubuntu0.2 Copyright (c) 2000-2020 the FFmpeg developers
  built with gcc 7 (Ubuntu/Linaro 7.5.0-3ubuntu1~18.04)
  configuration: --prefix=/usr --extra-version=0ubuntu0.2 --toolchain=hardened --libdir=/usr/lib/arm-linux-gnueabihf --incdir=/usr/include/arm-linux-gnueabihf --enable-gpl --disable-stripping --enable-avresample --enable-avisynth --enable-gnutls --enable-ladspa --ed
  libavutil      55. 78.100 / 55. 78.100
  libavcodec     57.107.100 / 57.107.100
  libavformat    57. 83.100 / 57. 83.100
  libavdevice    57. 10.100 / 57. 10.100
  libavfilter     6.107.100 /  6.107.100
  libavresample   3.  7.  0 /  3.  7.  0
  libswscale      4.  8.100 /  4.  8.100
  libswresample   2.  9.100 /  2.  9.100
  libpostproc    54.  7.100 / 54.  7.100
Input #0, video4linux2,v4l2, from '/dev/video0':
  Duration: N/A, start: 500.675032, bitrate: N/A
    Stream #0:0: Video: mjpeg, yuvj420p(pc, bt470bg/unknown/unknown), 1920x1080 [SAR 16:9 DAR 256:81], 30 fps, 30 tbr, 1000k tbn, 1000k tbc
Stream mapping:
  Stream #0:0 -> #0:0 (mjpeg (native) -> mjpeg (native))
Press [q] to stop, [?] for help
Output #0, image2, to 'capture.jpg':
  Metadata:
    encoder         : Lavf57.83.100
    Stream #0:0: Video: mjpeg, yuvj420p(pc), 1920x1080 [SAR 16:9 DAR 256:81], q=2-31, 200 kb/s, 30 fps, 30 tbn, 30 tbc
    Metadata:
      encoder         : Lavc57.107.100 mjpeg
    Side data:
      cpb: bitrate max/min/avg: 0/0/200000 buffer size: 0 vbv_delay: -1
frame=    1 fps=0.0 q=4.5 Lsize=N/A time=00:00:00.03 bitrate=N/A speed=0.077x    
video:19kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: unknown
```
File generated:
```
root@de10nano:~/demo# ll
total 28
drwxr-xr-x  2 root root  4096 Oct  1 04:52 ./
drwx------ 18 root root  4096 Oct  1 04:52 ../
-rw-r--r--  1 root root 19004 Oct  1 04:52 capture.jpg
```
You can view the image either locally on DE10-Nano through the HDMI or copy the `capture.jpg` to your development machine to view.

You may use [Eye of GNOME][LINK_EOG] image viewer application from Ubuntu to view it, e.g.
```
eog capture.jpg
```
### Running FFMPEG-PYTHON

Under `test` directory, the `ffmpeg_test.py` is a Python script that will use the FFMPEG-PYTHON library to take a picture from the USB Webcam. It's essentially the same command as above, but uses the FFMPEG-PYTHON wrapper library.

Copy the `ffmpeg_test.py` to DE10-Nano:
```
scp test/ffmpeg_test.py root@192.168.8.102:/home/root/
```
Run the test in DE10-Nano console:
```
python3.7 ffmpeg_test.py
```
Output from running the script:
```
root@de10nano:~# python3.7 ffmpeg_test.py
ffmpeg version 3.4.8-0ubuntu0.2 Copyright (c) 2000-2020 the FFmpeg developers
  built with gcc 7 (Ubuntu/Linaro 7.5.0-3ubuntu1~18.04)
  configuration: --prefix=/usr --extra-version=0ubuntu0.2 --toolchain=hardened --libdir=/usr/lib/arm-linux-gnueabihf --incdir=/usr/include/arm-linux-gnueabihf --enable-gpl --disable-stripping --enable-avresample --enable-avisynth --enable-gnutls --enable-ladspa --ed
  libavutil      55. 78.100 / 55. 78.100
  libavcodec     57.107.100 / 57.107.100
  libavformat    57. 83.100 / 57. 83.100
  libavdevice    57. 10.100 / 57. 10.100
  libavfilter     6.107.100 /  6.107.100
  libavresample   3.  7.  0 /  3.  7.  0
  libswscale      4.  8.100 /  4.  8.100
  libswresample   2.  9.100 /  2.  9.100
  libpostproc    54.  7.100 / 54.  7.100
Input #0, video4linux2,v4l2, from '/dev/video0':
  Duration: N/A, start: 4669.359652, bitrate: N/A
    Stream #0:0: Video: mjpeg, yuvj420p(pc, bt470bg/unknown/unknown), 1920x1080 [SAR 16:9 DAR 256:81], 30 fps, 30 tbr, 1000k tbn, 1000k tbc
Stream mapping:
  Stream #0:0 -> #0:0 (mjpeg (native) -> mjpeg (native))
Press [q] to stop, [?] for help
Output #0, image2, to 'capture.jpg':
  Metadata:
    encoder         : Lavf57.83.100
    Stream #0:0: Video: mjpeg, yuvj420p(pc), 1920x1080 [SAR 16:9 DAR 256:81], q=2-31, 200 kb/s, 30 fps, 30 tbn, 30 tbc
    Metadata:
      encoder         : Lavc57.107.100 mjpeg
    Side data:
      cpb: bitrate max/min/avg: 0/0/200000 buffer size: 0 vbv_delay: -1
frame=    1 fps=0.0 q=4.4 Lsize=N/A time=00:00:00.03 bitrate=N/A speed=0.114x    
video:45kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: unknown

```
## Setup the Azure Blob Storage Account

Microsoft Azure has provided a detailed steps in registering for Azure Blob Storage account at [here][LINK_Azure_Blob_Account_Create].

The following shows the example of setting up the account for this tutorial:

1. Create a storage account with `de10nano` name
   
    ![](pics/storage-account-create-1.png)

2. Advanced settings, **remember to tick `Enable blob public access`**
   
    ![](pics/storage-account-public-access.png)

3. Networking settings
  
    ![](pics/storage-account-create-3.png)

4. Data protection settings
   
    ![](pics/storage-account-create-4.png)

5. Create storage account
   
   ![](pics/storage-account-create-5.png)

6. Once deployment is completed, click on *Go to resource* to create storage container.

    ![](pics/storage-account-create-6.png)

7. On the left bar, click on **Containers** and then '+ Container'to Create a blob storage container named `uvcimages`

    ![](pics/storage-account-create-container-1.png)

    Output:

    ![](pics/storage-account-create-container.png)

## Bind Azure Blob Storage Account into Azure IoT Hub

Microsoft Azure has provided a detailed steps on uploading images to Azure Blob Storage through Azure IoT Hub at [here][LINK_Azure_Blob_IoT_Hub_Binding]

1. Go to **Home** > [IoT Hub created earlier] > on the left pannel select **File Upload** > **Select Azure Storage Container**.
![](pics/iothub-file-upload.png)

2. Select the correct Azure storage account and container. Then **Save**.


3. This shows the `uvcimages` Azure Blob Storage container that we have created above has been successfully added into Azure IoT Hub `File upload`.
![](pics/iothub-file-upload-blob-setup.png)

## Azure D2C/C2D message validation
There are three message types to communicate with Azure IoT Hub.
+ Telemetry
+ Property
+ Command

Understand the differences between the message types [here][LINK_Azure_Telemetry_Property_Command].

For this tutorial, we are only sending Telemetry messages, which can be verified using the following:
+ `DE10-Nano Terminal`: to check messages in device side
+ `Azure IoT Explorer`: to check messages in cloud side 

1. DE10-Nano's Terminal

    This is the simplest way check messages sent to Azure. It is useful to debug transactions when not seeing them in other ways.
    <details><summary> Here's log in the terminal.</summary><div>

    ```
    root@de10nano:~/uvc-test# python3.7 main.py
    IoT Hub Client for Python
    DEBUG ::: Check de10nano
    Connecting using Connection String HostName=de10-nano.azure-devices.net;DeviceId=de10-nano;SharedAccessKey=JJxeyhNgWZuBCxcCf5CoSXW99IlRfQnczzac9TRidpk=
    ```

    </div></details>

2. Azure IoT Explorer 

    To check telemetry data quickly, go to `Telemetry` and click `Start` button on the top tab, and the button will be change `Stop`.  
    You can see the raw data regardless of supporting PnP in the application. You may experience the latency using Azure IoT Explorer.

    ![](pics/telemetry-az-explorer.png)

## Run the Blob Upload Test to Azure

Create a temporary directory in DE10-Nano to host the source codes:
```
mkdir Downloads/uvc-test
```
Copy the source files from Host Development Machine to DE10-Nano
```
scp -r package test/* requirements.txt main.py root@192.168.8.102:~/Downloads/uvc-test
```
Run pip install.
```
cd ~/Downloads/uvc-test
pip3.7 install -r requirements.txt
```

*Note: If you face any error during pip install, run the following command to install required packages.*
```
apt-get install build-essential libssl-dev libffi-dev python3.7-dev
```

You have to set variable in *test_main.sh* to create an Azure device client for a local test.

* Setting `IOTHUB_DEVICE_CONNECTION_STRING` environment:
    ```bash
    export IOTHUB_DEVICE_SECURITY_TYPE="connectionString"
    export IOTHUB_DEVICE_CONNECTION_STRING="HostName;DeviceId=;SharedAccessKey=" 
    ```
    You can get it from Azure IoT Explorer to select a device.

    ![](pics/copy-device-string-in-az-explorer.png)


Source `test_main.sh` and run `main.py`. After that, push `Q` in the terminal to finish the application.

```
source test_main.sh
python3.7 main.py
```

The log messages are below.
```
root@de10nano:~/Downloads/uvc-test# python3.7 main.py 
IoT Hub Client for Python
DEBUG ::: Check de10nano
Connecting using Connection String HostName=de10-nano.azure-devices.net;DeviceId=de10-nano;SharedAccessKey=JJxeyhNgWZuBCxcCf5CoSXW99IlRfQnczzac9TRidpk=
FFMPEG started with 2 FPS
Press Q to quit

Sending image from the provisioned device every 60 seconds
```
Once connection is established, the logs will continue with FFMPEG and Azure Blob connection and upload, e.g.

<details><summary> Sample log of image capture with upload and telemetry message</summary><div>

```
Uploading file: ./capture.jpg to Azure Storage as blob: de10-nano/capture_20211019-162304.jpg in container uvcimages

https://de10nano.blob.core.windows.net/uvcimages/de10-nano/capture_20211019-162304.jpg?sv=2018-03-28&sr=b&sig=DAoYjAWIYkrRu2mmRJt50MScrQZeSXEUqnkm3fyRy7Y%3D&se=2021-10-19T17%3A23%3A04Z&sp=rw
Upload succeeded. Result is: 

{'etag': '"0x8D9931CBB111335"', 'last_modified': datetime.datetime(2021, 10, 19, 16, 23, 5, tzinfo=datetime.timezone.utc), 'content_md5': bytearray(b'\xc1\xa3\xf0\xa60p\x81\x88\xbbM\x7f\x8f\xfc\xc2\xb0\x89'), 'client_request_id': 'd653a3c0-30f8-11ec-8de0-a0f3c12f2f}

Blob path: https://de10nano.blob.core.windows.net/uvcimages/de10-nano/capture_20211019-162304.jpg
Sent message: {"blob_uri": "https://de10nano.blob.core.windows.net/uvcimages/de10-nano/capture_20211019-162304.jpg"}
```
</div></details>

# Step 2: Azure Container Development

Now you will develop the following
+ `Dockerfile` to compile previous files to run the application
+ Docker option to run the built container

Perform the following in this step:
1. Customize Dockerfile and build a container in VSCode
2. Compress and copy it to DE10-Nano
3. Un-compress and launch it with options

This step and Step 4 are almost same as [Module 4 Section B][LINK_Develop_and_Deploy_Container_Reconfiguring_FPGA_Circuit_of_DE10-Nano_from_Azure_Cloud].

1. Customize Dockerfile and build a container in VSCode  
    You can customize Dockerfile if you have made changes to some files.
    To create containers, right Click on module.json and `Build IoT Edge Module Image`(Don't push the image), and choose `arm32v7` as the platform.

    *Note: You may change `image:tag:version` in module.json to manage container images*

2. Compress and copy it to DE10-Nano  
    Check the image from `docker images` from the integrated terminal in VSCode and copy the image to DE10-Nano.
    ```
    docker images #Check container images
    docker save <your ACR repository address>/uvcmodule:0.0.1-arm32v7 -o uvc-container.tar #Compress a container image
    scp uvc-container.tar root@<DE10-Nano IP address>:~/Downloads/ #Copy the compressed image
    ```

3. Un-compress and launch a container with options  
    Open a console on the DE10-Nano and load and test the container image.
    ```
    docker load -i ~/Downloads/uvc-container.tar #Uncompress the image
    docker run --privileged -d -v /sys/kernel/config:/sys/kernel/config -v /lib/firmware:/lib/firmware -e IOTHUB_DEVICE_SECURITY_TYPE="connectionString" -e IOTHUB_DEVICE_CONNECTION_STRING="HostName=;DeviceId=;SharedAccessKey=" -e IOTEDGE_GATEWAYHOSTNAME=de10nano <ACR repository address>/uvcmodule:0.0.1-arm32v7
    
    ```
    In the case of our application, the application will refer to several environment variables and you have to add them with `-e` option.
    In the next step, Azure IoT Edge will provide them and you don't take care of them.
    Once the container starts, you can get its hash. Also, you can check it from `docker ps`.

    *Note:This option is a standard option and if you want to use external devices such as camera or open ports, you can add options.*

    The result will be same as Step 4(`docker logs` as device side or Azure IoT Explorer as cloud side).
    This is a sample log.
    ```
    # docker run --privileged  -v /sys/kernel/config:/sys/kernel/config -v /lib/firmware:/lib/firmware -e IOTHUB_DEVICE_SECURITY_TYPE="connectionString" -e IOTHUB_DEVICE_CONNECTION_STRING="HostName=;DeviceId=;SharedAccessKey=" -e IOTEDGE_GATEWAYHOSTNAME=de10nano -d <ACR repository address>/uvcmodule:0.0.1-arm32v7
    4cc57e2cdd3e082dba02bf1cc79a4ce34e93b0879af08e15610f824e2ae4604d
    # docker ps
    CONTAINER ID        IMAGE                                              COMMAND             CREATED             STATUS              PORTS               NAMES
    4cc57e2cdd3e        <ACR repository address>/uvcmodule:0.0.1-arm32v7   "/app/run.sh"       13 seconds ago      Up 11 seconds                           kind_neumann
    # docker stop 4cc
    4cc
    root@de10nano:/overlay# docker logs 4cc
    IoT Hub Client for Python
    DEBUG ::: Check de10nano
    Connecting using Connection String HostName=de10-nano-iothub.azure-devices.net;DeviceId=de10nanoU18;SharedAccessKey=z63QR7E+nqhvZgcNg1ZTm7kXT8PxwcIwuUgrEQlvxeI=
    FFMPEG started with 2 FPS
    Press Q to quit

    Sending image from the provisioned device every 60 seconds

    Uploading file: ./capture.jpg to Azure Storage as blob: de10nanoU18/capture_20211104-020938.jpg in container uvcimages


    If completed, you can check the container options by using `docker inspect`.
    ```
    docker inspect <container ID> > docker-info.json
    ```
    This setting will be reused for Step5.

    When stopping the container, you can use `docker stop` command.
    ```
    docker stop <container ID>
    ```

![](pics/uploaded-blob-from-device.png)

# Step 3: Azure IoT Edge Module Enablement Phase

In this step, you will migrate container from earlier step to Azure IoT Module. These are the files we will work on
+ `deployment.template.json`
+ `deployment.arm32v7.json`

`development.arm32v7.json` isn't developed directly but auto-generated from the VSCode extension.

We will perform the following in this step:
1. Push a container image to ACR(Azure Container Registry)
2. Azure IoT Module Setting
3. Re-Launch IoT Edge Service


This step is almost same in [Module4][LINK_Develop_and_Deploy_Container_Reconfiguring_FPGA_Circuit_of_DE10-Nano_from_Azure_Cloud] with additional steps and information.

## Push a Container Image to ACR
Right Click on module.json in the project and `Build and Push IoT Edge Module Image` to re-create the image and push it to ACR.

## Azure IoT Module Setting
To enable IoT Edge, you have to update `deployment.template.json` in your VSCode project.
There are 2 locations should be updated.

+ Delete SimulatedTemperatureSensor Module
+ Add createOptions for RfsModule
+ Modify the `$edgeHub:properties.desired:routes`

The project uses the SimulatedTemperatureSensor sample and the module you specified as default.
In this case, SimulatedTemperatureSensor isn't needed and should be deleted.

*Note: Please refer to `sw/softwarecode/deployment.template.json`*

Also, update json to follow [this documentation][LINK_How_To_Convert_Options] aligning with `docker-info.json` from the previous step.

Here are frequently used options(Docker vs Azure IoT Edge Options).
```
Docker : Azure IoT Edge Option(deployment.template.json)
(--privileged) : (moduleContent.$edgeAgent.properties.desired.modules.<your module>.settings.createOptions.HostConfig.Privileged)
(-v) :(moduleContent.$edgeAgent.properties.desired.modules.<your module>.settings.createOptions.HostConfig.Binds:) and (moduleContent.$edgeAgent.properties.desired.modules.<your module>.settings.createOptions.HostConfig.Mounts)
```
These options are same that you used in Module4 and you can refer back to them.

Please ensure you copy the settings for `createOptions` and add the `env` node at `modules.UvcModule.env`

```JSON
Before:
  "createOptions": {}
After:
  "createOptions": {
    "HostConfig": {
      "Binds": [
        "/dev/video0:/dev/video0"
      ],
      "Privileged": true,
      "Devices": [
        {
          "PathOnHost": "/dev/video0",
          "PathInContainer": "/dev/video0",
          "CgroupPermissions": "rwm"
        }
      ]
    }
  }

  "env": {
    "IOTHUB_DEVICE_CONNECTION_STRING" : {
      "value": "HostName=;DeviceId=;SharedAccessKey="
    },
    "CAPTURE_INTERVAL" : {
      "value": 120
    }
  }
```

If you want customizing more, please follow [Azure IoT Edge Documentations][LINK_Azure_IoT_Edge_Docs].

Finally, our application sends messages to not Azure IoT Hub's output but Azure IoT Hub, and the default setting is opening only output.
So, it is needed to modify it.
```JSON
Before:
        "routes": {
          "UvcModuleToIoTHub": "FROM /messages/modules/UvcModule/outputs/* INTO $upstream",
          "sensorToUvcModule": "FROM /messages/modules/SimulatedTemperatureSensor/outputs/temperatureOutput INTO BrokeredEndpoint(\"/modules/UvcModule/inputs/input1\")"
        },
After:
        "routes": {
          "UvcModuleToIoTHub": "FROM /messages/modules/UvcModule/* INTO $upstream"
        },
```

## Run IoT Edge Service

Open a terminal in DE10-Nano to make sure to set the environment in `/etc/aziot/config.toml`.
*Note:If config.tmol is missing, copy config.toml.edge.template*

```toml
## Manual provisioning with connection string
#
[provisioning]
source = "manual"
connection_string = "HostName=example.azure-devices.net;DeviceId=my-device;SharedAccessKey=YXppb3QtaWRlbnRpdHktc2VydmljZXxhemlvdC1pZGU="
```

`connection_string` should be your IoT Edge connection string that you get from Azure Portal for the Edge device
Once done editing `/etc/aziot/config.toml`, please restart iotedge services.
```
iotedge config apply
iotedge system restart
```

Back to VSCode project, right-click in `deployment.template.json`, select `Generate IoT Edge Deployment Manifest`.
Then, right-click `config/deployment.arm32v7.json` to click `Create Deployment for Single Device`.

Wait for a few minutes for IoT Edge modules to wake up.
You can use iotedge commands on DE10-Nano to track the status or Module identities in Azure IoT Explorer.

![](pics/module-status-az-explorer.png)

```
iotedge list # Listing up Modules
iotedge logs <modulename> # Logging the specific modules
```

<details><summary>DE10-Nano Terminal log</summary><div>

```
root@de10nano:~# iotedge list
NAME             STATUS           DESCRIPTION      CONFIG
UvcModule        running          Up a minute      de10nanoflex.azurecr.io/uvcmodule:0.0.1-arm32v7
edgeAgent        running          Up 7 minutes     mcr.microsoft.com/azureiotedge-agent:1.2
edgeHub          running          Up 2 minutes     mcr.microsoft.com/azureiotedge-hub:1.2

# iotedge logs UvcModule
Running with 120s
Running with Real Image Capture
ffmpeg version 4.1.6-1~deb10u1 Copyright (c) 2000-2020 the FFmpeg developers
  built with gcc 8 (Debian 8.3.0-6)
  configuration: --prefix=/usr --extra-version='1~deb10u1' --toolchain=hardened --libdir=/usr/lib/arm-linux-gnueabihf --incdir=/usr/include/arm-linux-gnueabihf --arch=arm --enable-gpl --disable-stripping --enable-avresample --disable-filter=resample --enable-avisynth --enable-gnutls --enable-ladspa --enable-libaom --enable-libass --enable-libbluray --enable-libbs2b --enable-libcaca --enable-libcdio --enable-libcodec2 --enable-libflite --enable-libfontconfig --enable-libfreetype --enable-libfribidi --enable-libgme --enable-libgsm --enable-libjack --enable-libmp3lame --enable-libmysofa --enable-libopenjpeg --enable-libopenmpt --enable-libopus --enable-libpulse --enable-librsvg --enable-librubberband --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libspeex --enable-libssh --enable-libtheora --enable-libtwolame --enable-libvidstab --enable-libvorbis --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx265 --enable-libxml2 --enable-libxvid --enable-libzmq --enable-libzvbi --enable-lv2 --enable-omx --enable-openal --enable-opengl --enable-sdl2 --enable-libdc1394 --enable-libdrm --enable-libiec61883 --enable-chromaprint --enable-frei0r --enable-libx264 --enable-shared
  libavutil      56. 22.100 / 56. 22.100
  libavcodec     58. 35.100 / 58. 35.100
  libavformat    58. 20.100 / 58. 20.100
  libavdevice    58.  5.100 / 58.  5.100
  libavfilter     7. 40.101 /  7. 40.101
  libavresample   4.  0.  0 /  4.  0.  0
  libswscale      5.  3.100 /  5.  3.100
  libswresample   3.  3.100 /  3.  3.100
  libpostproc    55.  3.100 / 55.  3.100
[mjpeg @ 0x4b71f0] Found EOI before any SOF, ignoring
[mjpeg @ 0x4b71f0] No JPEG data found in image
Input #0, video4linux2,v4l2, from '/dev/video0':
  Duration: N/A, start: 15561.434740, bitrate: N/A
    Stream #0:0: Video: mjpeg, yuvj420p(pc, bt470bg/unknown/unknown), 1920x1080 [SAR 16:9 DAR 256:81], 30 fps, 30 tbr, 1000k tbn, 1000k tbc
Stream mapping:
  Stream #0:0 -> #0:0 (mjpeg (native) -> mjpeg (native))
Press [q] to stop, [?] for help
[mjpeg @ 0x4b9840] Found EOI before any SOF, ignoring
[mjpeg @ 0x4b9840] No JPEG data found in image
Error while decoding stream #0:0: Invalid data found when processing input
Output #0, image2, to './capture.jpg':
  Metadata:
    encoder         : Lavf58.20.100
    Stream #0:0: Video: mjpeg, yuvj420p(pc), 1920x1080 [SAR 16:9 DAR 256:81], q=2-31, 200 kb/s, 30 fps, 30 tbn, 30 tbc
    Metadata:
      encoder         : Lavc58.35.100 mjpeg
    Side data:
      cpb: bitrate max/min/avg: 0/0/200000 buffer size: 0 vbv_delay: -1
frame=    1 fps=0.0 q=3.3 Lsize=N/A time=00:00:05.26 bitrate=N/A speed=18.5x    
video:68kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: unknown
Image path: ./capture.jpg
Uploading ./capture.jpg...

Uploading file: ./capture.jpg to Azure Storage as blob: de10-nano/capture_20211001-073234.jpg in container uvcimages

https://de10nano.blob.core.windows.net/uvcimages/de10-nano/capture_20211001-073234.jpg?sv=2018-03-28&sr=b&sig=3jwGrqZAb1B5br1X25sFrvlpJwT%2BO3nvWKz%2FWAfJYTw%3D&se=2021-10-01T08%3A32%3A38Z&sp=rw
Upload succeeded. Result is: 

{'etag': '"0x8D984ADA60B030E"', 'last_modified': datetime.datetime(2021, 10, 1, 7, 32, 39, tzinfo=datetime.timezone.utc), 'content_md5': bytearray(b'0_\x0e\\\xc3\r7(\xd1\xadF\x8b\xd0\x9e\xc0\x87'), 'client_request_id': 'c14181e6-2289-11ec-81ca-0242ac120003', 'request_id': '92eac48f-901e-0137-3196-b6db22000000', 'version': '2020-06-12', 'version_id': None, 'date': datetime.datetime(2021, 10, 1, 7, 32, 39, tzinfo=datetime.timezone.utc), 'request_server_encrypted': True, 'encryption_key_sha256': None, 'encryption_scope': None}

Blob path: https://de10nano.blob.core.windows.net/uvcimages/de10-nano/capture_20211001-073234.jpg
Sent message: {"blob_uri": "https://de10nano.blob.core.windows.net/uvcimages/de10-nano/capture_20211001-073234.jpg"}

```
</div></details>

If your Module(UvcModule) is "Connected", you can check the data in Azure IoT Explorer similar in Step 1, but its output is wrapped under multiple levels below IoT Edge Module.
Please select IoT Hub,Devices, `Module identities`, your module name, and `IoT Plug and Play components`.

![](pics/module-pnp-az-explorer.png)

# Step 4: Azure IoT Central Application Development Phase
Once you have completed Step 3, you can create an Azure IoT Central Application that is easier to scale to multiple Azure IoT Edge devices. 
An Azure IoT Central Application is a SaaS(Software as a Service) application with the following features:

+ Easy to use it through the browser
+ Easy to register new devices and manage their status
+ Easy to keep data and create simple views for data visualizations

In this step, you will learn how to migrate the IoT Edge Module to IoT Central Application.
Please refer to Azure IoT Central Application documentation for the latest information.

You will perform the following in this step:
1. Create Azure IoT Central Application in Browser
2. Create the Device Template
    + Copy or Customize he interfaces in Device Template
    + Create Views for visualizations
3. Deploy Device from Template
    + Modify envorinment in DE10-Nano
    + Checking D2C/C2D data communication


## Create Azure IoT Central Application in Browser
Go to [Azure Portal][LINK_Azure_Portal], login, search `iot central` in the search box and select `IoT Central Applications`.

![](pics/search-in-azure-portal.png)

This is a sample setting. Be very aware of Pricing Plan because this application will send data every 60 seconds by default, and the number of transactions will affect your cost.

![](pics/iot-central-application.png)

Once you have successfully created the application, you will get notification e-mail, or you can go to the resource page to access application URL.

![](pics/url-in-iot-central-application.png)

## Create the Device Template
Access the URL and select `Device template`.

![](pics/device-template-in-iot-central.png)

Input `Device template name`.
Regarding Manifest, upload `<Your VScode Project root>/config/deployment.arm32v7.json` from Step5 and it will be validated.
Click `Next` and `Create` to finish the creation.

### Copy or Customize the interfaces for your application
In this view, you can define models, modules, and views.

![](pics/device-template-sample.png)

Click `Edit DTDL` and modify **"contents"** in PnP model.
If you don't modify PnP model from [public space][LINK_FCC_Public_Model], they are same in `de10_nano-2.json`.  
*Note: **Do not** modify your hash value in "@id" of the Module.*

<details><summary> Here's an example.</summary><div>

Before:
```JSON
{
    "@id": "dtmi:youk1s7uk:UvcModule;1",
    "@type": "Interface",
    "displayName": {
        "en": "Module UvcModule"
    },
    "@context": [
        "dtmi:iotcentral:context;2",
        "dtmi:dtdl:context;2"
    ]
}
```
After:
```JSON
{
    "@id": "dtmi:youk1s7uk:UvcModule;1",
    "@type": "Interface",
    "displayName": {
        "en": "Module UvcModule"
    },
    "@context": [
        "dtmi:iotcentral:context;2",
        "dtmi:dtdl:context;2"
    ],
    "contents": [
    {
        "@type": "Component",
        "name": "gSensor",
        "schema": "dtmi:Terasic:FCC:DE10_Nano_Sensor;1",
        "comment": "DE10Nano Basic Sensor",
        "displayName": {
          "en" : "DE10-Nano Onboard Sensor"
        },
        "description" : {
          "en" : "Sensors on DE10-Nano"
        }
    },
    {
        "@type": "Component",
        "name": "rfsSensors",
        "schema": "dtmi:Terasic:FCC:RFS;1",
        "comment": "Extended Card in FPGA Cloud Connectivity Kit",
        "displayName": {
          "en" : "RFS Daughter Card"
        },
        "description" : {
          "en" : "RFS Daughter Card"
        }
    },
    {
        "@type": "Component",
        "name": "thresholdProperty",
        "schema": "dtmi:Terasic:FCC:DE10_Nano_Threshold;1",
        "comment": "Sensor Thresholds (Only in Sensor Aggregation Design)",
        "displayName": {
          "en" : "Sensor Threshold Properties"
        },
        "description" : {
          "en" : "Sensor Threshold Properties for Sensor Aggregation Design"
        }
    },
    {
        "@type": "Component",
        "name": "uvcCameraFeed",
        "schema": "dtmi:Terasic:FCC:UVC;1",
        "comment": "UVC Camera Feed",
        "displayName": {
          "en" : "UVC Camera Feed"
        },
        "description" : {
          "en" : "UVC Camera Feed for Image Telemetry Design"
        }
    }
  ]
}
```
</div></details>

After completing, you can see three components(`DE10-Nano Onboard Sensor`/`RFS Daughter Card`/`Sensor Threshold Properties`) in your module(RfsModule).
In a similar way, copy the PnP statements for these three components and in this case you can copy all statements in files below:
```
DE10-Nano Onboard Sensor: de10_nano_sensor-1.json
RFS Daughter Card: rfs-1.json
Sensor Threshold Properties: de10_nano_threshold-1.json
UVC Camera Feed: uvc-1.json
```

Then, the PnP model migration is completed.

### Customize Views
You can also create Views. Move to `Views` and click `Visualizing the devices`.
The PnP model here, develops from the steps completed in Module 05, and so, this tutorial will only show visualizations specific to **UVC Camera Feed** model.
To display the camera feed, please add a `Last Known Value(LKV)` tile and modify the properties similar to below:

![](pics/lkv-blob-image-tile-settings.png)

For other sensors data, follow the steps in Module 05 to enable the additional tiles under `Views`, such as 6 tiles for each sensor module(MPU9250 sensor data is divided to each 3 axis).

When completing the edits, click `Publish`.

## Deploy the Device from a template
Move to `Devices` in left tab and click device template created in the previous step.
Select `New` and `Create`.

When created, select the device to move the detail and select `Connect` in the top.
You can check ID scope, Device ID, Primary/Secondary Key to connect a real device.
![](pics/register-device-in-iot-central.png)

Open a terminal in DE10-Nano and edit `/etc/aziot/config.toml`.
In Step 3, you used a connection string to enable DE10-Nano with IoT Edge but in this case, DPS will be used.
There two points to modify.

1. Comment out connection string to be disabled
    Please comment out to insert `#`.
    Comment Out:
    ```toml
    ## Manual provisioning with connection string
    #
    #[provisioning]
    #source = "manual"
    #connection_string = "HostName=;DeviceId=;SharedAccessKey="
    ="
    ```

2. Update values in DPS resources to be enabled
    ```toml
    ## DPS provisioning with symmetric key
    [provisioning]
    source = "dps"
    global_endpoint = "https://global.azure-devices-provisioning.net"
    id_scope = "<Filled in ID Scope>"
    #
    [provisioning.attestation]
    method = "symmetric_key"
    registration_id = "<Filled in Device ID>"
    #
    symmetric_key = { value = "<Filled in Primary Key>" }
    # inline key (base64), or...
    # symmetric_key = { uri = "file:///var/secrets/device-id.key" }
    # file URI, or...
    # symmetric_key = { uri = "pkcs11:slot-id=0;object=device%20id?pin-value=1234" }}
    # PKCS#11 URI
    ```

Apply a new configuration for iotedge service.
```
iotedge config apply
```

Wait for several minutes while checking packets in `Raw data` in the central application and Property or Telemetry packets will be coming.
When completed, you can do as below.
+ See data as graph in `Visualizations` view
+ Control thresholds in `Manage` view.

![](pics/visualizing-data-in-iot-central.png)

## Security considerations:
This design example and Intel FPGA IPs may not meet your security requirements. It depends on various external 3rd-party Open Source Components.
You will have to conduct a security review of your design including both hardware and software components to ensure it meets your security requirements.

Here's a list of general guidelines to consider when designing your next solution that combines both hardware and software elements:
1. Documentation for all IP cores used should be reviewed for any security concerns. 
2. Remove JTAG interfaces from final designs.
3. Control access to areas of memory to prevent unauthorized transactions or corruption by other IP in the design. 
4. Ensure correct configuration of the IP via the control interface and user input data is valid.
5. Protect the bitstreams for your design using the built-in security features from Intel Quartus Prime.
6. Enable password protection for the ARM processor.
7. Protect access to the design through hardware ports.
8. Restrict debugging access by tools such as Signal Tap.
9. Encrypt information on SD cards, FPGA bitstreams, and DDR memory devices.
10. Apply security features to any user data in storage, such as SD card.
11. Consider using encryption schemes enable secure data communication.
12. Consider the boot sequence and boot security aspects of the design.
13. Implement Intel FPGA bitstream encryption technology to further protect the FPGA design content of the products. For information on Intel FPGA bitstream encryption technology, refer to [Using the Design Security Features in Intel® FPGAs](https://www.intel.com/content/dam/www/programmable/us/en/pdfs/literature/an/an556.pdf).
14. Restrict access from unauthorized personnel to the system hosting the FPGA designs (physical as well as remote access). Authentication of accesses to the system (including Linux) shall be put in place.
15. Review the security aspects on the Azure IoT Edge including cloud communications, device provisioning etc... following guidelines from Microsoft Azure, refer to [Security standards for Azure IoT Edge](https://docs.microsoft.com/en-us/azure/iot-edge/security)


[LINK_Ubuntu_16_04]:http://download.terasic.com/downloads/cd-rom/de10-nano/DE10-Nano-Cloud-Native.zip
[LINK_Ubuntu_16_Upgrade]:https://github.com/daisukeiot/InnovateFPGA2021/blob/main/DE10-Nano-Setup.md
[LINK_Ubuntu_18_04]:http://download.terasic.com/downloads/cd-rom/de10-nano/AzureImage/DE10-Nano-Cloud-Native_18.04.zip
[LINK_MS_Tutorial]:https://github.com/daisukeiot/InnovateFPGA2021
[LINK_DE10_DEVKIT_LINK]:https://github.com/intel-iot-devkit/terasic-de10-nano-kit
[LINK_INTEL_REPO_in_GITHUB]:https://github.com/intel-iot-devkit/terasic-de10-nano-kit
[LINK_Terasic_RFS]: https://www.terasic.com.tw/cgi-bin/page/archive.pl?Language=English&CategoryNo=65&No=1025&PartNo=1
[LINK_Terasic_DE10_NANO_User_Manual]: https://www.terasic.com.tw/cgi-bin/page/archive_download.pl?Language=English&No=1046&FID=f1f656bb5f040121c36f2f93f6b107ff
[LINK_Terasic_getting_started_guide]: https://www.terasic.com.tw/attachment/archive/1046/Getting_Started_Guide.pdf
[LINK_Terasic_RFS_User_Manual]: https://www.terasic.com.tw/cgi-bin/page/archive_download.pl?Language=English&No=1025&FID=d1d10684aa5c6a87efc407b52d504104
[LINK_Terasic_resource]: de10-nano.terasic.com/cd
[LINK_VSCode_remote_SSH]: https://code.visualstudio.com/docs/remote/ssh
[LINK_VSCode_Remote_Extension]: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack
[LINK_IoT_SDK_compile]: https://github.com/Azure/azure-iot-sdk-c/blob/master/doc/devbox_setup.md#linux
[LINK_Azure_IoT_Edge_Sample_Module]: https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-sdks#azure-iot-device-sdks
[LINK_Azure_IoT_Device_SDK_antoher_language]: https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-sdks#azure-iot-device-sdks
[LINK_Azure_IoT_Device_SDK_web_app]: https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-live-data-visualization-in-web-apps
[LINK_Python_Source_Releases]: https://www.python.org/downloads/source/
[LINK_How_To_Convert_Options]: https://docs.microsoft.com/en-us/azure/iot-edge/how-to-use-create-options
[LINK_Azure_IoT_Edge_Docs]: https://docs.microsoft.com/en-us/azure/iot-edge
[LINK_Azure_Portal]: https://portal.azure.com
[LINK_Concept_Digital_Twins]: https://docs.microsoft.com/en-us/azure/iot-pnp/concepts-digital-twin
[LINK_Edit_Module_Twin_In_VSCode]: https://github.com/Microsoft/vscode-azure-iot-toolkit/wiki/Edit-Module-Twin
[LINK_IoT_Plug_and_Play_device_developer_guide]: https://docs.microsoft.com/en-us/azure/iot-pnp/concepts-developer-guide-device?pivots=programming-language-python
[LINK_Build_an_Azure_Container-based_Application_using_Visual_Studio_Code]: https://software.intel.com/content/www/us/en/develop/articles/build-an-azure-container-based-application-using-visual-studio.html
[LINK_Develop_and_Deploy_Container_Reconfiguring_FPGA_Circuit_of_DE10-Nano_from_Azure_Cloud]: https://software.intel.com/content/www/us/en/develop/articles/reconfigure-an-fpga-from-the-cloud-with-containers.html
[LINK_Altera_SoC_Workshop_Series]: https://rocketboards.org/foswiki/Documentation/AlteraSoCWorkshopSeries
[LINK_W3S_Developing_Drivers_for_Altera_SoC_Linux]: https://rocketboards.org/foswiki/Documentation/WS3DevelopingDriversForAlteraSoCLinux
[LINK_Install_Azure_IoT_Explorer]: https://docs.microsoft.com/en-us/azure/iot-fundamentals/howto-use-iot-explorer
[LINK_PnP_Modeling_Guide]:https://docs.microsoft.com/en-us/azure/iot-develop/concepts-modeling-guide
[LINK_PnP_Model_Repository]:https://github.com/Azure/iot-plugandplay-models
[LINK_Dmr_Client_Installation]: https://docs.microsoft.com/en-us/azure/iot-develop/concepts-model-repository#dmr-client-tools
[LINK_PnP_Overview]:https://docs.microsoft.com/en-us/azure/iot-develop/overview-iot-plug-and-play
[LINK_Azure_Telemetry_Property_Command]:https://docs.microsoft.com/en-us/azure/iot-central/core/concepts-telemetry-properties-commands
[LINK_FCC_Public_Model]:https://github.com/Azure/iot-plugandplay-models/tree/main/dtmi/terasic/fcc
[LINK_EOG]:https://help.gnome.org/users/eog/stable/commandline.html.en
[LINK_Azure_Blob_Account_Create]:https://docs.microsoft.com/en-us/azure/storage/common/storage-account-create?tabs=azure-portal
[LINK_Azure_Blob_IoT_Hub_Binding]:https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-python-python-file-upload
[LINK_Design_Security]:https://www.intel.com/content/dam/www/programmable/us/en/pdfs/literature/an/an556.pdf
[LINK_Azure_Security_Framework]:https://docs.microsoft.com/en-us/azure/iot-edge/security