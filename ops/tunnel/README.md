# hwiStock local dashboard tunnel

Use this from `hwibuntu` when hwiStock runs on `hwiServer` with local-only
binds.

```bash
/data/workspace/My/hwiStock/ops/tunnel/hwibuntu-dashboard-tunnel.sh
```

Equivalent command:

```bash
ssh -N -L 5000:127.0.0.1:5000 -L 5001:127.0.0.1:5001 hwiServer
```

Then open:

```text
http://127.0.0.1:5000/dashboard
```

The dashboard should remain bound to `127.0.0.1` on the server. Do not use
`0.0.0.0`, LAN IP, or public IP exposure for this access path.
