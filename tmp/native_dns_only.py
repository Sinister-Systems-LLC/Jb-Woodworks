#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-24
"""native_dns_only.py — minimal Frida session that ONLY hooks getaddrinfo."""
import frida, sys, time, json

HOSTS = {
    "aws.api.snapchat.com": "54.224.131.131",
    "us-east1-aws.api.sc-gw.com": "54.224.131.131",
    "aws.api.sc-gw.com": "54.224.131.131",
    "gcp.api.snapchat.com": "35.190.43.134",
    "gcp.api.sc-gw.com": "35.190.43.134",
    "web.snapchat.com": "34.149.46.130",
    "app-analytics.snapchat.com": "35.244.195.33",
    "auth.snapchat.com": "54.224.131.131",
    "argos.snapchat.com": "54.224.131.131",
    "us-east1-aws.api.snapchat.com": "54.224.131.131",
}

SRC = r"""
var HOSTS = __HOSTS__;
var gai = Module.findExportByName("libc.so", "getaddrinfo");
console.log("[native_dns] gai=" + gai);

Interceptor.attach(gai, {
    onEnter: function(args) {
        this.host = null;
        try {
            if (args[0] && !args[0].isNull()) this.host = args[0].readCString();
        } catch (e) {}
        this.resPtr = args[3];
    },
    onLeave: function(retval) {
        try {
            var ret = retval.toInt32();
            if (this.host && HOSTS[this.host]) {
                send({t: "gai_seen", host: this.host, ret: ret});
                if (ret !== 0) {
                    var ipStr = HOSTS[this.host];
                    var parts = ipStr.split(".");
                    var b0 = parseInt(parts[0]) & 0xff;
                    var b1 = parseInt(parts[1]) & 0xff;
                    var b2 = parseInt(parts[2]) & 0xff;
                    var b3 = parseInt(parts[3]) & 0xff;

                    var sa = Memory.alloc(16);
                    sa.writeU8(2); sa.add(1).writeU8(0);
                    sa.add(2).writeU8(0); sa.add(3).writeU8(0);
                    sa.add(4).writeU8(b0);
                    sa.add(5).writeU8(b1);
                    sa.add(6).writeU8(b2);
                    sa.add(7).writeU8(b3);
                    for (var i = 8; i < 16; i++) sa.add(i).writeU8(0);

                    var ai = Memory.alloc(64);
                    for (var j = 0; j < 64; j++) ai.add(j).writeU8(0);
                    ai.add(4).writeU8(2);    // ai_family
                    ai.add(8).writeU8(1);    // ai_socktype
                    ai.add(12).writeU8(6);   // ai_protocol
                    ai.add(16).writeU8(16);  // ai_addrlen
                    ai.add(32).writePointer(sa);

                    this.resPtr.writePointer(ai);
                    retval.replace(0);
                    send({t: "gai_synth", host: this.host, ip: ipStr});
                }
            }
        } catch (e) {
            send({t: "gai_err", host: this.host || "?", err: String(e).substring(0,200)});
        }
    }
});
console.log("[native_dns] installed");
""".replace("__HOSTS__", json.dumps(HOSTS))

dev = frida.get_device_manager().add_remote_device("127.0.0.1:9999")
snap = [p for p in dev.enumerate_processes() if 'snap' in p.name.lower()]
if not snap:
    print("snap not found", flush=True)
    sys.exit(1)
pid = snap[0].pid
print(f"attaching pid={pid}", flush=True)
session = dev.attach(pid)
script = session.create_script(SRC)

def on_msg(m, d):
    if m.get('type') == 'send':
        print(f"FRIDA: {m.get('payload')}", flush=True)
    elif m.get('type') == 'log':
        print(f"LOG: {m.get('payload')}", flush=True)

script.on('message', on_msg)
script.load()
print("HELD 900s", flush=True)
time.sleep(900)
