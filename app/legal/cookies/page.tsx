// Author: RKOJ-ELENO :: 2026-05-23
// Cookies / local-storage notice. We currently do NOT set tracking cookies.
import type { Metadata } from "next";
import { LegalLayout } from "@/components/sections/legal-layout";
import { LEGAL } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Cookies Notice",
  description: `What cookies and browser storage JB Woodworks uses (almost none). Effective ${LEGAL.effectiveDate}.`
};

export default function CookiesNotice() {
  return (
    <LegalLayout
      tag="Cookies"
      title={<>Cookies<br /><em>Notice.</em></>}
      intro={<>The short version: we do not use tracking cookies. The long version explains exactly what minimal storage we do use and why.</>}
      activeHref="/legal/cookies"
    >
      <h2>Summary</h2>
      <p>
        This website does not set any cookies for advertising, cross-site tracking, behavioral profiling, or analytics. We do not embed third-party tracking scripts (Google Analytics, Facebook Pixel, etc.).
      </p>

      <h2>What we do use</h2>
      <table className="w-full text-[0.92rem] my-6 border-collapse">
        <thead>
          <tr className="border-b border-line-strong text-cream-50 text-[0.75rem] tracking-[0.16em] uppercase">
            <th className="text-left py-3 pr-4">Item</th>
            <th className="text-left py-3 pr-4">Type</th>
            <th className="text-left py-3 pr-4">Purpose</th>
            <th className="text-left py-3">Duration</th>
          </tr>
        </thead>
        <tbody className="text-cream-50">
          <tr className="border-b border-line">
            <td className="py-3 pr-4 text-white"><code>jbw_splash_seen</code></td>
            <td className="py-3 pr-4">sessionStorage</td>
            <td className="py-3 pr-4">Prevents the brand splash from re-firing on every page navigation within the same tab.</td>
            <td className="py-3">Tab lifetime</td>
          </tr>
          <tr className="border-b border-line">
            <td className="py-3 pr-4 text-white">Form anti-abuse cache</td>
            <td className="py-3 pr-4">Server-side, in-memory</td>
            <td className="py-3 pr-4">Briefly remembers the IP address that submitted the contact form to throttle repeat submissions and detect bots.</td>
            <td className="py-3">Up to 90 days</td>
          </tr>
        </tbody>
      </table>

      <h2>What we do NOT use</h2>
      <ul>
        <li>No third-party analytics (Google Analytics, Plausible, Fathom, Mixpanel, etc.).</li>
        <li>No advertising cookies or audience pixels (Meta, Google Ads, TikTok Pixel, etc.).</li>
        <li>No cross-site identifiers, fingerprinting, or browser-storage profiling.</li>
        <li>No social-media login tokens. Our social links open the platforms in new tabs and do not embed their tracking iframes.</li>
      </ul>

      <h2>If that ever changes</h2>
      <p>
        If we add any cookie or storage item beyond the table above, we will update this page first and, where required, present a clear consent control before setting it.
      </p>

      <h2>How to clear browser storage</h2>
      <p>
        You can clear all cookies and storage for any site directly from your browser settings:
      </p>
      <ul>
        <li><strong>Chrome / Edge:</strong> Settings &rarr; Privacy and Security &rarr; Cookies and other site data &rarr; See all site data.</li>
        <li><strong>Firefox:</strong> Settings &rarr; Privacy &amp; Security &rarr; Cookies and Site Data &rarr; Manage Data.</li>
        <li><strong>Safari:</strong> Preferences &rarr; Privacy &rarr; Manage Website Data.</li>
        <li><strong>Mobile browsers:</strong> Open Settings, find Privacy or Site Settings, and clear data per site.</li>
      </ul>

      <h2>Do Not Track</h2>
      <p>
        We do not set tracking cookies, so a Do-Not-Track signal does not change anything about how the site behaves. We still honor it as a matter of principle.
      </p>

      <h2>Contact</h2>
      <p>
        Questions about cookies or storage on the site? Email <a href={`mailto:${LEGAL.contactEmail}`}>{LEGAL.contactEmail}</a>.
      </p>
    </LegalLayout>
  );
}
