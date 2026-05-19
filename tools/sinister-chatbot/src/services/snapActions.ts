// Author: Sinister Sanctum master agent (Claude) :: 2026-05-19

import { Browser, BrowserContext, Page, chromium } from "playwright";
import { kameleo } from "./kameleo.js";
import { ensureProfile, loginAccount, handleSnapCrash, handleChromeCrash, isBlankPage } from "./snapLogin.js";
import { prisma } from "../lib/db.js";
import { accountLogger } from "../lib/logger.js";

function jitter(minMs: number, maxMs: number) {
  return minMs + Math.floor(Math.random() * (maxMs - minMs));
}

async function isSessionExpired(page: Page): Promise<boolean> {
  const url = page.url();
  // Redirected to login page
  if (/accounts\.snapchat\.com\/accounts\/login/i.test(url)) return true;
  // Redirected to root snapchat.com (not /web)
  if (/^https?:\/\/(www\.)?snapchat\.com\/?(\?|$)/i.test(url) && !/(\/web|web\.snapchat)/i.test(url)) return true;
  // Login form elements visible
  const loginForm = await page.$(
    'input[name="accountIdentifier"], input#username, text=/Log in to Snapchat/i'
  ).catch(() => null);
  return !!loginForm;
}

async function withSession<T>(
  accountId: string,
  fn: (page: Page, ctx: BrowserContext) => Promise<T>,
  opts: { requireLoggedIn?: boolean; keepOpen?: boolean } = {},
): Promise<T> {
  const acc = await prisma.account.findUniqueOrThrow({ where: { id: accountId } });
  const log = accountLogger(acc.username);
  if (opts.requireLoggedIn && acc.loginStatus !== "success") {
    const r = await loginAccount(accountId, true);
    if (!r.ok) throw new Error(`login-required: ${r.error}`);
  }
  let profileId = await ensureProfile(accountId);
  let cdp = await kameleo.startProfile(profileId);
  let browser: Browser | null = null;
  try {
    browser = await chromium.connectOverCDP(cdp);
    let ctx = browser.contexts()[0] || (await browser.newContext());
    let page = ctx.pages()[0] || (await ctx.newPage());
    // Force desktop viewport so Snap serves the web UI, not mobile/download page
    await page.setViewportSize({ width: 1920, height: 1080 });
    // Force dark mode
    await page.emulateMedia({ colorScheme: "dark" });
    // Force desktop UA at page level to prevent mobile redirects
    await page.setExtraHTTPHeaders({
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    });

    // --- Close 502 Bad Gateway tabs from old UA bug ---
    const allPagesInit = ctx.pages();
    for (const p of allPagesInit) {
      if (p === page) continue;
      const pUrl = p.url();
      const pTitle = await p.title().catch(() => '');
      if (/502 Bad Gateway/i.test(pTitle) || /chrome-error:\/\/|^http:\/\/(safari|applewebkit|gecko|nt|khtml|win64|x64|\(windows)/i.test(pUrl)) {
        await p.close().catch(() => {});
      }
    }

    // --- Session expiry + mobile page check ---
    const currentUrl = page.url();
    // Check for mobile/non-web pages — but DON'T clear cookies (that kills auth)
    const onMobile = /snapchat\.com\/(download|dl)/i.test(currentUrl) ||
      /click\.snapchat\.com/i.test(currentUrl) ||
      !!(await page.$('text=/Download Snapchat|Open Snapchat|Get Snapchat for any device/i').catch(() => null));
    if (onMobile || !/(web\.snapchat\.com|snapchat\.com\/web)/i.test(currentUrl)) {
      if (onMobile) log.warn("mobile page detected in withSession — navigating to web chat (preserving cookies)");
      await page.goto("https://web.snapchat.com/", {
        waitUntil: "domcontentloaded",
        timeout: 30000,
      }).catch(() => {});
      await page.waitForTimeout(3000);
      // If still not on web chat, try once more
      if (!/(web\.snapchat\.com|snapchat\.com\/web)/i.test(page.url())) {
        await page.goto("https://web.snapchat.com/", { waitUntil: "networkidle", timeout: 30000 }).catch(() => {});
        await page.waitForTimeout(3000);
      }
    }

    if (await isSessionExpired(page)) {
      log.warn("session expired — navigating to login page in same profile");
      // DON'T delete profile — preserve cloud storage. Just re-login in the same browser.
      const r = await loginAccount(accountId, true);
      if (!r.ok) throw new Error(`login-required: re-login failed: ${r.error}`);

      // Reconnect to the profile (it's the same one, just re-logged in)
      profileId = await ensureProfile(accountId);
      cdp = await kameleo.startProfile(profileId);
      if (browser) await browser.close().catch(() => {});
      browser = await chromium.connectOverCDP(cdp);
      ctx = browser.contexts()[0] || (await browser.newContext());
      page = ctx.pages()[0] || (await ctx.newPage());
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.emulateMedia({ colorScheme: "dark" });
    }
    // --- End session expiry check ---

    // --- Blank page detection ---
    if (await isBlankPage(page)) {
      log.warn("blank white page — re-logging in same profile");
      // DON'T delete — just re-login
      const r = await loginAccount(accountId, true);
      if (!r.ok) throw new Error(`login-required: re-login after blank page failed: ${r.error}`);
      profileId = await ensureProfile(accountId);
      cdp = await kameleo.startProfile(profileId);
      browser = await chromium.connectOverCDP(cdp);
      ctx = browser.contexts()[0] || (await browser.newContext());
      page = ctx.pages()[0] || (await ctx.newPage());
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.emulateMedia({ colorScheme: "dark" });
    }
    // --- End blank page detection ---

    // --- Chrome crash detection (Aw, Snap! / STATUS_ACCESS_VIOLATION) ---
    await handleChromeCrash(page, log);

    // --- Snap crash detection ---
    const crashResult = await handleSnapCrash(page, log);
    if (crashResult.persistent) {
      log.error("SNAP_CRASH_PERSISTENT — marking account and closing");
      await prisma.account.update({
        where: { id: accountId },
        data: { loginStatus: "crashed", lastError: "SNAP_CRASH_PERSISTENT" },
      });
      throw new Error("SNAP_CRASH_PERSISTENT");
    }
    // --- End crash detection ---

    return await fn(page, ctx);
  } finally {
    // Disconnect Playwright but leave the Kameleo browser window open
    // so the user can see the profiles. Only stop when explicitly not keeping open.
    if (opts.keepOpen) {
      if (browser) await browser.close().catch(() => {}); // disconnects CDP, doesn't close the browser
    } else {
      if (browser) await browser.close().catch(() => {});
      await kameleo.stopProfile(profileId);
    }
  }
}

// --- Add Friends panel helpers ---

async function dismissBanners(page: Page, log: ReturnType<typeof accountLogger>): Promise<void> {
  // Dismiss the "Click to install the Desktop App" banner — click the X button
  try {
    await page.evaluate(() => {
      // Find and click any close/dismiss buttons for banners
      const allEls = document.querySelectorAll('*');
      for (const el of allEls) {
        const text = (el.textContent || '').trim();
        const rect = el.getBoundingClientRect();
        // Look for small X buttons near the top of the page (banner dismiss)
        if ((text === '×' || text === 'X' || text === '✕' || text === 'x') && rect.y < 200 && rect.width < 40) {
          (el as HTMLElement).click();
          return;
        }
        // Look for the banner itself and its close button
        if (text.includes('Click to install') && rect.y < 200) {
          const closeBtn = el.querySelector('[aria-label*="close" i], [aria-label*="dismiss" i]');
          if (closeBtn) (closeBtn as HTMLElement).click();
        }
      }
    });
  } catch {}
  // Also dismiss any other overlays
  const dismissSelectors = [
    'button[aria-label="Close" i]',
    'button[aria-label="Dismiss" i]',
    'svg[aria-label="Close" i]',
  ];
  for (const sel of dismissSelectors) {
    const el = await page.$(sel).catch(() => null);
    if (el && await el.isVisible().catch(() => false)) {
      const box = await el.boundingBox().catch(() => null);
      // Only dismiss if in the banner area (y < 200)
      if (box && box.y < 200) {
        await el.click({ delay: jitter(40, 80) }).catch(() => {});
        log.info("dismissed banner/overlay");
        await page.waitForTimeout(jitter(500, 1000));
      }
    }
  }
  // Also try the X button on the install banner specifically
  const xButtons = await page.$$('button, [role="button"]').catch(() => []);
  for (const btn of xButtons) {
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) continue;
    const box = await btn.boundingBox().catch(() => null);
    if (!box) continue;
    // The X on the install banner is small (~20x20), in the upper area, right side of the banner
    if (box.width < 35 && box.height < 35 && box.y > 60 && box.y < 180 && box.x > 200) {
      const text = ((await btn.textContent()) || "").trim();
      if (!text || text === "×" || text === "X" || text === "✕") {
        await btn.click({ delay: jitter(40, 80) }).catch(() => {});
        log.info("dismissed install banner X button");
        await page.waitForTimeout(jitter(500, 1000));
        break;
      }
    }
  }
}

