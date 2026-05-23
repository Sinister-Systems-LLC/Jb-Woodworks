// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Thanks", description: "Inquiry received - we will be in touch shortly." };

export default function ThanksPage() {
  return (
    <section className="pt-40 pb-24 bg-gradient-to-b from-ink-2 to-ink text-center">
      <div className="container-site">
        <span className="section-tag">Thanks</span>
        <h1 className="mb-5">Message<br /><em>received.</em></h1>
        <p className="section-subheadline mx-auto">
          Thank you for reaching out. We will be in touch shortly to discuss your project.
        </p>
        <div className="flex gap-3.5 justify-center flex-wrap">
          <Link href="/" className="btn btn-primary btn-large">Back to home</Link>
          <Link href="/portfolio" className="btn btn-ghost btn-large">Browse portfolio</Link>
        </div>
      </div>
    </section>
  );
}
