// Author: RKOJ-ELENO :: 2026-05-23
// Accessibility statement. Targets WCAG 2.1 Level AA.
import type { Metadata } from "next";
import { LegalLayout } from "@/components/sections/legal-layout";
import { LEGAL } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Accessibility Statement",
  description: `JB Woodworks' commitment to an accessible website. Effective ${LEGAL.effectiveDate}.`
};

export default function AccessibilityStatement() {
  return (
    <LegalLayout
      tag="Accessibility"
      title={<>Accessibility<br /><em>Statement.</em></>}
      intro={<>Our goal is a site any visitor can use - keyboard-only, screen-reader, reduced motion, high contrast. If anything stops you, tell us.</>}
      activeHref="/legal/accessibility"
    >
      <h2>Our commitment</h2>
      <p>
        {LEGAL.entityName} is committed to making this website usable by the widest range of visitors possible. We design and build with the Web Content Accessibility Guidelines (WCAG) 2.1 Level AA as our target.
      </p>

      <h2>What we have done</h2>
      <ul>
        <li><strong>Semantic markup.</strong> Headings, lists, navigation, and landmarks are marked up with their correct HTML elements so assistive technology can interpret them.</li>
        <li><strong>Keyboard navigation.</strong> Every interactive element (links, buttons, the contact form, the mobile menu) is reachable and operable using only a keyboard. A &quot;Skip to main content&quot; link is the first focusable item on every page.</li>
        <li><strong>Visible focus.</strong> Focus indicators are always visible and meet contrast requirements.</li>
        <li><strong>Color contrast.</strong> The gold-on-black color palette meets or exceeds WCAG AA contrast ratios for body text and interactive elements.</li>
        <li><strong>Reduced motion.</strong> Visitors who have set their operating-system preference for reduced motion receive a calmer experience: animations are minimized or removed automatically (via <code>prefers-reduced-motion: reduce</code>).</li>
        <li><strong>Image and video alternatives.</strong> Decorative images are marked with <code>aria-hidden</code> or empty alt text so screen readers skip them. Meaningful images include descriptive alt text. Hero videos are muted, loop without sound, and are accompanied by foreground text content.</li>
        <li><strong>Responsive layout.</strong> Content reflows for narrow viewports, supports browser zoom up to 200%, and does not require horizontal scrolling at any common screen size.</li>
        <li><strong>Form labels and validation.</strong> Every contact-form field has an associated label. Errors are announced inline and described clearly.</li>
      </ul>

      <h2>Known limitations</h2>
      <p>
        We are continually improving. If you find any accessibility issue, we want to hear about it so we can fix it:
      </p>
      <ul>
        <li>Some portfolio detail pages may include images without descriptive alt text. We are working through the library to add it.</li>
        <li>Auto-rotating hero slides cycle on a timer; visitors with the &quot;reduced motion&quot; preference receive a static first slide, and visible dot controls let any visitor jump or pause.</li>
        <li>Background videos are decorative and contain no narration; if you experience any issue with video controls, let us know.</li>
      </ul>

      <h2>How to report an issue</h2>
      <p>
        If anything on this site is unusable for you, please contact us:
      </p>
      <ul>
        <li>Email: <a href={`mailto:${LEGAL.contactEmail}`}>{LEGAL.contactEmail}</a></li>
        <li>Phone: <a href="tel:4075611453">{LEGAL.contactPhone}</a></li>
      </ul>
      <p>
        Please include the page URL, a description of the issue, and the assistive technology, browser, or operating system you are using if you can. We aim to acknowledge accessibility reports within five business days and provide a remediation plan within thirty days.
      </p>

      <h2>Alternative ways to do business with us</h2>
      <p>
        You do not have to use the website to work with us. Phone calls, voicemail, text messages, and email are all welcome at the numbers and address above. If a different format is easier for you (large print, audio, in person at a job site), let us know and we will accommodate it.
      </p>

      <h2>Formal complaints</h2>
      <p>
        If you are not satisfied with how we have addressed an accessibility report, you may file a complaint with the appropriate authority for your jurisdiction. In the United States, that includes the U.S. Department of Justice (ada.gov) and the Florida Commission on Human Relations (fchr.myflorida.com).
      </p>

      <h2>Standards reference</h2>
      <p>
        Web Content Accessibility Guidelines (WCAG) 2.1, Level AA, published by the World Wide Web Consortium (W3C). Section 508 of the U.S. Rehabilitation Act is referenced where federal-funding contexts apply.
      </p>
    </LegalLayout>
  );
}
