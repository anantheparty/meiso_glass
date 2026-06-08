# 功耗和延迟日志

V0 日志应当包含足够的时间元数据，用于开始测量：

- heartbeat 间隔抖动
- 命令往返时间
- 视频启动/停止耗时
- 设备健康快照

后续增加：

- 电源轨 monitor 样本
- SDC CPU/GPU/NPU 统计
- endpoint 温度和时钟状态
- camera frame 时间戳
- RTP 序号/丢包统计
- 每个有效遥测帧的能耗

## 最小指标

```text
endpoint_awake_time_s
endpoint_video_session_s
sdc_receive_fps
network_rtt_ms
command_ack_ms
packet_loss_percent
sdc_cpu_mem_temp
endpoint_cpu_mem_temp
rail_power_mw
```

## Demo 日志目录

每次 demo 应当生成一个日志目录，至少包含：

```text
probe_endpoint.log
probe_sdc.log
endpoint_agent.log
sdc_agent.log
video_sender_pipeline.txt
video_receiver_pipeline.txt
manual_notes.md
```

## 策略

延迟区间使用 `monotonic_ns`。只有做人类可读的跨日志事件关联时才使用 `realtime_ns`。