async function openAddFriendsPanel(page: Page, log: ReturnType<typeof accountLogger>): Promise<boolean> {
  // Dismiss any banners that might interfere
  await dismissBanners(page, log);

  // Check if panel already open
  const alreadyOpen = await page.$('text=/Add Friends/i').catch(() => null);
  if (alreadyOpen && await alreadyOpen.isVisible().catch(() => false)) {
    log.info("Add Friends panel already open");
    return true;
  }

  // Snap's top bar has icon buttons. The Add Friends button has an SVG with a person+ icon.
  // Layout: [Bitmoji] [Snap/Download] [AddFriends] [NewChat]
  // Strategy 1: Find buttons with SVGs in the top bar area, try the person+ icon.
  // Strategy 2: Positional — collect top-bar buttons, sort by x, pick 2nd-to-last.
  // The top bar area is y < 80 and within the sidebar width (x < 370).
  const topButtons: { el: any; x: number; y: number; w: number; h: number }[] = [];
  const allBtns = await page.$$('button, [role="button"]').catch(() => []);
  for (const btn of allBtns) {
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) continue;
    const box = await btn.boundingBox().catch(() => null);
    if (!box || box.y > 80 || box.height > 50 || box.x > 370) continue;
    topButtons.push({ el: btn, x: box.x, y: box.y, w: box.width, h: box.height });
  }

  topButtons.sort((a, b) => a.x - b.x);
  log.info({ count: topButtons.length, positions: topButtons.map((b) => `${Math.round(b.x)},${Math.round(b.y)}`) }, "top bar buttons");

  if (topButtons.length === 0) {
    log.warn("no top bar buttons found");
    return false;
  }

  // The Add Friends button is typically the 2nd-to-last in the top bar.
  // But also try ALL buttons (except the first which is avatar) to be robust.
  const tryOrder: number[] = [];
  if (topButtons.length >= 3) tryOrder.push(topButtons.length - 2); // 2nd to last (most likely)
  for (let i = topButtons.length - 1; i >= 1; i--) {
    if (!tryOrder.includes(i)) tryOrder.push(i);
  }

  for (const i of tryOrder) {
    const btn = topButtons[i];
    await btn.el.click({ delay: jitter(40, 110) });
    await page.waitForTimeout(jitter(1200, 2200));

    // Check if the Add Friends panel opened — REQUIRE the "Add Friends" heading text
    const panel = await page.$('text=/Add Friends/i').catch(() => null);
    const panelVisible = panel ? await panel.isVisible().catch(() => false) : false;

    if (panelVisible) {
      // Verify heading is on the RIGHT side (panel area, not sidebar)
      const panelBox = panel ? await panel.boundingBox().catch(() => null) : null;
      if (panelBox && panelBox.x > 250) {
        log.info({ x: Math.round(btn.x), y: Math.round(btn.y), headingX: Math.round(panelBox.x) }, "opened Add Friends panel (heading confirmed)");
        return true;
      }
    }

    // Also check for a search input that appeared on the right side (x > 350)
    let rightSearchFound = false;
    const inputs = await page.$$('input').catch(() => []);
    for (const inp of inputs) {
      const vis = await inp.isVisible().catch(() => false);
      if (!vis) continue;
      const ibox = await inp.boundingBox().catch(() => null);
      if (ibox && ibox.x > 350) { rightSearchFound = true; break; }
    }

    if (rightSearchFound) {
      log.info({ x: Math.round(btn.x), y: Math.round(btn.y) }, "opened Add Friends panel (right-side input found)");
      return true;
    }

    // Close whatever opened and try next
    await page.keyboard.press("Escape").catch(() => {});
    await page.waitForTimeout(jitter(300, 600));
  }

  log.warn("could not open Add Friends panel after trying all top bar buttons");
  return false;
}

async function findPanelSearchInput(page: Page, log: ReturnType<typeof accountLogger>): Promise<any | null> {
  // CRITICAL: Snap has TWO search inputs on screen when the Add Friends panel is open:
  //   1. LEFT sidebar search (for chat conversations) — typically x < 350
  //   2. RIGHT Add Friends panel search — positioned BELOW the "Add Friends" heading
  //
  // The key: find the "Add Friends" heading first, then find the input NEAR it.
  // This is much more reliable than using x-position which varies by window size.

  // Step 1: Find the "Add Friends" PANEL heading (not the sidebar button).
  // The panel heading is a large text element positioned in the RIGHT portion of the screen.
  // Use page.evaluate for speed instead of iterating all elements via Playwright.
  const panelHeadingBox = await page.evaluate(() => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode as Text;
      const text = (node.textContent || '').trim();
      if (text !== 'Add Friends') continue;
      const parent = node.parentElement;
      if (!parent) continue;
      const rect = parent.getBoundingClientRect();
      // The PANEL heading is on the right side (x > 300) and near the top (y < 200)
      // The sidebar icon button also says "Add Friends" but is at x < 300 and very small
      if (rect.x > 250 && rect.width > 50 && rect.height > 10 && rect.y < 200) {
        return { x: rect.x, y: rect.y, width: rect.width };
      }
    }
    return null;
  }).catch(() => null);

  if (!panelHeadingBox) {
    log.warn("Add Friends heading not found — panel may not be open");
    return null;
  }

  log.info({ headingX: Math.round(panelHeadingBox.x), headingY: Math.round(panelHeadingBox.y) }, "found Add Friends heading");

  // Step 2: Find the search input that is:
  //   - BELOW the heading (y > heading.y)
  //   - Within the same horizontal region (x overlaps with heading)
  //   - NOT the sidebar search (which is at a different x position)
  const headingCenterX = panelHeadingBox.x + panelHeadingBox.width / 2;
  const allInputs = await page.$$('input').catch(() => []);
  const candidates: { el: any; x: number; y: number; dist: number; placeholder: string }[] = [];

  for (const inp of allInputs) {
    const visible = await inp.isVisible().catch(() => false);
    if (!visible) continue;
    const box = await inp.boundingBox().catch(() => null);
    if (!box) continue;
    const placeholder = await inp.getAttribute('placeholder').catch(() => '') || '';

    // Input must be BELOW the heading
    if (box.y < panelHeadingBox.y) continue;

    // Input must be within 200px vertically of the heading (the search is right below)
    if (box.y - panelHeadingBox.y > 200) continue;

    // Calculate horizontal distance from panel center
    const inputCenterX = box.x + box.width / 2;
    const dist = Math.abs(inputCenterX - headingCenterX);

    candidates.push({ el: inp, x: box.x, y: box.y, dist, placeholder });
  }

  log.info({
    candidates: candidates.length,
    positions: candidates.map(c => `${Math.round(c.x)},${Math.round(c.y)} dist=${Math.round(c.dist)} "${c.placeholder}"`),
  }, "panel search candidates");

  if (candidates.length === 0) {
    log.warn("no input found below Add Friends heading");
    return null;
  }

  // Pick the candidate closest to the heading center (horizontally aligned)
  candidates.sort((a, b) => a.dist - b.dist);
  const best = candidates[0];
  log.info({ x: Math.round(best.x), y: Math.round(best.y), placeholder: best.placeholder }, "selected panel search input");
  return best.el;
}

async function clickAddForUsername(page: Page, targetUsername: string, log: ReturnType<typeof accountLogger>): Promise<boolean> {
  const targetLower = targetUsername.toLowerCase();

  // Snap's DOM concatenates text without spaces (e.g. "andrewandrewt407add").
  // To disambiguate similar usernames like andrewt407 vs andrewt4070, we check
  // that the username appears AND is not immediately followed by more alphanumerics.
  const exactRe = new RegExp(
    targetLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?![a-z0-9])',
    'i',
  );

  // Collect all visible "Add" buttons in the panel (x > 280 = right-side panel area)
  // Snap uses "+ Add" button with an SVG icon. The textContent can be "Add", "+ Add",
  // or just whitespace + "Add". We match any button containing "add" but NOT "added".
  const candidates: { btn: any; parentText: string; y: number }[] = [];
  const allButtons = await page.$$('button').catch(() => []);
  for (const btn of allButtons) {
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) continue;
    const text = ((await btn.textContent()) || '').trim().toLowerCase();
    // Match "add", "+ add", "Add" but NOT "added", "Added", "add friend"
    if (!/\badd\b/i.test(text) || /added|add friend/i.test(text)) continue;
    const box = await btn.boundingBox().catch(() => null);
    if (!box || box.x < 280) continue; // must be in the panel area

    const parentText = await btn.evaluate((el) => {
      let node: HTMLElement | null = el as HTMLElement;
      for (let i = 0; i < 8 && node; i++) {
        const t = node.textContent?.toLowerCase() || '';
        if (t.length > 15) return t;
        node = node.parentElement;
      }
      return node?.textContent?.toLowerCase() || '';
    });

    candidates.push({ btn, parentText, y: box.y });
  }

  log.info({
    target: targetUsername,
    candidateCount: candidates.length,
    candidateTexts: candidates.map(c => c.parentText.slice(0, 40)),
  }, "Add button candidates found");

  // First pass: find the row whose parent text contains the exact username
  for (const c of candidates) {
    if (exactRe.test(c.parentText)) {
      await c.btn.click({ delay: jitter(40, 110) });
      log.info({ target: targetUsername, parentText: c.parentText.slice(0, 60) }, "clicked Add for exact match");
      return true;
    }
  }

  // Second pass: simple includes (less strict, but still valid if only one match)
  for (const c of candidates) {
    if (c.parentText.includes(targetLower)) {
      await c.btn.click({ delay: jitter(40, 110) });
      log.info({ target: targetUsername, parentText: c.parentText.slice(0, 60) }, "clicked Add via includes match");
      return true;
    }
  }

  // Final fallback: click the first/topmost Add button (first search result)
  if (candidates.length > 0) {
    candidates.sort((a, b) => a.y - b.y);
    await candidates[0].btn.click({ delay: jitter(40, 110) });
    log.info({ target: targetUsername }, "clicked topmost Add button (fallback)");
    return true;
  }

  return false;
}

// --- End Add Friends panel helpers ---

