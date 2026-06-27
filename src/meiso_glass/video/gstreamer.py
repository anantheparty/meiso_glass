from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass

SOFTWARE_H264_DECODER_PIPELINE = "avdec_h264 ! videoconvert ! autovideosink sync=false"


@dataclass
class GStreamerProcess:
    process: subprocess.Popen | None = None

    def running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self) -> None:
        if self.running() and self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    def start(self, command: str) -> None:
        self.stop()
        self.process = subprocess.Popen(command, shell=True)


def testsrc_h264_rtp_sender_command(
    host: str,
    port: int,
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
    encoder: str = "x264enc",
) -> str:
    """Return a portable test source H.264 RTP sender pipeline.

    Platform profiles can replace the encoder with an adapter-specific
    pipeline element without changing the command builder contract.
    """
    if encoder == "x264enc":
        enc = "x264enc tune=zerolatency speed-preset=ultrafast bitrate=4000 key-int-max=30"
    else:
        enc = shlex.quote(encoder)
    return (
        "gst-launch-1.0 -v videotestsrc is-live=true pattern=ball "
        f"! video/x-raw,width={width},height={height},framerate={fps}/1 "
        "! videoconvert "
        f"! {enc} "
        "! h264parse config-interval=1 "
        "! rtph264pay pt=96 "
        f"! udpsink host={shlex.quote(host)} port={port} sync=false"
    )


def h264_rtp_receiver_command(port: int = 5000, decoder_pipeline: str | None = None) -> str:
    dec = decoder_pipeline or SOFTWARE_H264_DECODER_PIPELINE
    caps = "application/x-rtp, media=(string)video, encoding-name=(string)H264, payload=(int)96"
    return f'gst-launch-1.0 -v udpsrc port={port} caps="{caps}" ! rtph264depay ! h264parse ! {dec}'
