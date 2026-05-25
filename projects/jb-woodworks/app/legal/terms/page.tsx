// Author: RKOJ-ELENO :: 2026-05-23
// Terms of Service. Starting draft. Have an attorney review before relying on
// it for any contract or liability waiver.
import type { Metadata } from "next";
import { LegalLayout } from "@/components/sections/legal-layout";
import { LEGAL } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: `Terms of Service for the JB Woodworks website. Effective ${LEGAL.effectiveDate}.`
};

export default function TermsOfService() {
  return (
    <LegalLayout
      tag="Terms"
      title={<>Terms of<br /><em>Service.</em></>}
      intro={<>The rules of engagement for using this website and for the project work we do. Read once, save the link.</>}
      activeHref="/legal/terms"
    >
      <h2>1. Acceptance</h2>
      <p>
        By accessing or using this website, you agree to these Terms of Service. If you do not agree, please do not use the site. These terms apply to the website only - written project contracts (estimates, work orders, change orders) signed between you and {LEGAL.entityName} govern actual project work and prevail over anything stated here in the event of conflict.
      </p>

      <h2>2. Estimates are not contracts</h2>
      <p>
        Quotes, estimates, and conversations through the contact form, by email, by phone, or in person are <strong>not binding contracts</strong>. A project becomes a contract only after both parties sign a written work order or estimate that specifies the scope, materials, price, and schedule.
      </p>
      <p>
        Verbal change requests during a project will be confirmed in writing (text or email) before being treated as authorized. Cost and schedule for any change beyond the original scope are subject to a written change order.
      </p>

      <h2>3. Workmanship warranty</h2>
      <p>
        Unless a different period is stated in the signed work order, {LEGAL.entityName} warrants the workmanship of completed projects for {LEGAL.workmanshipWarrantyYears} year from the date of substantial completion. The warranty covers defects in our craftsmanship.
      </p>
      <p>The warranty does <strong>not</strong> cover:</p>
      <ul>
        <li>Defects in materials covered by a separate manufacturer warranty (Trex, TimberTech, hardware manufacturers, etc.). Those claims pass through to the manufacturer.</li>
        <li>Damage caused by weather extremes, flooding, hurricanes, falling debris, or any other event outside our control.</li>
        <li>Damage caused by misuse, abuse, neglect, accidents, or modifications made after we complete the work.</li>
        <li>Normal wear, weathering, staining, or finish degradation expected of natural materials in the Florida climate.</li>
        <li>Settling of structures attached to existing buildings or supported on existing surfaces we did not construct.</li>
      </ul>
      <p>To make a warranty claim, contact us at {LEGAL.contactPhone} or <a href={`mailto:${LEGAL.contactEmail}`}>{LEGAL.contactEmail}</a> within the warranty period and describe the issue.</p>

      <h2>4. Photographs of your project</h2>
      <p>
        We may photograph completed work for use in our portfolio, on this website, and on social media. We will not knowingly publish photographs that show your face, your full address, or other personal details without your permission. If you would prefer that we not photograph your project at all, tell us before work begins.
      </p>

      <h2>5. Acceptable use of the website</h2>
      <p>You agree not to:</p>
      <ul>
        <li>Submit false, misleading, or fraudulent information through the contact form.</li>
        <li>Use the contact form, email, or phone line for spam, harassment, or solicitation unrelated to a genuine project inquiry.</li>
        <li>Attempt to gain unauthorized access to the website, its database, or its underlying infrastructure.</li>
        <li>Scrape, harvest, or systematically extract content from the site.</li>
        <li>Use any portion of the website or our work product to train a machine-learning model without our written permission.</li>
      </ul>

      <h2>6. Intellectual property</h2>
      <p>
        All content on this website - including text, photographs, designs, branding marks, and code - is the property of {LEGAL.entityName} or its licensors and is protected by United States and international copyright law. You may view the site for personal, non-commercial use. Any other use (including reproduction, distribution, or display) requires our prior written permission.
      </p>

      <h2>7. Third-party links</h2>
      <p>
        The site links to third-party services (social media platforms, manufacturer websites). We are not responsible for the content, privacy practices, or operation of those services.
      </p>

      <h2>8. No professional advice</h2>
      <p>
        Content on this website is for general informational purposes and is not legal, engineering, or contractor advice for your specific situation. Always confirm permitting, structural, and code requirements with the appropriate authority for your jurisdiction before proceeding with any project.
      </p>

      <h2>9. Disclaimer of warranties</h2>
      <p>
        The website is provided on an &quot;as-is&quot; and &quot;as-available&quot; basis. To the maximum extent permitted by law, {LEGAL.entityName} disclaims all warranties of any kind regarding the website, whether express, implied, statutory, or otherwise, including warranties of merchantability, fitness for a particular purpose, and non-infringement. Project-specific warranties are covered in Section 3 and in the signed work order.
      </p>

      <h2>10. Limitation of liability</h2>
      <p>
        To the maximum extent permitted by law, {LEGAL.entityName} and its owner, employees, contractors, and agents will not be liable for any indirect, incidental, consequential, special, or punitive damages arising out of or related to your use of this website. Our total liability for any claim arising out of website use is limited to the greater of (a) the amount you paid {LEGAL.entityName} in the 12 months preceding the claim, or (b) USD $100. This section does not limit liability for personal injury, gross negligence, willful misconduct, or any liability that cannot be limited by law.
      </p>

      <h2>11. Indemnification</h2>
      <p>
        You agree to defend, indemnify, and hold harmless {LEGAL.entityName} from any claim, loss, liability, or expense (including reasonable attorneys&apos; fees) arising out of (a) your breach of these Terms, (b) your misuse of the website, or (c) your violation of any law or third-party right in connection with your use of the website.
      </p>

      <h2>12. Governing law and venue</h2>
      <p>
        These Terms are governed by {LEGAL.governingLaw}, without regard to its conflict-of-laws rules. Any dispute arising out of or related to these Terms or the website will be resolved exclusively in {LEGAL.venue}, and you consent to the jurisdiction of those courts.
      </p>

      <h2>13. Changes</h2>
      <p>
        We may update these Terms at any time by posting a revised version with a new effective date. Material changes will be noted on the site for a reasonable period before they take effect. Continued use of the website after the effective date constitutes acceptance of the revised Terms.
      </p>

      <h2>14. Severability and entire agreement</h2>
      <p>
        If any provision of these Terms is held unenforceable, the remaining provisions remain in effect. These Terms, together with our <a href="/legal/privacy">Privacy Policy</a> and <a href="/legal/cookies">Cookies Notice</a>, constitute the entire agreement between you and {LEGAL.entityName} regarding the website.
      </p>

      <h2>15. Contact</h2>
      <p>
        Questions about these Terms? Reach us at <a href={`mailto:${LEGAL.contactEmail}`}>{LEGAL.contactEmail}</a> or {LEGAL.contactPhone}.
      </p>
    </LegalLayout>
  );
}