export async function addFriendByUsername(accountId: string, targetUsername: string): Promise<{ ok: boolean; error?: string }> {
  const log = accountLogger((await prisma.account.findUniqueOrThrow({ where: { id: accountId } })).username);
  try {
    await withSession(accountId, async (page) => {
      log.info({ target: targetUsername }, "adding friend via Add Friends panel");

      // Step 1: Ensure on web.snapchat.com
      if (!/(web\.snapchat\.com|snapchat\.com\/web)/i.test(page.url())) {
        await page.goto("https://web.snapchat.com/", { waitUntil: "domcontentloaded", timeout: 30000 });
        await page.waitForTimeout(jitter(2000, 4000));
      }

      // Step 1.5: Clear sidebar search and close any open panels
      // This prevents typing in the wrong search box
      await page.keyboard.press("Escape").catch(() => {});
      await page.waitForTimeout(jitter(300, 500));
      // Clear the sidebar search if it has text in it
      const sidebarSearch = await page.$('input[placeholder*="Search" i]').catch(() => null);
      if (sidebarSearch) {
        const sidebarBox = await sidebarSearch.boundingBox().catch(() => null);
        if (sidebarBox && sidebarBox.x < 350) {
          const val = await sidebarSearch.inputValue().catch(() => '');
          if (val) {
            await sidebarSearch.click();
            await page.keyboard.press("Control+A");
            await page.keyboard.press("Backspace");
            await page.keyboard.press("Escape");
            await page.waitForTimeout(jitter(300, 500));
          }
        }
      }

      // Step 2: Open Add Friends panel
      const panelOpened = await openAddFriendsPanel(page, log);
      if (!panelOpened) throw new Error("Could not open Add Friends panel");

      await page.waitForTimeout(jitter(800, 1500));

      // Step 3: Type username in the Add Friends PANEL search (NOT the sidebar search).
      // Use page.evaluate to find and focus the correct input from inside the DOM.
      // The panel search is the input that appears AFTER the "Add Friends" heading text,
      // in the right portion of the page.
      const focusedPanel = await page.evaluate(() => {
        // Find the "Add Friends" heading in the right portion of the page
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let headingRect: DOMRect | null = null;
        while (walker.nextNode()) {
          const text = (walker.currentNode.textContent || '').trim();
          if (text === 'Add Friends') {
            const parent = walker.currentNode.parentElement;
            if (parent) {
              const rect = parent.getBoundingClientRect();
              // Panel heading is on the right side (x > 250) and reasonably sized
              if (rect.x > 250 && rect.width > 50) {
                headingRect = rect;
                break;
              }
            }
          }
        }
        if (!headingRect) return { ok: false, error: 'heading not found' };

        // Find the search input below the heading
        const inputs = document.querySelectorAll('input');
        let bestInput: HTMLInputElement | null = null;
        let bestDist = Infinity;

        for (const inp of inputs) {
          const rect = inp.getBoundingClientRect();
          if (rect.width < 20 || !inp.offsetParent) continue;
          // Must be BELOW the heading
          if (rect.y < headingRect.y) continue;
          // Must be within 150px vertically
          if (rect.y - headingRect.y > 150) continue;
          // Must be roughly horizontally aligned with heading (within 200px of center)
          const headingCenter = headingRect.x + headingRect.width / 2;
          const inputCenter = rect.x + rect.width / 2;
          const dist = Math.abs(inputCenter - headingCenter);
          if (dist < bestDist) {
            bestDist = dist;
            bestInput = inp;
          }
        }

        if (!bestInput) return { ok: false, error: 'input not found below heading' };

        // Focus and click it
        bestInput.focus();
        bestInput.click();
        bestInput.value = '';
        const rect = bestInput.getBoundingClientRect();
        return { ok: true, x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width) };
      });

      if (!focusedPanel.ok) {
        log.error({ error: (focusedPanel as any).error }, "failed to find/focus panel search input");
        throw new Error("Add Friends panel search input not found: " + (focusedPanel as any).error);
      }

      log.info({ x: focusedPanel.x, y: focusedPanel.y, w: focusedPanel.w }, "focused panel search input via DOM");

      // Now type the username — the input is already focused via DOM
      await page.waitForTimeout(jitter(200, 400));
      for (const ch of targetUsername) {
        await page.keyboard.type(ch, { delay: jitter(70, 180) });
      }
      await page.waitForTimeout(jitter(200, 400));

      // Verify we typed in the right place
      const verifyInput = await page.evaluate((username: string) => {
        const inputs = document.querySelectorAll('input');
        for (const inp of inputs) {
          if (inp.value.toLowerCase().includes(username.substring(0, 5).toLowerCase())) {
            const rect = inp.getBoundingClientRect();
            return { x: Math.round(rect.x), inPanel: rect.x > 250 };
          }
        }
        return { x: 0, inPanel: false };
      }, targetUsername);

      if (!verifyInput.inPanel) {
        log.error({ x: verifyInput.x }, "TYPED IN WRONG INPUT — clearing and aborting");
        await page.keyboard.press("Control+A");
        await page.keyboard.press("Backspace");
        await page.keyboard.press("Escape");
        throw new Error("Typed in sidebar search instead of Add Friends panel");
      }

      log.info("typed username in panel search");
      await page.waitForTimeout(jitter(2500, 4000));

      // Step 3.5: Check for "No Results" or "Limit reached"
      const noResults = await page.$('text=/No Results/i').catch(() => null);
      const noResultsVisible = noResults ? await noResults.isVisible().catch(() => false) : false;
      if (noResultsVisible) {
        log.warn({ target: targetUsername }, "username does not exist on Snapchat (No Results)");
        await page.keyboard.press("Escape").catch(() => {});
        throw new Error(`USERNAME_NOT_FOUND: ${targetUsername}`);
      }

      // Check for Snapchat's daily add limit
      const limitReached = await page.$('text=/Limit reached|Try again tomorrow/i').catch(() => null);
      const limitVisible = limitReached ? await limitReached.isVisible().catch(() => false) : false;
      if (limitVisible) {
        log.warn({ target: targetUsername }, "SNAPCHAT DAILY ADD LIMIT REACHED — stopping adds for this account");
        await page.keyboard.press("Escape").catch(() => {});
        // Mark account as having hit the limit today
        await prisma.account.update({
          where: { id: accountId },
          data: { lastError: "ADD_LIMIT_REACHED" },
        });
        throw new Error(`ADD_LIMIT_REACHED: Snapchat daily limit hit`);
      }

      // Step 4: Find exact match and click + Add
      const added = await clickAddForUsername(page, targetUsername, log);
      if (!added) {
        // Check if already added/pending/friends
        const addedBtn = await page.$('button:has-text("Added"), button:has-text("Pending"), button:has-text("Requested")').catch(() => null);
        const addedVisible = addedBtn ? await addedBtn.isVisible().catch(() => false) : false;
        // Check for "My Friends" section showing the user
        const myFriends = await page.$('text=/My Friends/i').catch(() => null);
        const myFriendsVisible = myFriends ? await myFriends.isVisible().catch(() => false) : false;

        if (addedVisible) {
          log.info({ target: targetUsername }, "already added/pending — button visible");
        } else if (myFriendsVisible) {
          log.info({ target: targetUsername }, "already in My Friends");
        } else {
          // No Add button AND no indication of already added — this is a real failure
          log.warn({ target: targetUsername }, "Add button NOT found and user not in friends — add failed");
          throw new Error("Add button not found for " + targetUsername);
        }
      }

      await page.waitForTimeout(jitter(1500, 3000));

      // Step 5: Close panel
      await page.keyboard.press("Escape").catch(() => {});
      await page.waitForTimeout(jitter(500, 1000));
    }, { requireLoggedIn: true, keepOpen: true });

    await prisma.friendAdd.create({
      data: { accountId, targetUser: targetUsername, status: "sent" },
    });
    log.info({ target: targetUsername }, "friend added via panel");
    return { ok: true };
  } catch (e: any) {
    log.error({ target: targetUsername, err: e.message }, "friend add failed");
    // Don't create a friendAdd record for non-existent usernames — they should be
    // removed from the engaged list so we don't waste slots on fake usernames.
    if (/USERNAME_NOT_FOUND/.test(e.message)) {
      await prisma.engagedUsername.delete({ where: { username: targetUsername } }).catch(() => {});
      return { ok: false, error: e.message };
    }
    await prisma.friendAdd.create({
      data: { accountId, targetUser: targetUsername, status: `error:${e.message.slice(0, 80)}` },
    });
    return { ok: false, error: e.message };
  }
}

export interface AcceptOpts {
  declineQuickAdds?: boolean;
  onlyByUsername?: boolean;
}

export async function acceptPendingAdds(
  accountId: string,
  maxPerRun = 20,
  opts: AcceptOpts = {},
): Promise<{ accepted: number; skipped: number }> {
  const log = accountLogger((await prisma.account.findUniqueOrThrow({ where: { id: accountId } })).username);
  let accepted = 0;
  let skipped = 0;
  try {
    await withSession(accountId, async (page) => {
      await page.goto("https://web.snapchat.com/", { waitUntil: "domcontentloaded", timeout: 45000 });
      await page.waitForTimeout(jitter(2000, 3500));

      const friendsTab = await page.$('[aria-label*="Friends" i], a[href*="/friends"], button:has-text("Friends")');
      if (friendsTab) await friendsTab.click();
      await page.waitForTimeout(jitter(1500, 2500));

      // Iterate each pending request row and inspect the "added by" hint
      // (Snap shows "Added by username" / "Quick Add" / "Added from Search").
      const rows = await page.$$('[data-testid*="add-friend" i], [aria-label*="friend request" i], li:has(button:has-text("Accept"))');
      for (const row of rows) {
        if (accepted >= maxPerRun) break;
        const label = ((await row.textContent()) || "").toLowerCase();
        const isQuickAdd = /quick\s*add/.test(label);
        const isByUsername = /added\s+by\s+username/.test(label);

        if (opts.declineQuickAdds && isQuickAdd) {
          const dismiss = await row.$('button:has-text("Remove"), button:has-text("Dismiss"), button[aria-label*="remove" i]');
          if (dismiss) await dismiss.click().catch(() => {});
          skipped++;
          await page.waitForTimeout(jitter(800, 1600));
          continue;
        }
        if (opts.onlyByUsername && !isByUsername) {
          skipped++;
          continue;
        }
        const accept = await row.$('button:has-text("Accept")');
        if (!accept) continue;
        await accept.click();
        accepted++;
        await page.waitForTimeout(jitter(2000, 5000));
      }
    }, { requireLoggedIn: true, keepOpen: true });
    log.info({ accepted, skipped, ...opts }, "accept pending adds");
  } catch (e: any) {
    log.error({ err: e.message }, "accept failed");
  }
  return { accepted, skipped };
}

