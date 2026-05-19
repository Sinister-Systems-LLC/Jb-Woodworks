// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19

import axios, { AxiosInstance } from "axios";
import { logger } from "../lib/logger.js";

const BASE = process.env.KAMELEO_URL || "http://localhost:5050";
const KAMELEO_HOST = new URL(BASE).host;

// Desktop Chrome user-agent — forces Snap to serve the web UI, not mobile
const DESKTOP_UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36";

// --- Auto-tiling grid for Kameleo browser windows ---
// Instead of all windows stacking at 80,40, each new window gets a unique
// grid slot so they tile across the screen like a panel.
interface GridConfig {
  cols: number;
  rows: number;
  windowWidth: number;
  windowHeight: number;
  offsetX: number;
  offsetY: number;
}

// Grid for browser windows — must be large enough for Snapchat to render properly
// Minimum 1280x720 per window for Snap web to work correctly
// For 8 accounts on 1920x1080: 2x2 grid (960x540 each) — slightly below ideal but functional
// For larger screens (3840x2160): 4x2 grid (960x1080 each)
const GRID: GridConfig = {
  cols: 2,
  rows: 2,
  windowWidth: 960,
  windowHeight: 540,
  offsetX: 0,
  offsetY: 0,
};

// Map profileId -> assigned slot index
const slotAssignments = new Map<string, number>();
let nextSlot = 0;

function getSlotPosition(profileId: string): { x: number; y: number; width: number; height: number } {
  let slot = slotAssignments.get(profileId);
  if (slot === undefined) {
    slot = nextSlot++;
    slotAssignments.set(profileId, slot);
  }
  const col = slot % GRID.cols;
  const row = Math.floor(slot / GRID.cols) % GRID.rows;
  return {
    x: GRID.offsetX + col * GRID.windowWidth,
    y: GRID.offsetY + row * GRID.windowHeight,
    width: GRID.windowWidth,
    height: GRID.windowHeight,
  };
}

export function releaseSlot(profileId: string) {
  slotAssignments.delete(profileId);
}

export function resetSlots() {
  slotAssignments.clear();
  nextSlot = 0;
}

export interface ProxyCfg {
  host: string;
  port: number;
  username: string;
  password: string;
}

export interface CreateProfileOpts {
  fingerprintId: string;
  proxy: ProxyCfg;
  startPage: string;
  name?: string;
}

export interface KameleoFingerprint {
  id: string;
  device?: { type?: string };
  os?: { family?: string; version?: string };
  browser?: { product?: string; major?: number };
  screen?: { width?: number; height?: number };
}

class KameleoClient {
  private http: AxiosInstance;
  constructor() {
    this.http = axios.create({ baseURL: BASE, timeout: 30000 });
  }

  async pickFingerprint(): Promise<string> {
    // Use Windows + Chrome fingerprints — guarantees desktop user-agent and
    // Snap serves the full web UI, not the mobile "Download Snapchat" page.
    const { data } = await this.http.get<KameleoFingerprint[]>("/fingerprints", {
      params: { deviceType: "desktop", osFamily: "windows", browserProduct: "chrome" },
    });
    if (!Array.isArray(data) || data.length === 0) {
      // Fallback: try linux desktop
      const { data: fallback } = await this.http.get<KameleoFingerprint[]>("/fingerprints", {
        params: { deviceType: "desktop", osFamily: "linux", browserProduct: "chrome" },
      });
      if (!Array.isArray(fallback) || fallback.length === 0) {
        throw new Error("No desktop Chrome fingerprints available from Kameleo");
      }
      logger.warn("No Windows fingerprints, falling back to Linux");
      const pick = fallback[Math.floor(Math.random() * fallback.length)];
      return pick.id;
    }

    // Prefer fingerprints with screen width >= 1280
    const wide = data.filter((fp) => (fp.screen?.width ?? 1920) >= 1280);
    const pool = wide.length > 0 ? wide : data;
    const pick = pool[Math.floor(Math.random() * pool.length)];
    logger.info({
      fpId: pick.id.slice(0, 12),
      os: `${pick.os?.family} ${pick.os?.version}`,
      browser: `chrome ${pick.browser?.major}`,
      screen: `${pick.screen?.width}x${pick.screen?.height}`,
    }, "picked fingerprint");
    return pick.id;
  }

  async createProfile(opts: CreateProfileOpts): Promise<string> {
    const body = {
      fingerprintId: opts.fingerprintId,
      name: opts.name || `snap-${Date.now()}`,
      canvas: "intelligent",
      audio: "noise",
      webgl: "noise",
      webglMeta: { value: "automatic" },
      fonts: "automatic",
      // Force a wide desktop screen so Snap never thinks it's mobile
      screen: { value: "manual", extra: "1920x1080" },
      // Force desktop navigator so Snap never serves mobile "Download" page
      navigator: {
        value: "manual",
        extra: {
          userAgent: DESKTOP_UA,
          platform: "Win32",
        },
      },
      hardwareConcurrency: { value: "automatic" },
      deviceMemory: { value: "automatic" },
      timezone: { value: "automatic" },
      geolocation: { value: "automatic" },
      webRtc: { value: "automatic" },
      proxy: {
        value: "http",
        extra: {
          host: opts.proxy.host,
          port: opts.proxy.port,
          id: opts.proxy.username,
          secret: opts.proxy.password,
        },
      },
      startPage: opts.startPage,
      passwordManager: "disabled",
      storage: "cloud",
    };
    const { data } = await this.http.post("/profiles/new", body);
    return data.id;
  }

