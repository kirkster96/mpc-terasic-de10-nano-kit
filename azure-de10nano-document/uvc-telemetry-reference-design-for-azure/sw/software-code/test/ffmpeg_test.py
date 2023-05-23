# Copyright (C) 2021 Intel Corporation 
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import ffmpeg
import sys

if __name__ == '__main__':

    try:
        process = (
            ffmpeg
            .input('/dev/video0', vcodec='mjpeg', format='v4l2')
            .output('capture.jpg', vframes='1')
            .overwrite_output()
            .run_async()
        )
        process.communicate()

    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