export interface UnreadThread {
  fanUsername: string;
  displayName: string; // The display name shown in sidebar (for searching)
  lastMessage: string;
}

export async function pollUnreadThreads(accountId: string): Promise<UnreadThread[]> {
  const log = accountLogger((await prisma.account.findUniqueOrThrow({ where: { id: accountId } })).username);
  try {
    return await withSession(accountId, async (page) => {
      const url = page.url();
      if (!/(web\.snapchat\.com|snapchat\.com\/web)/i.test(url)) {
        await page.goto("https://web.snapchat.com/", { waitUntil: "domcontentloaded", timeout: 45000 });
        await page.waitForTimeout(jitter(2000, 4000));
      }

      await dismissBanners(page, log);
      // Close any open panels/chats first
      await page.keyboard.press("Escape").catch(() => {});
      await page.waitForTimeout(jitter(300, 500));

      const threads: UnreadThread[] = [];

      // Simple approach: find sidebar items with unread indicators, click to open,
      // read the username + last message from the opened chat, then close.
      // Only process 1-2 unread chats per tick to avoid spending too long.

      const unreadItems = await page.evaluate(() => {
        const items: { displayName: string; y: number; hasUnread: boolean }[] = [];
        const allEls = document.querySelectorAll('*');
        for (const el of allEls) {
          const rect = el.getBoundingClientRect();
          // Sidebar items: x < 370, y > 80, reasonable height
          if (rect.x > 370 || rect.y < 80 || rect.height < 40 || rect.height > 120 || rect.width < 100) continue;

          const text = (el.textContent || '').trim();
          if (!text || text.length < 3) continue;
          if (/team snapchat|my ai|snapchat support/i.test(text)) continue;

          // Check for unread: "New Chat", "Received", blue indicators
          const hasUnread = /new chat|received|\d+ new/i.test(text);

          // Check for blue colored text (Snap's unread indicator)
          const children = el.querySelectorAll('*');
          let hasBlue = false;
          for (const child of children) {
            const style = window.getComputedStyle(child);
            const color = style.color;
            if (color === 'rgb(0, 122, 255)' || color === 'rgb(0, 149, 246)' || color === 'rgb(53, 167, 255)') {
              hasBlue = true;
              break;
            }
          }

          if (hasUnread || hasBlue) {
            const nameMatch = text.match(/^([A-Za-z][A-Za-z0-9 ._-]*)/);
            const displayName = nameMatch ? nameMatch[1].trim() : '';
            if (displayName && displayName.length >= 2 && displayName.length < 25) {
              items.push({ displayName, y: rect.y, hasUnread: true });
            }
          }
        }
        // Deduplicate by name and sort by y
        const seen = new Set<string>();
        return items.filter(i => {
          if (seen.has(i.displayName)) return false;
          seen.add(i.displayName);
          return true;
        }).sort((a, b) => a.y - b.y).slice(0, 2); // Max 2 per tick
      });

      log.info({ unreadCount: unreadItems.length, names: unreadItems.map((i: any) => i.displayName) }, "sidebar scan");

      // For each unread, click to open, read username, close
      for (const item of unreadItems) {
        try {
          // Click the sidebar item by display name
          const sidebarEls = await page.$$('[role="listitem"], li, div[class]').catch(() => []);
          let clickedEl: any = null;
          for (const el of sidebarEls) {
            const visible = await el.isVisible().catch(() => false);
            if (!visible) continue;
            const box = await el.boundingBox().catch(() => null);
            if (!box || box.x > 370 || box.y < 80 || box.height < 35) continue;
            const text = ((await el.textContent()) || '').trim();
            if (text.includes(item.displayName)) {
              await el.click({ delay: jitter(40, 80) });
              clickedEl = el;
              break;
            }
          }
          if (!clickedEl) continue;

          await page.waitForTimeout(jitter(2000, 3000));

          // Read username from the chat — look for @username pattern in the right panel
          const chatUsername = await page.evaluate(() => {
            // Check URL for conversation ID hint
            const url = window.location.href;

            // Look for username text in chat header (right side, top area)
            const allEls = document.querySelectorAll('*');
            for (const el of allEls) {
              const rect = el.getBoundingClientRect();
              if (rect.x < 300 || rect.y > 150) continue;
              const text = (el.textContent || '').trim().toLowerCase();
              // Username patterns: short, alphanumeric with dots/underscores
              if (/^[a-z][a-z0-9._-]{2,20}$/.test(text) && !/(snapchat|search|chat|call|video|send|install|desktop|click)/i.test(text)) {
                return text;
              }
            }

            // Check for username below display name in header
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
              const t = (walker.currentNode.textContent || '').trim();
              if (!t) continue;
              const parent = walker.currentNode.parentElement;
              if (!parent) continue;
              const rect = parent.getBoundingClientRect();
              if (rect.x < 300 || rect.y > 120) continue;
              if (/^@?[a-z][a-z0-9._-]{2,20}$/i.test(t) && t.length < 25) {
                return t.replace(/^@/, '').toLowerCase();
              }
            }
            return '';
          });

          // Read last message from the chat
          const lastFanMsg = await page.evaluate(() => {
            const msgs: { text: string; isMe: boolean }[] = [];
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
              const t = (walker.currentNode.textContent || '').trim();
              if (!t || t.length < 2) continue;
              const parent = walker.currentNode.parentElement;
              if (!parent) continue;
              const rect = parent.getBoundingClientRect();
              if (rect.x < 340 || rect.y < 100) continue;
              if (/you are using snapchat|click to install|team snapchat|desktop app/i.test(t)) continue;
              if (t.length > 1 && t.length < 200) {
                const isBold = parseInt(window.getComputedStyle(parent).fontWeight) >= 600;
                const isLabel = t === 'ME' || t.length < 4 && /^[A-Z]+$/.test(t);
                if (!isLabel) msgs.push({ text: t, isMe: false });
              }
            }
            return msgs.length > 0 ? msgs[msgs.length - 1].text : '';
          });

          // Close the chat
          await page.keyboard.press("Escape").catch(() => {});
          await page.waitForTimeout(jitter(300, 500));
          await page.mouse.click(180, 200).catch(() => {});
          await page.waitForTimeout(jitter(200, 400));

          const fanUsername = chatUsername || item.displayName.replace(/[^a-zA-Z0-9._-]/g, '').toLowerCase();
          if (fanUsername.length < 2) continue;

          log.info({ displayName: item.displayName, resolvedUsername: fanUsername, lastMsg: lastFanMsg?.slice(0, 30) }, "resolved unread chat");

          // Create/update thread
          await prisma.chatThread.upsert({
            where: { accountId_fanUsername: { accountId, fanUsername } },
            create: { accountId, fanUsername, fanRealName: item.displayName, phase: "Building Rapport", lastMsgAt: new Date() },
            update: { lastMsgAt: new Date() },
          });

          threads.push({ fanUsername, displayName: item.displayName, lastMessage: lastFanMsg || "hey" });
        } catch (e: any) {
          log.warn({ displayName: item.displayName, err: e.message }, "unread chat processing failed");
        }
      }

      log.info({ count: threads.length, names: threads.map(t => t.fanUsername) }, "unread threads polled");
      return threads;
    }, { requireLoggedIn: true, keepOpen: true });
  } catch (e: any) {
    log.error({ err: e.message }, "poll failed");
    return [];
  }
}

/**
 * Open a specific chat by username and check if there are new messages
 * from the fan that we haven't responded to yet.
 */
