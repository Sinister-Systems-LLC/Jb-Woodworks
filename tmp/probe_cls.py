import frida, pathlib, re, sys

DEVICE = "127.0.0.1:9999"
RUNTIME_BUNDLE = pathlib.Path("/home/zonia/snap-frida-bridge/_agent.js")
RPC = r"""
  tryUse: function(names) {
    var Java = frida_java_bridge_default;
    var out = {};
    Java.perform(function () {
      for (var i = 0; i < names.length; i++) {
        var n = names[i];
        try {
          var Cls = Java.use(n);
          out[n] = {ok: true, methods: Cls.class.getDeclaredMethods().length};
        } catch (e) {
          out[n] = {ok: false, err: String(e).substring(0, 120)};
        }
      }
    });
    return JSON.stringify(out);
  }
"""

def parse_bundle(p):
    data = p.read_bytes()
    parts = data.split(b"\n", 3)
    m = re.match(rb"^(\d+)\s+/agent\.js$", parts[1])
    declared = int(m.group(1))
    source = parts[3]
    if len(source) == declared + 1 and source.endswith(b"\n"):
        source = source[:-1]
    header = parts[0] + b"\n" + parts[1] + b"\n" + parts[2] + b"\n"
    return header, source

def make_bundle(header, source):
    h = header.decode("utf-8")
    h = re.sub(r"^(\d+)\s+/agent\.js$", f"{len(source)} /agent.js", h, flags=re.M)
    return h.encode("utf-8") + source

def inject_rpc(rpc_src):
    header, source = parse_bundle(RUNTIME_BUNDLE)
    rpc_close = source.rfind(b"};")
    pre = source[:rpc_close].rstrip()
    if not pre.endswith(b","):
        pre += b","
    return make_bundle(header, pre + b"\n" + rpc_src.encode("utf-8") + b"\n" + source[rpc_close:])

dev = frida.get_device_manager().add_remote_device(DEVICE)
snap = [p for p in dev.enumerate_processes() if 'snap' in p.name.lower()][0]
session = dev.attach(snap.pid)
bundle = inject_rpc(RPC)
script = session.create_script(bundle.decode("utf-8"))
script.load()
names = ["C46170v4a", "defpackage.C46170v4a", "JBl", "defpackage.JBl", "IBl", "defpackage.IBl"]
print(script.exports_sync.try_use(names))
