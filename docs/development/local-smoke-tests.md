# Local Smoke Tests

本地 smoke test 只验证 Host/Edge contract 和 UDP reference path，不代表最终传输方案。

终端 A：

```bash
meiso host --config configs/examples/host.generic.yaml
```

终端 B：

```bash
meiso edge --config configs/examples/edge.generic.yaml
```

终端 C：

```bash
meiso send \
  --host 127.0.0.1 \
  --port 42001 \
  --session-id session-dev \
  --feature camera \
  --mode stream \
  --request-id req-camera-001 \
  --lease-ms 5000
```

当前 smoke test 的目标是证明：

- `meiso` CLI 能启动。
- Edge 能发送 heartbeat。
- Host 能接收 Edge heartbeat。
- FeatureRequest 能返回 `accepted`、`degraded` 或 `rejected`。
- lease 到期后 Edge 会关闭高功耗 feature。