async function checkChatForNewMessages(
  page: Page,
  fanUsername: string,
  threadId: string,
  log: ReturnType<typeof accountLogger>,
): Promise<string | null> {
  // Use the SIDEBAR search (LEFT side, x < 350) to find and open the chat.
  // NOT the Add Friends panel search — that's on the right side.
  // First, make sure the Add Friends panel is CLOSED.
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(jitter(300, 500));

  // Find the sidebar search — it's the input on the LEFT side (x < 350)
  const allInputs = await page.$$('input').catch(() => []);
  let search: any = null;
  for (const inp of allInputs) {
    const visible = await inp.isVisible().catch(() => false);
    if (!visible) continue;
    const box = await inp.boundingBox().catch(() => null);
    if (!box) continue;
    const placeholder = await inp.getAttribute('placeholder').catch(() => '') || '';
    // Sidebar search is on the LEFT side (x < 350) with "Search" placeholder
    if (box.x < 350 && /search/i.test(placeholder)) {
      search = inp;
      break;
    }
  }

  // Fallback: try data-testid
  if (!search) {
    search = await page.$('[data-testid="search-input"]').catch(() => null);
  }

  if (!search) {
    log.warn({ fan: fanUsername }, "sidebar search input not found for direct check");
    return null;
  }

  await search.click();
  await page.waitForTimeout(jitter(200, 400));
  await page.keyboard.press("Control+A");
  await page.keyboard.press("Backspace");
  await page.waitForTimeout(jitter(200, 400));
  for (const ch of fanUsername) {
    await page.keyboard.type(ch, { delay: jitter(60, 120) });
  }
  await page.waitForTimeout(jitter(2000, 3000));

  // Click the search result in the sidebar.
  // IMPORTANT: When searching by username (e.g. "andrewt407"), Snap may display
  // results with the DISPLAY name (e.g. "Andrew"), not the username. So we click
  // the first valid search result rather than requiring an exact text match.
  const targetLower = fanUsername.toLowerCase();
  const allItems = await page.$$('[role="listitem"], [role="option"], li, div[class]');
  let clicked = false;
  const resultCandidates: { el: any; text: string; y: number; exactMatch: boolean }[] = [];

  for (const item of allItems) {
    const visible = await item.isVisible().catch(() => false);
    if (!visible) continue;
    const box = await item.boundingBox().catch(() => null);
    if (!box || box.x > 370 || box.y < 80 || box.height < 30 || box.height > 120) continue;
    const text = ((await item.textContent()) || '').trim();
    if (!text || text.length < 2) continue;
    // Skip system accounts
    if (/team snapchat|my ai|snapchat support/i.test(text)) continue;
    const exactMatch = text.toLowerCase().includes(targetLower);
    resultCandidates.push({ el: item, text, y: box.y, exactMatch });
  }

  resultCandidates.sort((a, b) => {
    // Prefer exact matches, then sort by y position
    if (a.exactMatch !== b.exactMatch) return a.exactMatch ? -1 : 1;
    return a.y - b.y;
  });

  if (resultCandidates.length > 0) {
    await resultCandidates[0].el.click({ delay: jitter(40, 80) });
    log.info({ fan: fanUsername, clickedText: resultCandidates[0].text.slice(0, 40), exact: resultCandidates[0].exactMatch }, "clicked search result for direct check");
    clicked = true;
  }

  if (!clicked) {
    log.info({ fan: fanUsername }, "chat not found in sidebar search");
    await page.keyboard.press("Escape").catch(() => {});
    return null;
  }

  // Wait for chat to open — look for message input or contenteditable
  await page.waitForTimeout(jitter(2000, 3000));

  // Check if the chat actually opened (message input visible)
  let msgInput = await page.$('[contenteditable="true"], textarea, input[placeholder*="message" i], input[placeholder*="Send" i], input[placeholder*="chat" i]').catch(() => null);
  let inputVisible = msgInput ? await msgInput.isVisible().catch(() => false) : false;

  // If chat didn't open, try alternative approaches
  if (!inputVisible) {
    // Try 1: Click on any "Chat" or "Send Message" button in the search result
    const chatBtn = await page.$('button:has-text("Chat"), button:has-text("Send"), button:has-text("Message")').catch(() => null);
    if (chatBtn && await chatBtn.isVisible().catch(() => false)) {
      await chatBtn.click({ delay: jitter(40, 80) });
      await page.waitForTimeout(jitter(1500, 2500));
    }

    // Try 2: Press Enter to confirm the selection
    if (!inputVisible) {
      await page.keyboard.press("Enter");
      await page.waitForTimeout(jitter(1500, 2500));
    }

    // Try 3: Double-click the search result
    if (!inputVisible && resultCandidates.length > 0) {
      await resultCandidates[0].el.dblclick({ delay: jitter(40, 80) }).catch(() => {});
      await page.waitForTimeout(jitter(1500, 2500));
    }

    // Re-check for message input
    msgInput = await page.$('[contenteditable="true"], textarea, input[placeholder*="message" i], input[placeholder*="Send" i], input[placeholder*="chat" i]').catch(() => null);
    inputVisible = msgInput ? await msgInput.isVisible().catch(() => false) : false;
  }

  if (!inputVisible) {
    // Last resort: check if we can see any chat messages in the right panel
    // (the chat might be open but the input is outside the viewport or different)
    const hasChatContent = await page.evaluate(() => {
      const allEls = document.querySelectorAll('*');
      for (const el of allEls) {
        const rect = el.getBoundingClientRect();
        if (rect.x < 350 || rect.y < 100) continue;
        const text = (el.textContent || '').trim();
        // Look for typical chat indicators
        if (text.length > 5 && text.length < 200 && rect.height > 10 && rect.height < 100) {
          return true;
        }
      }
      return false;
    });

    if (!hasChatContent) {
      log.info({ fan: fanUsername }, "chat did not open (no message input or content)");
      await page.keyboard.press("Escape").catch(() => {});
      return null;
    }
    log.info({ fan: fanUsername }, "chat content visible but no message input — proceeding to read messages");
  }

  // Read all visible messages from the Snap chat view.
  // Snap web uses sender labels ("Me" = our account, display name = fan).
  // Messages are grouped under these labels. We scan top-to-bottom, tracking
  // which sender label we're under to determine role.
  const chatData = await page.evaluate(() => {
    // Collect all text nodes in the chat area (right panel, x > 340)
    const items: { text: string; x: number; y: number; fontSize: number; color: string; isBold: boolean }[] = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);

    while (walker.nextNode()) {
      const node = walker.currentNode as Text;
      const text = (node.textContent || '').trim();
      if (!text) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      const rect = range.getBoundingClientRect();
      if (rect.x < 340 || rect.y < 60 || rect.width < 3) continue;
      if (rect.height < 6) continue;

      const parent = node.parentElement;
      const style = parent ? window.getComputedStyle(parent) : null;
      const fontSize = style ? parseFloat(style.fontSize) : 14;
      const color = style?.color || '';
      const isBold = style ? parseInt(style.fontWeight) >= 600 : false;

      items.push({ text, x: rect.x, y: rect.y, fontSize, color, isBold });
    }

    items.sort((a, b) => a.y - b.y);

    // Identify sender labels. In Snap web chat:
    // - "Me" appears as a colored label (usually red/pink) before our messages
    // - The fan's display name appears as a colored label before their messages
    // - Sender labels are typically bold, short (< 20 chars), and colored
    // - Message text follows below the label
    //
    // We detect sender labels by checking for short, bold/colored text that matches
    // known patterns: "Me" or a single short name.

    // System/UI patterns to skip entirely
    const SKIP_RE = /^(\d{1,2}:\d{2}\s*(am|pm)?|\d{1,2}\s*(am|pm)|just now|\d+[mhd]\s*ago|today|yesterday|new|april|march|may|june|july|august|september|october|november|december|january|february)/i;
    const UI_RE = /^(delivered|opened|received|typing|new chat|say something|send a|click the|you (took|are)|try it|(is )?using snapchat|is using|snap(chat)? (is|support)|drag.*drop|upload|\d{4}|for web|at snapchat|snapchat\.com)/i;

    type MsgEntry = { text: string; role: 'fan' | 'me' };
    const messages: MsgEntry[] = [];
    let currentRole: 'fan' | 'me' = 'me'; // Default before first label

    for (const item of items) {
      // Skip system/UI text
      if (SKIP_RE.test(item.text)) continue;
      if (UI_RE.test(item.text)) continue;
      // Skip screenshot notifications
      if (/took a screenshot/i.test(item.text)) continue;
      // Skip very short non-word text
      if (item.text.length === 1 && !/[a-zA-Z0-9]/.test(item.text)) continue;

      // Check if this is a sender label
      // Sender labels in Snap are typically:
      // - "Me" (exactly) — our messages
      // - A short display name (1-2 words, < 20 chars) — fan messages
      // - Bold or colored differently from message text
      // - Usually has a distinct font size or color
      if (item.text === 'Me' && item.isBold) {
        currentRole = 'me';
        continue;
      }

      // A sender label for the fan is a short bold name that isn't a message
      if (item.isBold && item.text.length < 25 && !item.text.includes(' ') &&
          !/^(hey|hi|sup|yo|what|how|lol|omg|haha|ok|yeah|yea|nah|no|yes)/i.test(item.text)) {
        // This could be the fan's display name
        currentRole = 'fan';
        continue;
      }

      // Multi-word sender label (e.g., "Bailey Abigail")
      if (item.isBold && item.text.length < 25 && item.text.split(' ').length <= 3 &&
          /^[A-Z][a-z]/.test(item.text) &&
          !/^(Hey |Oh |How |What |I |You |No |Yes |LOL|OMG)/i.test(item.text)) {
        currentRole = 'fan';
        continue;
      }

      // It's a message — add it under current role
      messages.push({ text: item.text, role: currentRole });
    }

    return messages;
  });

  // EXIT the chat — press Escape + click neutral to deselect
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(jitter(200, 400));
  await page.keyboard.press("Escape").catch(() => {});
  await page.mouse.click(180, 200).catch(() => {});
  await page.waitForTimeout(jitter(200, 400));

  // Filter out remaining UI noise
  const UI_NOISE_RE = /^(click the|try it|using snapchat|you (are|took)|snap(chat)? (is|support)|send a|bailey|is using|for web|at snapchat|drag.*drop)/i;
  const cleanMessages = chatData.filter(m => !UI_NOISE_RE.test(m.text) && m.text.length >= 2);

  log.info({
    fan: fanUsername,
    totalMsgs: cleanMessages.length,
    last3: cleanMessages.slice(-3).map(m => `${m.role.toUpperCase()}: ${m.text.slice(0, 30)}`),
  }, "chat content read");

  // === SYNC messages from Snap to DB ===
  // Replace the entire DB thread content with what we see in Snap.
  // This ensures the AI always has the full, accurate conversation history.
  const thread = await prisma.chatThread.findUnique({
    where: { id: threadId },
    include: { messages: { orderBy: { timestamp: "asc" } } },
  });
  if (!thread) return null;

  // Check if the last message in the chat is from the fan
  if (cleanMessages.length === 0) return null;
  const lastMsg = cleanMessages[cleanMessages.length - 1];

  // If the last thing in the chat is from us (role='me'), no new fan message to process
  if (lastMsg.role === 'me') {
    // But still sync the history so our DB is up to date
    await syncMessagesToDb(threadId, cleanMessages, log);
    return null;
  }

  // Sync all messages to DB so the AI has full context
  await syncMessagesToDb(threadId, cleanMessages, log);

  // Return the last fan message for the AI to respond to
  log.info({ fan: fanUsername, msg: lastMsg.text.slice(0, 50) }, "new fan message detected");
  return lastMsg.text;
}

/**
 * Sync messages from Snap's chat view into our DB.
 * Replaces all messages in the thread with what we see in Snap,
 * so the AI always has accurate, complete conversation history.
 */
