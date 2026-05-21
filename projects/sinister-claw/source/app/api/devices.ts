// RKOJ Mobile :: api/devices.ts
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// ADB device + RKA / scrcpy helpers. Backed by the Forge bridge :5078
// running on the operator's PC. Endpoints under /api/devices.

// EventSource polyfill (idempotent -- same as forge.ts).
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore - no types ship with the polyfill
import RNEventSource from "react-native-event-source";
if (typeof (globalThis as { EventSource?: unknown }).EventSource === "undefined") {
  (globalThis as { EventSource: unknown }).EventSource = RNEventSource;
}

import { getBaseUrl, getAuthToken } from "./sanctum";

export interface AdbDevice {
  serial: string;
  state: "device" | "offline" | "unauthorized" | "bootloader" | "recovery" | string;
  transport: "usb" | "tcp" | string;
  model?: string;
  product?: string;
  device_codename?: string;
  android_version?: string;
  rka_state?: "armed" | "disarmed" | "killed" | string;
  heartbeat_age_s?: number;
  identity?: string;
}

async function devicesRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = await getBaseUrl();
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> ?? {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(`${baseUrl}/api/devices${path}`, { ...init, headers });
  if (!resp.ok) throw new Error(`Devices API ${path} ${resp.status}: ${await resp.text()}`);
  return (await resp.json()) as T;
}

export async function listDevices(): Promise<AdbDevice[]> {
  return devicesRequest<AdbDevice[]>("");
}

export async function getDeviceDetail(serial: string): Promise<AdbDevice> {
  return devicesRequest<AdbDevice>(`/${encodeURIComponent(serial)}`);
}

export interface AdbShellResult {
  serial: string;
  stdout: string;
  stderr: string;
  exit_code: number;
}

export async function adbShell(serial: string, cmd: string): Promise<AdbShellResult> {
  return devicesRequest<AdbShellResult>(
    `/${encodeURIComponent(serial)}/shell`,
    { method: "POST", body: JSON.stringify({ cmd }) },
  );
}

export async function openScrcpy(serial: string): Promise<{ ok: boolean; pid?: number }> {
  return devicesRequest<{ ok: boolean; pid?: number }>(
    `/${encodeURIComponent(serial)}/scrcpy`,
    { method: "POST" },
  );
}

export async function rkaArm(serial: string): Promise<{ ok: boolean; rka_state: string }> {
  return devicesRequest<{ ok: boolean; rka_state: string }>(
    `/${encodeURIComponent(serial)}/rka/arm`,
    { method: "POST" },
  );
}

export async function rkaKill(serial: string): Promise<{ ok: boolean; rka_state: string }> {
  return devicesRequest<{ ok: boolean; rka_state: string }>(
    `/${encodeURIComponent(serial)}/rka/kill`,
    { method: "POST" },
  );
}

/**
 * Tail the device's logcat. Returns an EventSource the caller must close().
 */
export async function openLogcatStream(
  serial: string,
  onLine: (line: string) => void,
): Promise<EventSource> {
  const baseUrl = await getBaseUrl();
  const token = await getAuthToken();
  const url = `${baseUrl}/api/devices/${encodeURIComponent(serial)}/logcat${token ? `?token=${encodeURIComponent(token)}` : ""}`;
  // @ts-expect-error EventSource polyfilled by react-native-event-source
  const es = new EventSource(url);
  es.addEventListener("line", (evt: MessageEvent) => onLine(evt.data));
  return es;
}
