# 硬件 Adapter API

硬件专用代码必须放在 adapter 后面。SDK 核心可以依赖 adapter 接口，但不能依赖板卡专用设备节点、GStreamer 元素名、固件工具或无线电驱动。

参考接口位于 `meiso_glass.adapters.interfaces`。

## 适配器类型

- `CameraAdapter`
- `DisplayAdapter`
- `VideoEncoderAdapter`
- `RadioAdapter`
- `PowerAdapter`
- `M4Bridge`
- `FpgaBridge`
- `SensorAdapter`
- `StorageAdapter`
- `AudioAdapter`

## 摄像头示例

```python
from meiso_glass.adapters.interfaces import CameraAdapter, StreamConfig

def start_camera(camera: CameraAdapter) -> None:
    config = StreamConfig(width=1280, height=720, fps=30, format="RGB")
    status = camera.start_stream(config)
    assert status.available
```

## 模拟实现要求

每个依赖硬件的功能，在 demo 或测试使用之前，都必须有 mock 实现。当前 mock 参考实现位于 `meiso_glass.adapters.mock`。

## 移植规则

如果某个功能需要板卡专用路径，就新增 adapter 实现和平台 profile。不要在核心运行时里加入 `if imx8mm`、`if orin` 或固定 `/dev/...` 路径。