async function syncMessagesToDb(
  threadId: string,
  chatMessages: { text: string; role: 'fan' | 'me' }[],
  log: ReturnType<typeof accountLogger>,
): Promise<void> {
  if (chatMessages.length === 0) return;

  // Get current DB messages
  const dbMessages = await prisma.chatMessage.findMany({
    where: { threadId },
    orderBy: { timestamp: "asc" },
  });

  // Build the expected message sequence from Snap
  const snapMsgs = chatMessages.map(m => ({
    role: m.role === 'fan' ? 'user' : 'assistant',
    content: m.text,
  }));

  // Only sync if the conversation in Snap is different from DB.
  // Compare by role+content sequence to detect mismatches.
  const dbSeq = dbMessages.map(m => `${m.role}:${m.content}`).join('|');
  const snapSeq = snapMsgs.map(m => `${m.role}:${m.content}`).join('|');

  if (dbSeq === snapSeq) return; // Already in sync

  // Replace DB messages with Snap messages
  log.info({ threadId, dbCount: dbMessages.length, snapCount: snapMsgs.length }, "syncing chat history from Snap to DB");

  // Delete all existing messages for this thread
  await prisma.chatMessage.deleteMany({ where: { threadId } });

  // Create new messages with incrementing timestamps
  const baseTime = Date.now() - snapMsgs.length * 60000; // Space them 1 min apart
  for (let i = 0; i < snapMsgs.length; i++) {
    await prisma.chatMessage.create({
      data: {
        threadId,
        role: snapMsgs[i].role,
        type: "text",
        content: snapMsgs[i].content,
        timestamp: new Date(baseTime + i * 60000),
      },
    });
  }
}

/**
 * Check if a user we previously added has accepted by searching in the
 * Add Friends panel (right side). If they show up under "My Friends",
 * they accepted. Then close the panel, open a chat with them via the
 * sidebar search, and send the greeting.
 */
export async function greetIfAccepted(
  accountId: string,
  targetUsername: string,
  greeting: string = "hey",
): Promise<{ accepted: boolean; greeted: boolean; error?: string }> {
  const log = accountLogger((await prisma.account.findUniqueOrThrow({ where: { id: accountId } })).username);
  try {
    return await withSession(accountId, async (page) => {
      // Navigate to web.snapchat.com
      if (!/(web\.snapchat\.com|snapchat\.com\/web)/i.test(page.url())) {
        await page.goto("https://web.snapchat.com/", { waitUntil: "domcontentloaded", timeout: 30000 });
        await page.waitForTimeout(jitter(2000, 4000));
      }

      // Step 1: Open the Add Friends panel and search there
      const panelOpened = await openAddFriendsPanel(page, log);
      if (!panelOpened) return { accepted: false, greeted: false, error: "could not open Add Friends panel" };

      await page.waitForTimeout(jitter(800, 1500));

      const searchInput = await findPanelSearchInput(page, log);
      if (!searchInput) {
        await page.keyboard.press("Escape").catch(() => {});
        return { accepted: false, greeted: false, error: "panel search input not found" };
      }

      // Type the username in the Add Friends panel search
      await searchInput.click({ delay: jitter(40, 110) });
      await page.waitForTimeout(jitter(200, 500));
      await page.keyboard.press("Control+A");
      await page.keyboard.press("Backspace");
      await page.waitForTimeout(jitter(200, 400));
      for (const ch of targetUsername) {
        await page.keyboard.type(ch, { delay: jitter(70, 150) });
      }
      await page.waitForTimeout(jitter(2500, 4000));

      // Step 2: Check if a "My Friends" section appeared with the target user.
      // Snap's Add Friends panel shows search results in sections:
      //   "Add Friends" — users you can add (NOT friends)
      //   "My Friends" — users who ARE your friends
      // The target can appear in BOTH sections simultaneously (search result + friend).
      // The key check: does "My Friends" section exist AND contain the target username?
      const targetLower = targetUsername.toLowerCase();

      const panelAnalysis = await page.evaluate((uname) => {
        // Find all text content in the right panel (x > 260)
        const allEls = document.querySelectorAll('*');
        let myFriendsSectionY = -1;
        let addFriendsSectionY = -1;
        const friendEntries: { text: string; y: number }[] = [];

        for (const el of allEls) {
          const rect = el.getBoundingClientRect();
          if (rect.x < 260 || rect.width < 10) continue;

          const text = (el.textContent || '').trim();
          const directText = el.childNodes.length === 1 && el.childNodes[0].nodeType === 3
            ? (el.childNodes[0] as Text).textContent?.trim() || ''
            : '';

          // Detect section headings
          if (directText === 'My Friends' || (directText.toLowerCase() === 'my friends')) {
            myFriendsSectionY = rect.y;
          }
          if (directText === 'Add Friends' || (directText.toLowerCase() === 'add friends')) {
            addFriendsSectionY = rect.y;
          }

          // Check for the target username in elements below "My Friends" heading
          if (text.toLowerCase().includes(uname) && rect.y > 0) {
            friendEntries.push({ text: text.toLowerCase().slice(0, 100), y: rect.y });
          }
        }

        // Check if target appears AFTER the "My Friends" heading
        let inMyFriends = false;
        if (myFriendsSectionY > 0) {
          for (const entry of friendEntries) {
            // Entry must be below "My Friends" heading
            if (entry.y > myFriendsSectionY && entry.text.includes(uname)) {
              // And if "Add Friends" section exists, entry must be below it too
              // Actually, "My Friends" section is usually BELOW "Add Friends"
              inMyFriends = true;
              break;
            }
          }
        }

        return {
          myFriendsSectionY,
          addFriendsSectionY,
          inMyFriends,
          hasTarget: friendEntries.length > 0,
          entriesCount: friendEntries.length,
        };
      }, targetLower);

      log.info({
        target: targetUsername,
        myFriendsY: panelAnalysis.myFriendsSectionY,
        addFriendsY: panelAnalysis.addFriendsSectionY,
        inMyFriends: panelAnalysis.inMyFriends,
        hasTarget: panelAnalysis.hasTarget,
      }, "panel analysis");

      // Close the Add Friends panel
      await page.keyboard.press("Escape").catch(() => {});
      await page.waitForTimeout(jitter(500, 1000));

      // Decision: user is a friend if they appear in the "My Friends" section
      if (!panelAnalysis.hasTarget) {
        log.info({ target: targetUsername }, "greet check: user not found in Add Friends panel");
        return { accepted: false, greeted: false };
      }
      if (!panelAnalysis.inMyFriends) {
        log.info({ target: targetUsername }, "greet check: user found but NOT in My Friends section — still pending");
        return { accepted: false, greeted: false };
      }

      // Step 3: User is a friend! Close the panel and use sendMessages to send greeting.
      // sendMessages already has tested logic for opening a chat via sidebar search.
      log.info({ target: targetUsername, inMyFriends: panelAnalysis.inMyFriends }, "greet check: user is a friend — will send greeting");
      return { accepted: true, greeted: false }; // greeted=false — caller will send via sendMessages
    }, { requireLoggedIn: true, keepOpen: true });
  } catch (e: any) {
    log.error({ target: targetUsername, err: e.message }, "greet check failed");
    return { accepted: false, greeted: false, error: e.message };
  }
}

/**
 * Open a chat from the sidebar by clicking on a display name.
 * Returns the actual Snapchat username and last message from the chat.
 * Used to resolve __sidebar: placeholders into real usernames.
 */
export async function openSidebarChat(
  accountId: string,
  displayName: string,
): Promise<{ username: string; lastMessage: string } | null> {
  const log = accountLogger((await prisma.account.findUniqueOrThrow({ where: { id: accountId } })).username);
  try {
    return await withSession(accountId, async (page) => {
      // Make sure we're on web.snapchat.com
      if (!/(web\.snapchat\.com|snapchat\.com\/web)/i.test(page.url())) {
        await page.goto("https://web.snapchat.com/", { waitUntil: "domcontentloaded", timeout: 30000 });
        await page.waitForTimeout(jitter(2000, 4000));
      }

      // Close any open panels
      await page.keyboard.press("Escape").catch(() => {});
      await page.waitForTimeout(jitter(300, 500));

      // Find and click the chat item in the sidebar matching the display name
      const displayLower = displayName.toLowerCase();
      const sidebarItems = await page.$$('[role="listitem"], li, div[class]').catch(() => []);
      let clicked = false;

      for (const item of sidebarItems) {
        const visible = await item.isVisible().catch(() => false);
        if (!visible) continue;
        const box = await item.boundingBox().catch(() => null);
        if (!box || box.x > 370 || box.y < 80 || box.height < 35 || box.height > 120) continue;
        const text = ((await item.textContent()) || '').trim();
        if (!text || text.length < 2) continue;
        if (/team snapchat|my ai|snapchat support/i.test(text)) continue;

        if (text.toLowerCase().includes(displayLower)) {
          await item.click({ delay: jitter(40, 80) });
          clicked = true;
          log.info({ displayName, clickedText: text.slice(0, 40) }, "clicked sidebar chat item");
          break;
        }
      }

      if (!clicked) {
        log.warn({ displayName }, "sidebar chat item not found");
        return null;
      }

      await page.waitForTimeout(jitter(2000, 3000));

      // Read the username from the chat header (top right area, shows display name + @username)
      const chatInfo = await page.evaluate(() => {
        // Look for elements in the chat header area (x > 300, y < 100)
        const allEls = document.querySelectorAll('*');
        let username = '';
        let lastMsg = '';

        for (const el of allEls) {
          const rect = el.getBoundingClientRect();
          if (rect.x < 300 || rect.y > 100) continue;
          const text = (el.textContent || '').trim();
          // Username pattern: starts with @ or looks like a snap handle
          if (/^@?[a-z0-9._-]{3,}$/i.test(text) && text.length < 30) {
            username = text.replace(/^@/, '').toLowerCase();
          }
        }

        // Also try to find username from the chat content — Snap shows sender labels
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        const messages: string[] = [];
        while (walker.nextNode()) {
          const node = walker.currentNode as Text;
          const t = (node.textContent || '').trim();
          if (!t) continue;
          const parent = node.parentElement;
          if (!parent) continue;
          const rect = parent.getBoundingClientRect();
          // Chat content is on the right side (x > 340)
          if (rect.x < 340 || rect.y < 60) continue;
          if (t.length >= 2 && t.length < 200 && rect.height > 8 && rect.height < 80) {
            messages.push(t);
          }
        }

        if (messages.length > 0) lastMsg = messages[messages.length - 1];
        return { username, lastMsg };
      });

      // Close the chat after reading
      await page.keyboard.press("Escape").catch(() => {});
      await page.waitForTimeout(jitter(200, 400));
      await page.mouse.click(180, 200).catch(() => {});

      if (!chatInfo.username) {
        // Try getting username from the URL — Snap chat URLs sometimes contain the conversation ID
        // Or fall back to the display name cleaned up
        const cleanName = displayName.replace(/[^a-zA-Z0-9._-]/g, '').toLowerCase();
        if (cleanName.length >= 3) {
          log.info({ displayName, fallback: cleanName }, "using cleaned display name as username fallback");
          // Create thread with this name
          await prisma.chatThread.upsert({
            where: { accountId_fanUsername: { accountId, fanUsername: cleanName } },
            create: { accountId, fanUsername: cleanName, fanRealName: displayName, phase: "Building Rapport", lastMsgAt: new Date() },
            update: { lastMsgAt: new Date() },
          });
          return { username: cleanName, lastMessage: chatInfo.lastMsg || "[opened from sidebar]" };
        }
        return null;
      }

      log.info({ displayName, username: chatInfo.username }, "resolved username from chat header");

      // Create/update thread
      await prisma.chatThread.upsert({
        where: { accountId_fanUsername: { accountId, fanUsername: chatInfo.username } },
        create: { accountId, fanUsername: chatInfo.username, fanRealName: displayName, phase: "Building Rapport", lastMsgAt: new Date() },
        update: { lastMsgAt: new Date(), fanRealName: displayName },
      });

      return { username: chatInfo.username, lastMessage: chatInfo.lastMsg || "[opened from sidebar]" };
    }, { requireLoggedIn: true, keepOpen: true });
  } catch (e: any) {
    log.error({ displayName, err: e.message }, "openSidebarChat failed");
    return null;
  }
}

