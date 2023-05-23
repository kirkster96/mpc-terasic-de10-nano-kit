# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import asyncio
import json
import os
import socket
import socks
import sys

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device import Message, ProxyOptions

from package.utility import *
from package.library import *

#####################################################
# DEFAULT DEFINES
# For testing purpose, switch to create_from_edge_environment() eventually
EDGE_CONNECTION_STRING = os.environ.get("IOTHUB_DEVICE_CONNECTION_STRING")

# TODO: Temporary limiter for loop count, remove once code fully validated. This will consume the messages in Azure IoT Central & Azure IoT Hub
LOOP_COUNT = 5
STAGTING_FPS = 2

#DTDL V2
#https://github.com/Azure/opendigitaltwins-dtdl/blob/master/DTDL/v2/dtdlv2.md

# Created for iot-plugandplay-models/ (with new uvc-1.json)
model_id ="dtmi:Terasic:FCC:DE10_Nano;2"


#####################################################
# PROVISION DEVICE (Reference: azure-iot-sdk-python/azure-iot-device/samples/pnp/simple_thermostat.py)
async def provision_device(provisioning_host, id_scope, registration_id, symmetric_key, model_id):
    provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
        provisioning_host=provisioning_host,
        registration_id=registration_id,
        id_scope=id_scope,
        symmetric_key=symmetric_key,
        websockets=True
    )

    provisioning_device_client.provisioning_payload = {"modelId": model_id}
    return await provisioning_device_client.register()


#####################################################
# MAIN function
async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )

        hostname = os.getenv('IOTEDGE_GATEWAYHOSTNAME',socket.gethostname()) 

        print("IoT Hub Client for Python")
        logger.debug('DEBUG ::: Check {}'.format(hostname))

        # Default values for image update interval
        desired_interval = 60

        if "IOTEDGE_IOTHUBHOSTNAME" in os.environ:
            isEdge = True
        else:
            isEdge = False

        if isEdge == True:
            print("Azure IoT Edge Device with PnP")
            device_client = IoTHubModuleClient.create_from_edge_environment(product_info=model_id)
            await device_client.connect()

            print("Retrieve Device Twin Upon Connection")
            twin = await device_client.get_twin()
            # Try to get any desired capture_interval value
            try:
                desired_interval = twin['desired']['uvcCameraFeed']['capture_interval']
            except KeyError as e:
                desired_interval = 60
                print(f"Desired Capture Interval not provided, using default {desired_interval}s")

            logger.debug(f'Running with {desired_interval}s between Image Capture')

            # Report the capture_interval back to cloud
            prop_dict = {}
            inner_dict ={}
            inner_dict['capture_interval'] = {
                "ac": 200,
                "ad": "Successfully executed patch",
                "av": 1,
                "value": desired_interval,
            }
            prop_dict['uvcCameraFeed'] = inner_dict
            await device_client.patch_twin_reported_properties(prop_dict)

        else:
            switch = os.getenv("IOTHUB_DEVICE_SECURITY_TYPE")
            if switch == "DPS":
                provisioning_host = (
                    os.getenv("IOTHUB_DEVICE_DPS_ENDPOINT")
                    if os.getenv("IOTHUB_DEVICE_DPS_ENDPOINT")
                    else "global.azure-devices-provisioning.net"
                )
                id_scope = os.getenv("IOTHUB_DEVICE_DPS_ID_SCOPE")
                registration_id = os.getenv("IOTHUB_DEVICE_DPS_DEVICE_ID")
                symmetric_key = os.getenv("IOTHUB_DEVICE_DPS_DEVICE_KEY")

                registration_result = await provision_device(
                    provisioning_host, id_scope, registration_id, symmetric_key, model_id
                )

                if registration_result.status == "assigned":
                    print("Device was assigned")
                    print(registration_result.registration_state.assigned_hub)
                    print(registration_result.registration_state.device_id)

                    print(model_id)
                    device_client = IoTHubDeviceClient.create_from_symmetric_key(
                        symmetric_key=symmetric_key,
                        hostname=registration_result.registration_state.assigned_hub,
                        device_id=registration_result.registration_state.device_id,
                        websockets=True,
                        proxy_options=ProxyOptions(proxy_type=socks.HTTP, proxy_addr="proxy-png.intel.com", proxy_port=912),
                        product_info=model_id,
                    )
                else:
                    raise RuntimeError(
                        "Could not provision device. Aborting DPS device connection."
                    )
            elif switch == "connectionString":
                conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
                print("Connecting using Connection String " + conn_str)
                device_client = IoTHubDeviceClient.create_from_connection_string(
                    conn_str, product_info=model_id
                )
            else:
                raise RuntimeError(
                    "At least one choice needs to be made for complete functioning of this sample."
                )

            # Connect the client when isEdge = False
            await device_client.connect()

        # Start FFMPEG asynchronously with STAGTING_FPS
        process = start_ffmpeg(STAGTING_FPS)

        # Allow 5 seconds for FFMPEG initialization.
        time.sleep(5)

        if isEdge == True:
            # Connect the client to Azure IoT Hub to upload Blob Images
            blob_client = IoTHubDeviceClient.create_from_connection_string(EDGE_CONNECTION_STRING, product_info=model_id)
            await blob_client.connect()
        else:
            blob_client = device_client

        async def send_telemetry():
            print(f'Sending image from the provisioned device every {desired_interval} seconds')
            while True:
                try:
                    # Suspend FFMPEG, Upload the latest image, then FFMPEG continues
                    blob_uri = await suspend_ffmpeg_and_upload(blob_client, process)
                    logger.debug(f'Blob path: {blob_uri}')

                    # Send telemetry with readings as payload
                    payload = json.dumps({
                        'blob_uri': blob_uri
                    })
                    msg = Message(payload)
                    msg.content_encoding = "utf-8"
                    msg.content_type = "application/json"
                    msg.custom_properties["$.sub"] = "uvcCameraFeed"

                    await device_client.send_message(msg, )
                    logger.debug(f'Sent message: {msg}')
                except FileNotFoundError as ex:
                    logger.debug(f'Image upload failed, retrying next iteration after {desired_interval} seconds')
                finally:
                    await asyncio.sleep(desired_interval)

        send_telemetry_task = asyncio.create_task(send_telemetry())

        # define behavior for halting the application
        def stdin_listener():
            while True:
                try:
                    #selection = input("Press Q to quit\n")
                    selection = input()
                    if selection == "Q" or selection == "q":
                        print("Quitting...")
                        break
                except:
                    # Delay 2 secs for next iteration
                    time.sleep(2)

        # Run the stdin listener in the event loop
        loop = asyncio.get_running_loop()
        user_finished = loop.run_in_executor(None, stdin_listener)

        print("Press Q to quit\n")

        # Wait for user to indicate they are done listening for messages
        await user_finished

        # Cancel send_telemetry
        send_telemetry_task.cancel()

        # Stop FFMPEG
        stop_ffmpeg(process)

        # Remove staging file
        remove_staging_file()

        if isEdge == True:
            # Disconnect from blob upload
            await blob_client.disconnect()
        else:
            # Under non-Edge mode, blob_client is duplicate of device_client
            blob_client = None

        # Finally, disconnect
        await device_client.disconnect()

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise

if __name__ == "__main__":
    # If using Python 3.7 or above, you can use following code instead:
    asyncio.run(main())
