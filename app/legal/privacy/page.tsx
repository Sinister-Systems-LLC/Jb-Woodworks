// Author: RKOJ-ELENO :: 2026-05-23
// Privacy Policy. Starting draft. Have an attorney review for your jurisdiction
// before relying on it for compliance with any regulation (CCPA, GDPR, etc.).
import type { Metadata } from "next";
import { LegalLayout } from "@/components/sections/legal-layout";
import { LEGAL } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: `How JB Woodworks collects, uses, and protects information from visitors and customers. Effective ${LEGAL.effectiveDate}.`
};

export default function PrivacyPolicy() {
  return (
    <LegalLayout
      tag="Privacy"
      title={<>Privacy<br /><em>Policy.</em></>}
      intro={<>This describes what information we collect, why we collect it, how we use it, and the choices you have. Plain English, no dark patterns.</>}
      activeHref="/legal/privacy"
    >
      <h2>Who we are</h2>
      <p>
        {LEGAL.entityName} ({LEGAL.entityForm}) operates the website at this domain and provides custom woodworking services in {LEGAL.jurisdiction} and surrounding areas. References to &quot;we,&quot; &quot;us,&quot; or &quot;our&quot; in this policy mean {LEGAL.entityName}.
      </p>

      <h2>What we collect</h2>
      <p>We collect the smallest amount of information that lets us answer your inquiry and run the business honestly. Specifically:</p>
      <ul>
        <li><strong>Information you give us directly</strong> through the contact form, by phone, by email, or in person: your name, email address, phone number (if provided), the service you are interested in, and the message or description you send.</li>
        <li><strong>Server-side technical signals</strong> automatically captured when you submit the contact form: your IP address, your browser user-agent string, and a timestamp. These are used solely to detect and discourage spam and abuse of the form.</li>
        <li><strong>Photographs of work product</strong> we may take during projects we perform for you. These are used to maintain a portfolio. We will ask before publishing any photograph that identifies you, your address, or other personal details.</li>
      </ul>
      <p>We do <strong>not</strong> use third-party advertising trackers, cross-site analytics, fingerprinting, or behavioral profiling on this website. See our <a href="/legal/cookies">Cookies notice</a> for the full story on cookies and storage.</p>

      <h2>Why we use it</h2>
      <ul>
        <li>To respond to your project inquiry, prepare an estimate, and schedule any site visit.</li>
        <li>To send project-related communication during a build (status, scheduling, photographs of progress).</li>
        <li>To keep accurate records for tax, warranty, and liability purposes.</li>
        <li>To improve the website (e.g. fix a broken link a visitor reported).</li>
      </ul>
      <p>We do <strong>not</strong> sell, rent, or trade your information. We do not run remarketing or advertising audiences based on your visit.</p>

      <h2>Who we share it with</h2>
      <p>We share only what is necessary to operate the business and only with parties bound to keep it confidential:</p>
      <ul>
        <li><strong>Email delivery providers</strong> (e.g. Resend or a similar transactional email service) for the sole purpose of routing your inquiry to our inbox.</li>
        <li><strong>Hosting providers</strong> (e.g. Railway) where the website and database run.</li>
        <li><strong>Subcontractors or material suppliers</strong> directly involved in a specific project you have engaged us for, only when necessary to complete that project.</li>
        <li><strong>Law enforcement or government authorities</strong> only when required by lawful process (subpoena, court order, valid warrant).</li>
      </ul>

      <h2>How long we keep it</h2>
      <p>
        Contact-form inquiries are retained for up to {LEGAL.inquiryRetentionMonths} months and then deleted unless they led to an active project file. Active-project records (contracts, invoices, communications) are retained for at least the warranty period plus any period required by Florida law for contractor records. After that, records are deleted or anonymized.
      </p>
      <p>
        Server access logs (IP address, user-agent, timestamp) for the contact form are retained for up to 90 days for abuse detection, then purged.
      </p>

      <h2>How we protect it</h2>
      <p>
        The website is served over HTTPS. Form submissions are validated server-side and rate-limited. We follow reasonable, industry-standard administrative, technical, and physical safeguards appropriate to a business of our size. No system is perfectly secure, however, and we cannot guarantee absolute security.
      </p>

      <h2>Your rights</h2>
      <p>Depending on where you live, you may have the right to:</p>
      <ul>
        <li>Request a copy of the personal information we hold about you.</li>
        <li>Request that we correct inaccurate information.</li>
        <li>Request that we delete your information, subject to legal retention obligations.</li>
        <li>Object to or restrict certain processing.</li>
        <li>Lodge a complaint with a supervisory authority.</li>
      </ul>
      <p>
        To exercise any of these rights, contact us at <a href={`mailto:${LEGAL.privacyContactEmail}`}>{LEGAL.privacyContactEmail}</a>. We will respond within 30 days. We will not retaliate against you for exercising any privacy right.
      </p>

      <h2>Children</h2>
      <p>This website is not directed to children under 13. We do not knowingly collect personal information from children under 13. If you believe we have, please contact us and we will delete it.</p>

      <h2>Out-of-state and international visitors</h2>
      <p>The website is operated from {LEGAL.jurisdiction}. If you access it from elsewhere, your information will be transferred to and processed in the United States. By using the site, you consent to this transfer.</p>

      <h2>Changes</h2>
      <p>We may update this policy from time to time. The effective date at the top reflects the most recent revision. Material changes will be noted on the site for a reasonable period before they take effect.</p>

      <h2>Contact</h2>
      <p>
        For any privacy question, write to <a href={`mailto:${LEGAL.privacyContactEmail}`}>{LEGAL.privacyContactEmail}</a> or call {LEGAL.contactPhone}.
      </p>
    </LegalLayout>
  );
}