/**
 * ALL-IN-ONE: detect unread chats, open them, read messages, generate AI response,
 * type it directly in the already-open chat, and close. No sidebar searching needed.
 */
export async function detectAndRespondToUnreads(
  accountId: string,
  group: any,
  delays: { typeMin: number; typeMax: number; betweenMsgMin: number; betweenMsgMax: number; responseDelayMin: number; responseDelayMax: number },
): Promise<void> {
  const acc = await prisma.account.findUniqueOrThrow({ where: { id: accountId } });
  const log = accountLogger(acc.username);

  await withSession(accountId, async (page) => {
    // Ensure on web.snapchat.com
    if (!/(web\.snapchat\.com|snapchat\.com\/web)/i.test(page.url())) {
      await page.goto("https://web.snapchat.com/", { waitUntil: "domcontentloaded", timeout: 30000 });
      await page.waitForTimeout(jitter(2000, 4000));
    }
    await dismissBanners(page, log);
    await page.keyboard.press("Escape").catch(() => {});
    await page.waitForTimeout(jitter(300, 500));

    // Find sidebar items that need action:
    // 1. "Received" / "New Chat" — fan messaged us, we need to respond
    // 2. "Say Hi!" — fan added us back but hasn't messaged, we send opener
    const unreadItems = await page.evaluate(() => {
      const items: { displayName: string; y: number; type: string }[] = [];
      const seen = new Set<string>();
      const allEls = document.querySelectorAll('*');
      for (const el of allEls) {
        const rect = el.getBoundingClientRect();
        if (rect.x > 370 || rect.y < 80 || rect.height < 40 || rect.height > 120 || rect.width < 100) continue;
        const text = (el.textContent || '').trim();
        if (!text || text.length < 3) continue;
        if (/team snapchat|my ai|snapchat support/i.test(text)) continue;

        // Determine type
        let type = '';
        if (/received|new chat/i.test(text)) type = 'received';
        else if (/say hi/i.test(text)) type = 'sayhi';
        else continue;

        // Extract display name — strip status words
        let cleanText = text.replace(/received|opened|delivered|new chat|new snap|screenshot|say hi|just now|\d+[smhd]\s*ago|\d+\s*(min|sec|hour|day)|\·/gi, '').trim();
        const nameMatch = cleanText.match(/^([A-Za-z][A-Za-z0-9 ._'🏴🇬🇭❌-]{0,25})/);
        let name = nameMatch ? nameMatch[1].trim() : '';
        // Remove emoji-like chars
        name = name.replace(/[^\w\s._'-]/g, '').trim();
        if (name && name.length >= 2 && !seen.has(name) && !/^(close|view|call|send|chat)$/i.test(name)) {
          seen.add(name);
          items.push({ displayName: name, y: rect.y, type });
        }
      }
      return items.sort((a, b) => a.y - b.y).slice(0, 3);
    });

    if (unreadItems.length === 0) {
      log.info("no unread chats found");
      return;
    }
    log.info({ count: unreadItems.length, items: unreadItems.map((i: any) => `${i.displayName}(${i.type})`) }, "found actionable chats");

    for (const item of unreadItems) {
      try {
        // Step 1: Click the unread chat by its Y position in the sidebar
        // This is more reliable than matching by text content
        log.info({ fan: item.displayName, y: item.y }, "clicking unread chat by position");
        await page.mouse.click(150, item.y + 10);  // Click center of sidebar at the item's Y
        await page.waitForTimeout(jitter(2000, 3000));

        // Step 2: Handle based on type
        if (item.type === 'sayhi') {
          // Fan added us back but hasn't messaged — send a unique opener
          const openers = [
            "heyy",
            "hii",
            "heyyy whats up",
            "heyy added u cuz i was bored lol",
            "heyy u seem cool",
            "hey cutie",
            "hii how r u",
          ];
          const opener = openers[Math.floor(Math.random() * openers.length)];

          // Find and focus the message input
          const sayHiInputFocused = await page.evaluate(() => {
            const editables = document.querySelectorAll('[contenteditable="true"]');
            for (const el of editables) {
              const rect = el.getBoundingClientRect();
              if (rect.x > 300 && rect.width > 50 && rect.y > 300) {
                (el as HTMLElement).focus();
                (el as HTMLElement).click();
                return true;
              }
            }
            return false;
          });

          if (sayHiInputFocused) {
            for (const ch of opener) {
              await page.keyboard.type(ch, { delay: jitter(delays.typeMin, delays.typeMax) });
            }
            await page.waitForTimeout(jitter(300, 800));
            await page.keyboard.press("Enter");
            log.info({ fan: item.displayName, opener }, "sent opener to Say Hi fan");

            // Create thread
            const fanUsername = item.displayName.replace(/[^a-zA-Z0-9._-]/g, '').toLowerCase();
            await prisma.chatThread.upsert({
              where: { accountId_fanUsername: { accountId, fanUsername } },
              create: { accountId, fanUsername, fanRealName: item.displayName, phase: "Building Rapport", lastMsgAt: new Date() },
              update: { lastMsgAt: new Date() },
            });
            await prisma.chatMessage.create({
              data: {
                threadId: (await prisma.chatThread.findUnique({ where: { accountId_fanUsername: { accountId, fanUsername } } }))!.id,
                role: "assistant", type: "text", content: opener,
              },
            });
          }

          // Close chat
          await page.keyboard.press("Escape").catch(() => {});
          await page.waitForTimeout(jitter(300, 500));
          await page.mouse.click(180, 200).catch(() => {});
          continue;
        }

        // Step 2 (for "received" type): Read last message from fan
        const lastFanMsg = await page.evaluate(() => {
          const texts: string[] = [];
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          while (walker.nextNode()) {
            const t = (walker.currentNode.textContent || '').trim();
            if (!t || t.length < 2) continue;
            const parent = walker.currentNode.parentElement;
            if (!parent) continue;
            const rect = parent.getBoundingClientRect();
            if (rect.x < 340 || rect.y < 100) continue;
            if (/you are using snapchat|click to install|team snapchat|desktop app|send a chat|drag.*drop/i.test(t)) continue;
            if (t.length >= 2 && t.length < 200) texts.push(t);
          }
          return texts.length > 0 ? texts[texts.length - 1] : 'hey';
        });

        log.info({ fan: item.displayName, lastMsg: lastFanMsg.slice(0, 40) }, "read last message");

        // Step 3: Create/find thread and generate AI response
        const cleanDisplayName = item.displayName.replace(/\s*(received|opened|delivered|new chat|new snap|screenshot)\s*/gi, '').trim();
        const fanUsername = cleanDisplayName.replace(/[^a-zA-Z0-9._-]/g, '').toLowerCase();

        // Check if this fan already got the CTA — don't respond unless they have objections
        const existingThread = await prisma.chatThread.findUnique({
          where: { accountId_fanUsername: { accountId, fanUsername } },
        });
        if (existingThread?.converted) {
          log.info({ fan: fanUsername }, "fan already converted — skipping (CTA already sent)");
          await page.keyboard.press("Escape").catch(() => {});
          await page.waitForTimeout(jitter(300, 500));
          continue;
        }

        await prisma.chatThread.upsert({
          where: { accountId_fanUsername: { accountId, fanUsername } },
          create: { accountId, fanUsername, fanRealName: item.displayName, phase: "Building Rapport", lastMsgAt: new Date() },
          update: { lastMsgAt: new Date() },
        });

        // Import and run chat engine
        const { runChatEngine } = await import("./chatEngine.js");
        const result = await runChatEngine({
          accountId,
          fanUsername,
          incomingMessage: lastFanMsg,
        });

        if (result.underage || result.cooldown || result.content.length === 0) {
          log.info({ fan: item.displayName, underage: result.underage, cooldown: result.cooldown }, "skipping response");
          await page.keyboard.press("Escape").catch(() => {});
          await page.waitForTimeout(jitter(300, 500));
          continue;
        }

        // Step 4: Type directly in the chat input.
        // Use page.evaluate to find and focus any contenteditable or input on the right side,
        // then type via keyboard (no element handle needed).
        const inputFocused = await page.evaluate(() => {
          // Strategy 1: contenteditable div (Snap's message input)
          const editables = document.querySelectorAll('[contenteditable="true"]');
          for (const el of editables) {
            const rect = el.getBoundingClientRect();
            if (rect.x > 300 && rect.width > 50 && rect.y > 300) {
              (el as HTMLElement).focus();
              (el as HTMLElement).click();
              return { ok: true, x: Math.round(rect.x), y: Math.round(rect.y) };
            }
          }
          // Strategy 2: input/textarea with chat-related placeholder
          const inputs = document.querySelectorAll('input, textarea');
          for (const el of inputs) {
            const rect = el.getBoundingClientRect();
            const ph = (el as HTMLInputElement).placeholder?.toLowerCase() || '';
            if (rect.x > 300 && (ph.includes('send') || ph.includes('chat') || ph.includes('message'))) {
              (el as HTMLElement).focus();
              (el as HTMLElement).click();
              return { ok: true, x: Math.round(rect.x), y: Math.round(rect.y) };
            }
          }
          // Strategy 3: click at bottom-center of right panel
          return { ok: false, x: 0, y: 0 };
        });

        if (!inputFocused.ok) {
          // Fallback: click at the bottom of the page where input usually is
          const vp = page.viewportSize() || { width: 1920, height: 1080 };
          await page.mouse.click(vp.width * 0.65, vp.height - 40);
          await page.waitForTimeout(500);
          log.warn({ fan: item.displayName }, "input not found via DOM — clicked bottom of page");
        } else {
          log.info({ fan: item.displayName, x: inputFocused.x, y: inputFocused.y }, "focused chat input");
        }
        await page.waitForTimeout(jitter(300, 500));

        // Type each message piece using keyboard (input already focused)
        for (const p of result.content) {
          if (p.type !== "text") continue;
          for (const ch of p.content) {
            await page.keyboard.type(ch, { delay: jitter(delays.typeMin, delays.typeMax) });
          }
          await page.waitForTimeout(jitter(300, 800));
          await page.keyboard.press("Enter");
          log.info({ fan: item.displayName, msg: p.content.slice(0, 30) }, "sent message");
          await page.waitForTimeout(jitter(delays.betweenMsgMin, delays.betweenMsgMax));
        }

        // Step 5: Close the chat — press Escape and click neutral area
        await page.keyboard.press("Escape").catch(() => {});
        await page.waitForTimeout(jitter(300, 500));
        await page.mouse.click(180, 200).catch(() => {});
        await page.waitForTimeout(jitter(300, 500));
        log.info({ fan: item.displayName }, "chat closed after responding");

      } catch (e: any) {
        log.warn({ fan: item.displayName, err: e.message }, "respond to unread failed");
        await page.keyboard.press("Escape").catch(() => {});
        await page.waitForTimeout(jitter(300, 500));
      }
    }
  }, { requireLoggedIn: true, keepOpen: true });
}

export async function sendMessages(
  accountId: string,
  fanUsername: string,
  pieces: { type: string; content: string }[],
  typingMin: number,
  typingMax: number,
  betweenMsgMin: number,
  betweenMsgMax: number,
): Promise<void> {
  await withSession(accountId, async (page) => {
    await page.goto("https://web.snapchat.com/", { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(jitter(2000, 3500));

    const log = accountLogger((await prisma.account.findUniqueOrThrow({ where: { id: accountId } })).username);

    // Dismiss any banners that might block interactions
    await dismissBanners(page, log);

    // Step 1: Find and click the sidebar search input (x < 370)
    const search = await page.waitForSelector('[data-testid="search-input"], input[placeholder*="Search" i]', { timeout: 15000 });
    await search.click();
    for (const ch of fanUsername) await page.keyboard.type(ch, { delay: jitter(80, 180) });
    await page.waitForTimeout(jitter(2000, 3500));

    // Step 2: Find all search result items in the sidebar (x < 370), skip "Ask My AI" / "My AI"
    const targetLower = fanUsername.toLowerCase();
    const allItems = await page.$$('[role="listitem"], [role="option"], [data-testid*="search"], [data-testid*="chat-list"], li, div[class]');
    let clicked = false;

    // Collect candidate result entries in the sidebar
    const resultCandidates: { el: any; text: string; y: number }[] = [];
    for (const item of allItems) {
      const visible = await item.isVisible().catch(() => false);
      if (!visible) continue;
      const box = await item.boundingBox().catch(() => null);
      if (!box || box.x > 370 || box.height < 30 || box.height > 120) continue;
      // Must be below the search input area (y > 80)
      if (box.y < 80) continue;
      const text = ((await item.textContent()) || '').trim();
      if (!text || text.length < 3) continue;
      // Must contain the target username
      if (!text.toLowerCase().includes(targetLower)) continue;
      resultCandidates.push({ el: item, text, y: box.y });
    }

    log.info({ target: fanUsername, candidateCount: resultCandidates.length }, "sidebar search result candidates");

    // Sort by y position (top to bottom)
    resultCandidates.sort((a, b) => a.y - b.y);

    // Click the first result that does NOT contain "Ask My AI" or "My AI"
    for (const candidate of resultCandidates) {
      if (/ask\s*my\s*ai|my\s*ai/i.test(candidate.text)) {
        log.info({ text: candidate.text.slice(0, 60) }, "skipping My AI search result");
        continue;
      }
      await candidate.el.click({ delay: jitter(40, 110) });
      log.info({ text: candidate.text.slice(0, 60), y: Math.round(candidate.y) }, "clicked search result");
      clicked = true;
      break;
    }

    // Fallback: if no candidate was found via element inspection, try clicking by
    // coordinates in the sidebar area where results typically appear
    if (!clicked && resultCandidates.length === 0) {
      // Try a broader search: any clickable element in sidebar containing the username
      const broader = await page.$$('*');
      const broadCandidates: { el: any; text: string; y: number; depth: number }[] = [];
      for (const el of broader) {
        const visible = await el.isVisible().catch(() => false);
        if (!visible) continue;
        const box = await el.boundingBox().catch(() => null);
        if (!box || box.x > 370 || box.y < 80 || box.height < 35 || box.height > 100) continue;
        const text = ((await el.textContent()) || '').trim();
        if (!text.toLowerCase().includes(targetLower)) continue;
        if (/ask\s*my\s*ai|my\s*ai/i.test(text)) continue;
        // Prefer elements with smaller text length (more specific / leaf nodes)
        broadCandidates.push({ el, text, y: box.y, depth: text.length });
      }
      broadCandidates.sort((a, b) => a.y - b.y || a.depth - b.depth);
      if (broadCandidates.length > 0) {
        await broadCandidates[0].el.click({ delay: jitter(40, 110) });
        log.info({ text: broadCandidates[0].text.slice(0, 60) }, "clicked search result (broad fallback)");
        clicked = true;
      }
    }

    if (!clicked) {
      throw new Error(`No search result found for "${fanUsername}" in sidebar`);
    }

    // Step 3: Wait for the chat to open and message input to appear
    await page.waitForTimeout(jitter(1500, 2500));
    const msgInput = await page.waitForSelector(
      '[contenteditable="true"], textarea, input[type="text"][placeholder*="message" i]',
      { timeout: 15000 },
    );
    log.info("chat opened — message input found");

    // Step 4: Type and send each message piece
    for (const p of pieces) {
      if (p.type !== "text") continue;
      await msgInput.click();
      for (const ch of p.content) await page.keyboard.type(ch, { delay: jitter(typingMin, typingMax) });
      await page.waitForTimeout(jitter(300, 900));
      await page.keyboard.press("Enter");
      log.info({ piece: p.content.slice(0, 40) }, "sent message piece");
      await page.waitForTimeout(jitter(betweenMsgMin, betweenMsgMax));
    }

    // EXIT the chat by hovering over the conversation in the sidebar and clicking "X Close Chat".
    // This properly closes the chat so the fan doesn't see us as "viewing".
    log.info("closing chat view");

    // Strategy 1: Find the chat in sidebar, hover to reveal close button, click it
    let chatClosed = false;
    const sidebarChatItems = await page.$$('[role="listitem"], li, div[class]').catch(() => []);
    for (const item of sidebarChatItems) {
      const visible = await item.isVisible().catch(() => false);
      if (!visible) continue;
      const box = await item.boundingBox().catch(() => null);
      if (!box || box.x > 370 || box.y < 80 || box.height < 35 || box.height > 120) continue;
      const itemText = ((await item.textContent()) || '').toLowerCase();
      // Check if this sidebar item contains the fan's name/username
      const fanLower = fanUsername.toLowerCase();
      if (!itemText.includes(fanLower)) continue;

      // Hover over the chat item to reveal the close button
      await page.mouse.move(box.x + box.width - 30, box.y + box.height / 2, { steps: 5 });
      await page.waitForTimeout(jitter(500, 800));

      // Look for close/X button that appeared on hover
      const closeBtn = await item.$('[aria-label*="Close" i], [aria-label*="close" i]').catch(() => null);
      if (closeBtn && await closeBtn.isVisible().catch(() => false)) {
        await closeBtn.click({ delay: jitter(40, 80) });
        chatClosed = true;
        log.info("closed chat via hover close button");
        break;
      }

      // Try clicking any small X/close element in the hovered area
      const xBtns = await item.$$('button, [role="button"], svg').catch(() => []);
      for (const xBtn of xBtns) {
        const xBox = await xBtn.boundingBox().catch(() => null);
        if (!xBox || xBox.width > 30 || xBox.height > 30) continue;
        const xVis = await xBtn.isVisible().catch(() => false);
        if (!xVis) continue;
        await xBtn.click({ delay: jitter(40, 80) }).catch(() => {});
        chatClosed = true;
        log.info("closed chat via X button");
        break;
      }
      if (chatClosed) break;
    }

    // Strategy 2: Fallback — press Escape and click neutral area
    if (!chatClosed) {
      await page.keyboard.press("Escape").catch(() => {});
      await page.waitForTimeout(jitter(300, 500));
      await page.keyboard.press("Escape").catch(() => {});
      await page.waitForTimeout(jitter(200, 400));
      await page.mouse.click(180, 200).catch(() => {});
      log.info("closed chat via escape fallback");
    }

    await page.waitForTimeout(jitter(300, 600));
  }, { requireLoggedIn: true, keepOpen: true });
}