  async startProfile(profileId: string, position?: { x: number; y: number; width: number; height: number }): Promise<string> {
    const headless = /^(1|true|yes)$/i.test(process.env.KAMELEO_HEADLESS || "");

    // Auto-tile: if no explicit position, assign one from the grid
    const pos = position ?? getSlotPosition(profileId);

    let args: string[];
    if (headless) {
      args = ["headless", "disable-notifications", "force-dark-mode"];
    } else {
      args = [
        "disable-notifications",
        "force-dark-mode",
        // Mute all audio by default
        "mute-audio",
        // Reduce CPU usage when minimized
        "disable-backgrounding-occluded-windows",
        "disable-renderer-backgrounding",
        `--window-size=${pos.width},${pos.height}`,
        `--window-position=${pos.x},${pos.y}`,
      ];
    }

    logger.info({ profileId: profileId.slice(0, 8), pos: `${pos.x},${pos.y} ${pos.width}x${pos.height}` }, "starting profile");

    const doStart = () =>
      this.http.post(`/profiles/${profileId}/start`, { arguments: args });

    // Check if already running — if so, just return the CDP URL
    // (the window is already positioned from when it was first started)
    try {
      const { data: profile } = await this.http.get(`/profiles/${profileId}`);
      if (profile.lifetimeState === "running" || profile.lifetimeState === "Running") {
        logger.info({ profileId: profileId.slice(0, 8) }, "profile already running, reusing");
        return `ws://${KAMELEO_HOST}/playwright/${profileId}`;
      }
    } catch {}

    try {
      await doStart();
    } catch (e: any) {
      if (e.response?.status === 409) {
        logger.info({ profileId: profileId.slice(0, 8) }, "profile 409 (already running), reusing");
        return `ws://${KAMELEO_HOST}/playwright/${profileId}`;
      }
      const msg = e.response?.data?.detail || e.response?.data?.error || e.message;
      throw new Error(`Kameleo startProfile failed: ${JSON.stringify(msg)}`);
    }
    return `ws://${KAMELEO_HOST}/playwright/${profileId}`;
  }

  async profileExists(profileId: string): Promise<boolean> {
    try {
      await this.http.get(`/profiles/${profileId}`);
      return true;
    } catch (e: any) {
      if (e.response?.status === 404) return false;
      throw e;
    }
  }

  async stopProfile(profileId: string): Promise<void> {
    releaseSlot(profileId);
    await this.http.post(`/profiles/${profileId}/stop`, {}, {
      headers: { "Content-Type": "application/json" },
    }).catch((e) => {
      logger.warn({ err: e.message }, "stopProfile failed");
    });
  }

  async deleteProfile(profileId: string): Promise<void> {
    await this.http.delete(`/profiles/${profileId}`).catch(() => {});
  }

  async getRunningProfiles(): Promise<Array<{ id: string; name: string; status: string }>> {
    // Graceful degradation: if Kameleo isn't running, return empty list so
    // pages that just want to know "which profiles are up" can render with
    // zero rather than 500. Only swallow connection errors — other errors
    // (4xx/5xx from a real Kameleo) still surface.
    try {
      const { data } = await this.http.get("/profiles");
      return (data as any[])
        .filter((p) => p.status?.lifetimeState === "running")
        .map((p) => ({ id: p.id, name: p.name, status: p.status.lifetimeState }));
    } catch (e: any) {
      if (e.code === "ECONNREFUSED" || e.code === "ENOTFOUND" || e.code === "ETIMEDOUT" || !e.response) {
        logger.debug({ code: e.code }, "kameleo unavailable — returning empty profile list");
        return [];
      }
      throw e;
    }
  }

  /** Find an existing profile by name, returning the newest one. */
  async findProfileByName(name: string): Promise<string | null> {
    const { data } = await this.http.get("/profiles");
    const matches = (data as any[])
      .filter((p) => p.name === name)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
    if (matches.length === 0) return null;
    // Clean up older duplicates if any exist
    for (let i = 1; i < matches.length; i++) {
      logger.warn({ profileId: matches[i].id, name }, "deleting duplicate Kameleo profile");
      await this.deleteProfile(matches[i].id);
    }
    return matches[0].id;
  }

  /** Delete ALL snap-* profiles so they get recreated with fresh desktop fingerprints. */
  async purgeAllSnapProfiles(): Promise<number> {
    const { data } = await this.http.get("/profiles");
    let count = 0;
    for (const p of data as any[]) {
      if (p.name?.startsWith("snap-")) {
        if (p.status?.lifetimeState === "running") {
          await this.stopProfile(p.id);
        }
        await this.deleteProfile(p.id);
        count++;
      }
    }
    resetSlots();
    return count;
  }
}

export const kameleo = new KameleoClient();
