# 首次运行

下面步骤使用通用 Linux 配置。网络和视频冒烟测试通过后，再切换到平台专用 profile。

## 1. 探测设备

```bash
mkdir -p logs
bash scripts/probe_system.sh | tee logs/probe_$(hostname)_$(date +%F_%H%M%S).log
```

## 2. 安装 SDK

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 3. 单机冒烟测试

终端 A：

```bash
meiso-sdc --config configs/examples/sdc.generic.yaml
```

终端 B：

```bash
meiso-endpoint --config configs/examples/endpoint.generic.yaml
```

终端 C：

```bash
meiso-send --host 127.0.0.1 --port 42001 ping
meiso-send --host 127.0.0.1 --port 42001 health
```

## 4. 双设备冒烟测试

给 endpoint 和 SDC 选择静态地址或 DHCP 地址。然后更新：

- endpoint 配置中的 `network.peer_host`，指向 SDC 地址
- endpoint 配置中的 `video.host`，指向 SDC 地址
- 向 endpoint 地址发送命令

示例：

```bash
meiso-send --host 192.168.10.2 --port 42001 ping
```

## 5. 视频冒烟测试

SDC 上的终端 A：

```bash
bash scripts/video_receiver.sh 5000
```

host 或 SDC 上的终端 B：

```bash
meiso-send --host 192.168.10.2 --port 42001 start_video --video-host 192.168.10.3 --video-port 5000
```

停止视频：

```bash
meiso-send --host 192.168.10.2 --port 42001 stop_video
```

`configs/platforms/endpoint.imx8mm.yaml` 和 `configs/platforms/sdc.orin.yaml` 只作为当前实验室上电调试 profile，不作为 SDK 默认配置。
