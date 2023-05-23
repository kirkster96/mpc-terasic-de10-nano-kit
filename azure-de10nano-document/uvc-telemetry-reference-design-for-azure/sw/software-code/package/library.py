from __future__ import unicode_literals, print_function

import ffmpeg
import os
import signal
import sys
import time

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobClient

from package.utility import *

PATH_TO_FILE = r"./capture.jpg"

# Function to perform Azure Blob Storage connection and perform upload
async def store_blob(blob_info, file_name):
    try:
        sas_url = "https://{}/{}/{}{}".format(
            blob_info["hostName"],
            blob_info["containerName"],
            blob_info["blobName"],
            blob_info["sasToken"]
        )

        print("\nUploading file: {} to Azure Storage as blob: {} in container {}\n".format(file_name, blob_info["blobName"], blob_info["containerName"]))
        print( sas_url )
        # Upload the specified file
        with BlobClient.from_blob_url(sas_url) as blob_client:
            with open(file_name, "rb") as f:
                result = blob_client.upload_blob(f, overwrite=True)
                return (True, result)

    except FileNotFoundError as ex:
        # catch file not found and add an HTTP status code to return in notification to IoT Hub
        ex.status_code = 404
        return (False, ex)

    except AzureError as ex:
        # catch Azure errors that might result from the upload operation
        return (False, ex)


# Function to start FFMPEG in a streaming mode and save Webcam image with the
# provided frame per second
# Native ffmpeg command: 
# ffmpeg -f v4l2 -input_format mjpeg -i /dev/video0 -update 1 -r 1 -y capture.jpg  
def start_ffmpeg(fps = 1):

    try:
        process = (
            ffmpeg
            .input('/dev/video0', vcodec='mjpeg', format='v4l2', nostdin=None)
            .output(PATH_TO_FILE, r=int(fps), format='image2', update='1')
            .overwrite_output()
            .run_async(quiet=True)
        )

    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

    print(f"FFMPEG started with {fps} FPS")

    return process

# Function to stop FFMPEG since FFMPEG is started asynchronously with non-blocking
# STDIN
def stop_ffmpeg(process):

    # Suspend the FFMPEG
    os.kill(process.pid, signal.SIGKILL)

    print("FFMPEG stopped")

    return True

# Function to suspend FFMPEG to allow dumped frame to be uploaded
async def suspend_ffmpeg_and_upload(device_client, process):

    # Suspend the FFMPEG (Ctrl + Z)
    os.kill(process.pid, signal.SIGSTOP)

    # Get the storage info for the blob
    blob_name = os.path.basename(PATH_TO_FILE)
    timestr = time.strftime("%Y%m%d-%H%M%S")
    blob_name = "{0}_{2}.{1}".format(*blob_name.split('.'), timestr)
    storage_info = await device_client.get_storage_info_for_blob(blob_name)

    # Upload to blob
    success, result = await store_blob(storage_info, PATH_TO_FILE)

    # Continue the FFMPEG (fg)
    os.kill(process.pid, signal.SIGCONT)

    if success == True:
        print("Upload succeeded. Result is: \n")
        print(result)
        print()

        await device_client.notify_blob_upload_status(
            storage_info["correlationId"], True, 200, "OK: {}".format(PATH_TO_FILE)
        )

    else :
        # If the upload was not successful, the result is the exception object
        print("Upload failed. Exception is: \n")
        print(result)
        print()

        await device_client.notify_blob_upload_status(
            storage_info["correlationId"], False, result.status_code, str(result)
        )

        raise FileNotFoundError("Missing image file")

    return f'https://{storage_info["hostName"]}/{storage_info["containerName"]}/{storage_info["blobName"]}'

# Function to clean up the staging file
def remove_staging_file():
    os.remove(PATH_TO_FILE)
