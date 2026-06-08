# Config Profile Bible

本文件定义配置和 platform profile 的边界。

## 配置分类

`configs/examples/` 是平台中立示例，只能用于本地开发、mock、generic Linux smoke test。

`configs/platforms/` 是参考平台或具体硬件 bring-up profile，可以包含 board name、vendor pipeline、device path、driver hint。

未来可以增加：

```text
configs/reference/
configs/labs/
configs/hardware-gated/
```

## Generic Config 规则

generic config 不得出现：

- reference board name
- vendor-specific decoder alias
- fixed hardware path
- lab IP as universal default
- required physical sensor

generic config 可以出现：

- loopback IP
- development port
- software pipeline
- mock capability

## Platform Profile 规则

platform profile 是 adapter composition data，不是 core branch 的输入借口。代码不得写成：

```python
if cfg.platform == "some_board":
    ...
```

正确方向是 profile 选择 adapter 或 pipeline：

```yaml
video:
  decoder: customhwdec ! customvideosink sync=false
```

## Schema

配置 schema 至少校验：

- `device.role`
- `device.id`
- `device.platform`
- network port range
- required peer fields
- video fields
- logging directory
- unknown top-level section policy
