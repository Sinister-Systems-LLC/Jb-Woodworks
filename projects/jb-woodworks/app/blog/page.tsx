// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { blogPostsByDate } from "@/lib/content/blog/posts";
import { SITE } from "@/lib/site";
import { Icon } from "@/components/ui/icon";
import { BackLink } from "@/components/ui/back-link";

export const metadata: Metadata = {
  title: "Blog & Field Notes",
  description:
    "Materials guides, build process notes, and Florida-specific deck / dock / furniture advice from the JB Woodworks shop.",
  alternates: { canonical: `${SITE.url}/blog` },
  openGraph: {
    title: "JB Woodworks - Blog & Field Notes",
    description:
      "Materials guides, build process notes, and Florida-specific deck / dock / furniture advice from the JB Woodworks shop.",
    url: `${SITE.url}/blog`,
    type: "website",
    siteName: SITE.name
  },
  twitter: {
    card: "summary_large_image",
    title: "JB Woodworks - Blog & Field Notes",
    description: "Materials guides, build process notes, and Florida-specific advice."
  }
};

export default function BlogIndex() {
  const posts = blogPostsByDate();

  // ItemList schema for the blog index — surfaces all posts to crawlers.
  const ld = {
    "@context": "https://schema.org",
    "@type": "Blog",
    "@id": `${SITE.url}/blog#blog`,
    name: "JB Woodworks - Blog & Field Notes",
    url: `${SITE.url}/blog`,
    publisher: {
      "@type": "LocalBusiness",
      "@id": `${SITE.url}/#business`,
      name: SITE.name
    },
    blogPost: posts.map((p) => ({
      "@type": "BlogPosting",
      headline: p.title,
      description: p.description,
      datePublished: p.publishedAt,
      dateModified: p.updatedAt ?? p.publishedAt,
      author: { "@type": "Organization", name: p.author },
      url: `${SITE.url}/blog/${p.slug}`,
      image: p.ogImage ? `${SITE.url}${p.ogImage}` : undefined
    }))
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }}
      />

      <section className="pt-40 pb-16 bg-gradient-to-b from-ink-2 to-ink border-b border-line relative overflow-hidden">
        <div
          aria-hidden
          className="absolute inset-0 pointer-events-none bg-cover bg-center"
          style={{ backgroundImage: "url(/img/generated/process-bench.png)", opacity: 0.18 }}
        />
        <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "linear-gradient(180deg, rgba(8,8,8,0.45) 0%, rgba(8,8,8,0.75) 60%, #080808 100%)" }} />
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%)" }} />

        <div className="container-site relative">
          <BackLink href="/" label="Back to home" section="Field Notes" />
          <span className="section-tag">Field Notes</span>
          <h1 className="mb-5">Notes from<br /><em>the shop.</em></h1>
          <p className="section-subheadline">
            Materials guides, build process, Florida-specific advice. Written by us, for the customers asking real questions.
          </p>
        </div>
      </section>

      <section className="py-20">
        <div className="container-site">
          <ul className="grid gap-10 sm:grid-cols-2 lg:grid-cols-3 list-none p-0">
            {posts.map((p, i) => (
              <li key={p.slug}>
                <Link
                  href={`/blog/${p.slug}`}
                  className="group block bg-ink-3 border border-line rounded-xl overflow-hidden transition-all duration-500 ease-out hover:border-gold hover:-translate-y-1.5 hover:shadow-[0_4px_32px_rgba(0,0,0,0.6)] h-full"
                >
                  {p.cover && (
                    <div className="relative aspect-[16/10] bg-ink-5 overflow-hidden">
                      <Image
                        src={p.cover}
                        alt={p.title}
                        fill
                        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                        quality={85}
                        loading={i < 2 ? undefined : "lazy"}
                        priority={i < 2}
                        className="object-cover transition-transform duration-1000 ease-out group-hover:scale-105 cinematic-image"
                      />
                      <span aria-hidden className="absolute inset-x-0 bottom-0 h-2/3 pointer-events-none" style={{ background: "linear-gradient(180deg, transparent 0%, rgba(8,8,8,0.55) 100%)" }} />
                    </div>
                  )}
                  <div className="p-7">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-[0.6rem] font-bold tracking-[0.22em] uppercase text-gold">
                        {p.category}
                      </span>
                      <span className="block w-1 h-1 rounded-full bg-gold-dim" aria-hidden />
                      <time dateTime={p.publishedAt} className="text-[0.7rem] tracking-wide text-cream-30">
                        {formatDate(p.publishedAt)}
                      </time>
                      <span className="block w-1 h-1 rounded-full bg-gold-dim" aria-hidden />
                      <span className="text-[0.7rem] tracking-wide text-cream-30">{p.readingTimeMinutes} min read</span>
                    </div>
                    <h3 className="font-display text-[1.3rem] text-white mb-3 leading-snug">{p.title}</h3>
                    <p className="text-cream-50 text-[0.92rem] leading-[1.7] mb-4">{p.excerpt}</p>
                    <span className="inline-flex items-center gap-1.5 text-gold text-[0.72rem] font-bold tracking-[0.14em] uppercase">
                      Read the piece
                      <Icon name="arrow-right" size={14} className="transition-transform duration-300 group-hover:translate-x-1" />
                    </span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Bottom CTA — Get Free Quote + Contact us */}
      <section className="py-20 sm:py-24 bg-ink-2 border-t border-line relative overflow-hidden">
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.08), transparent 70%)" }} />
        <div className="container-site relative text-center">
          <span className="section-tag mx-auto inline-block">Ready to build</span>
          <h2 className="mt-2 mb-5">Stop reading,<br /><em>start building.</em></h2>
          <p className="text-cream-50 text-[1rem] max-w-[560px] mx-auto mb-10">
            The blog is here for context — the real conversation starts when you tell us about your space.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href="/contact" className="btn btn-primary btn-large jbw-magnetic">Get a Free Quote</Link>
            <a href={`tel:${SITE.phoneTel}`} className="btn btn-ghost btn-large jbw-magnetic">Call {SITE.phone}</a>
          </div>
        </div>
      </section>
    </>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso + "T12:00:00Z");
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}
