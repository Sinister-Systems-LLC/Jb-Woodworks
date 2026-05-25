// Author: RKOJ-ELENO :: 2026-05-24
//
// frida-probe.js -- Snap auto-update Phase 2 runtime class probe.
//
// Invocation (driven by run-probe.py, but works standalone for debugging):
//     frida -U -n com.snapchat.android -l frida-probe.js --quiet --runtime=v8 --no-pause
//
// What it does:
//   Walks Java.enumerateLoadedClasses() inside the running Snap process and
//   filters for three known obfuscated-class shape patterns whose names rotate
//   between Snap releases but whose method/field shapes stay stable:
//     1. kiib_zck  -- 2 methods g(byte[])->byte[] and h(byte[])->byte[]
//     2. m0l       -- 3 fields (int,int,byte[]) or (int,int,ByteString)
//     3. hlm       -- impl with finalize/apply returning signature-typed obj
//   For each pattern it ranks candidates by confidence (HIGH/MEDIUM/LOW).
//
// What it outputs:
//   A single JSON object wrapped in start/end markers on stdout so the Python
//   orchestrator can carve it out of mixed frida log output. Marker lines:
//     ===PROBE_OUTPUT_START===
//     {"schema_version":"sinister.frida-probe.v1", ...}
//     ===PROBE_OUTPUT_END===
//
// What the orchestrator does with it:
//   run-probe.py parses the JSON, picks the top candidate per pattern,
//   downgrades overall confidence if any pattern is ambiguous or missing,
//   then writes hooks/v<snap-version>-hooks.json with validation_status=pending
//   for Phase 3 smoke-test to validate.

'use strict';

function nowIso() {
    return new Date(Date.now()).toISOString();
}

function safeUse(fqName) {
    try {
        return Java.use(fqName);
    } catch (e) {
        console.error('[probe] skip class ' + fqName + ': ' + e.message);
        return null;
    }
}

function describeMethods(klass) {
    var out = [];
    try {
        var methods = klass.class.getDeclaredMethods();
        for (var i = 0; i < methods.length; i++) {
            var m = methods[i];
            var paramTypes = m.getParameterTypes();
            var paramNames = [];
            for (var p = 0; p < paramTypes.length; p++) {
                paramNames.push(paramTypes[p].getName());
            }
            out.push({
                name: m.getName(),
                params: paramNames,
                returns: m.getReturnType().getName()
            });
        }
    } catch (e) {
        console.error('[probe] describeMethods failed: ' + e.message);
    }
    return out;
}

function describeFields(klass) {
    var out = [];
    try {
        var fields = klass.class.getDeclaredFields();
        for (var i = 0; i < fields.length; i++) {
            var f = fields[i];
            out.push({ name: f.getName(), type: f.getType().getName() });
        }
    } catch (e) {
        console.error('[probe] describeFields failed: ' + e.message);
    }
    return out;
}

function matchKiibZck(methods) {
    var g = null, h = null;
    for (var i = 0; i < methods.length; i++) {
        var m = methods[i];
        if (m.params.length === 1 && m.params[0] === 'byte[]' && m.returns === 'byte[]') {
            if (m.name === 'g' || (!g && m.name.length <= 2)) { g = m.name; }
            else if (m.name === 'h' || (!h && m.name.length <= 2)) { h = m.name; }
        }
    }
    if (!g || !h) { return null; }
    var conf = 'LOW';
    if (methods.length === 2 && g === 'g' && h === 'h') { conf = 'HIGH'; }
    else if (g === 'g' && h === 'h') { conf = 'MEDIUM'; }
    return { method_g: g, method_h: h, confidence: conf };
}

function matchM0l(fields) {
    if (fields.length < 3) { return null; }
    var ints = 0, payload = null;
    for (var i = 0; i < fields.length; i++) {
        var t = fields[i].type;
        if (t === 'int') { ints++; }
        else if (t === 'byte[]' || t.indexOf('ByteString') >= 0) { payload = fields[i].name; }
    }
    if (ints < 2 || !payload) { return null; }
    var conf = (fields.length === 3 && ints === 2) ? 'HIGH' : 'MEDIUM';
    var nameHits = 0;
    for (var j = 0; j < fields.length; j++) {
        var n = fields[j].name;
        if (n === 'id' || n === 'status' || n === 'payload' || n.length === 1) { nameHits++; }
    }
    if (nameHits === 0) { conf = 'LOW'; }
    return { payload_field: payload, int_field_count: ints, confidence: conf };
}

function matchHlm(fqName, methods) {
    var hasFinalize = false, hasApply = false, sigReturn = null;
    for (var i = 0; i < methods.length; i++) {
        var m = methods[i];
        if (m.name === 'finalize') { hasFinalize = true; }
        if (m.name === 'apply') { hasApply = true; sigReturn = m.returns; }
    }
    if (!hasFinalize && !hasApply) { return null; }
    var pkgHit = fqName.indexOf('com.google.android.gms.common.api') >= 0;
    var conf = 'LOW';
    if (hasApply && pkgHit) { conf = 'HIGH'; }
    else if (hasApply || pkgHit) { conf = 'MEDIUM'; }
    return { has_finalize: hasFinalize, has_apply: hasApply, apply_returns: sigReturn, confidence: conf };
}

function runProbe() {
    var out = {
        schema_version: 'sinister.frida-probe.v1',
        snap_version_guess: null,
        probe_completed_at: null,
        candidates: { kiib_zck: [], m0l: [], hlm: [] },
        all_classes_count: 0
    };
    var classes = Java.enumerateLoadedClassesSync();
    out.all_classes_count = classes.length;
    for (var i = 0; i < classes.length; i++) {
        var fq = classes[i];
        var k = safeUse(fq);
        if (!k) { continue; }
        var methods = describeMethods(k);
        var fields = describeFields(k);
        var kiib = matchKiibZck(methods);
        if (kiib) {
            out.candidates.kiib_zck.push({
                pattern: 'kiib_zck', class: fq,
                method_g: kiib.method_g, method_h: kiib.method_h,
                confidence: kiib.confidence
            });
        }
        var m0l = matchM0l(fields);
        if (m0l) {
            out.candidates.m0l.push({
                pattern: 'm0l', class: fq,
                payload_field: m0l.payload_field,
                int_field_count: m0l.int_field_count,
                confidence: m0l.confidence
            });
        }
        var hlm = matchHlm(fq, methods);
        if (hlm) {
            out.candidates.hlm.push({
                pattern: 'hlm', class: fq,
                has_finalize: hlm.has_finalize, has_apply: hlm.has_apply,
                apply_returns: hlm.apply_returns, confidence: hlm.confidence
            });
        }
    }
    out.probe_completed_at = nowIso();
    console.log('===PROBE_OUTPUT_START===');
    console.log(JSON.stringify(out));
    console.log('===PROBE_OUTPUT_END===');
}

Java.perform(function () {
    try {
        runProbe();
    } catch (e) {
        console.error('[probe] fatal: ' + e.message + ' ' + (e.stack || ''));
    }
});
