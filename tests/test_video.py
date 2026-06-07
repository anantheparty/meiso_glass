from meiso_glass.video.gstreamer import h264_rtp_receiver_command
from meiso_glass.video.gstreamer import testsrc_h264_rtp_sender_command as sender_command


def test_sender_pipeline_uses_requested_host_port_and_encoder():
    cmd = sender_command(
        host="192.0.2.10",
        port=5001,
        width=640,
        height=480,
        fps=15,
        encoder="x264enc",
    )

    assert "videotestsrc" in cmd
    assert "width=640,height=480,framerate=15/1" in cmd
    assert "udpsink host=192.0.2.10 port=5001" in cmd


def test_receiver_pipeline_can_select_named_decoder_profile():
    cmd = h264_rtp_receiver_command(port=5002, decoder="nvidia")

    assert "udpsrc port=5002" in cmd
    assert "nvv4l2decoder" in cmd
