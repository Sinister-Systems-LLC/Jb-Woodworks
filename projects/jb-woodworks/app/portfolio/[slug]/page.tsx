// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { Reveal } from "@/components/ui/reveal";
import { Icon } from "@/components/ui/icon";
import { BackLink } from "@/components/ui/back-link";
import { BeforeAfter } from "@/components/sections/before-after";
import { getPortfolioItem, portfolio } from "@/lib/content";
import { SITE } from "@/lib/site";

type Props = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  return portfolio.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const item = getPortfolioItem(slug);
  if (!item) return { title: "Project not found" };
  return {
    title: item.title,
    description: `${item.blurb} - JB Woodworks portfolio.`
  };
}

export default async function PortfolioItemPage({ params }: Props) {
  const { slug } = await params;
  const item = getPortfolioItem(slug);
  if (!item) notFound();

  // Per-project JSON-LD (CreativeWork) — improves rich-result eligibility for
  // each portfolio detail page (parent layout already emits LocalBusiness).
  const coverSrc = item.is_raw_cover ? `/img/projects/${item.cover}` : `/media/${item.cover}`;
  const work: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    "@id": `${SITE.url}/portfolio/${item.slug}`,
    name: item.title,
    description: item.blurb,
    image: `${SITE.url}${encodeURI(coverSrc)}`,
    genre: item.category,
    creator: { "@type": "LocalBusiness", "@id": `${SITE.url}/#business`, name: SITE.name },
    inLanguage: "en-US",
    url: `${SITE.url}/portfolio/${item.slug}`
  };
  if (item.meta?.year) work.dateCreated = item.meta.year;
  if (item.meta?.materials) work.material = item.meta.materials;
  if (item.meta?.location) work.contentLocation = item.meta.location;

  // BreadcrumbList JSON-LD — Home > Portfolio > {Title}. Google uses this to
  // render the breadcrumb hierarchy in search results.
  const crumbs = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: `${SITE.url}/` },
      { "@type": "ListItem", position: 2, name: "Portfolio", item: `${SITE.url}/portfolio` },
      { "@type": "ListItem", position: 3, name: item.title, item: `${SITE.url}/portfolio/${item.slug}` }
    ]
  };

  const metaEntries: { label: string; value: string }[] = [];
  if (item.meta?.year) metaEntries.push({ label: "Year", value: item.meta.year });
  if (item.meta?.location) metaEntries.push({ label: "Location", value: item.meta.location });
  if (item.meta?.materials) metaEntries.push({ label: "Materials", value: item.meta.materials });
  if (item.meta?.duration) metaEntries.push({ label: "Build time", value: item.meta.duration });

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(work) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(crumbs) }} />
      <section className="pt-40 pb-16 bg-gradient-to-b from-ink-2 to-ink border-b border-line relative overflow-hidden">
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(var(--accent-rgb),0.10), transparent 70%)" }} />
        <div className="container-site relative">
          <BackLink href="/portfolio" label="Back to portfolio" section={item.category} />
          <span className="section-tag">
            {item.category}
            {item.subcategory && (
              <>
                <span aria-hidden className="mx-2 text-cream-30">·</span>
                <span className="text-cream-50">{item.subcategory}</span>
              </>
            )}
          </span>
          <h1 className="mb-5"><em>{item.title}.</em></h1>
          <p className="section-subheadline">{item.blurb}</p>
          {metaEntries.length > 0 && (
            <dl className="mt-8 grid gap-x-9 gap-y-3 sm:grid-cols-2 lg:grid-cols-4 max-w-[760px]">
              {metaEntries.map((m) => (
                <div key={m.label} className="border-t border-line/70 pt-3">
                  <dt className="text-[0.62rem] font-bold tracking-[0.22em] uppercase text-gold">{m.label}</dt>
                  <dd className="mt-1 text-cream-50 text-[0.95rem]">{m.value}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      </section>

      <section className="py-24">
        <div className="container-site">
          <div className="grid gap-6 max-w-[960px] mx-auto">
            {item.media.map((m, i) => (
              <Reveal key={i} delay={i * 80} className="bg-ink-3 border border-line rounded-xl overflow-hidden transition-colors hover:border-gold-dim">
                {m.type === "video" ? (
                  <video
                    controls
                    preload="metadata"
                    muted
                    playsInline
                    poster={`/media/${m.poster}`}
                    className="w-full h-auto block"
                  >
                    <source src={`/media/${m.src}`} type="video/mp4" />
                    Your browser does not support video.
                  </video>
                ) : m.type === "before-after" ? (
                  <figure className="block">
                    <BeforeAfter
                      before={(m.beforeRaw ?? true) ? `/img/projects/${m.before}` : `/media/${m.before}`}
                      after={(m.afterRaw ?? true) ? `/img/projects/${m.after}` : `/media/${m.after}`}
                      alt={item.title}
                      eager={i === 0}
                    />
                    {m.caption && (
                      <figcaption className="px-5 py-4 text-cream-50 text-[0.85rem] italic font-display border-t border-line">
                        {m.caption}
                      </figcaption>
                    )}
                  </figure>
                ) : (
                  <Image
                    src={`/img/projects/${m.src}`}
                    alt={item.title}
                    width={1600}
                    height={1200}
                    sizes="(max-width: 960px) 100vw, 960px"
                    loading={i === 0 ? undefined : "lazy"}
                    priority={i === 0}
                    quality={92}
                    style={{ width: "100%", height: "auto" }}
                    className="block cinematic-image"
                  />
                )}
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTAs — Get Free Quote + Contact us (per operator: all portfolio pages need both) */}
      <section className="py-24 bg-ink-2 border-t border-line relative overflow-hidden">
        <div aria-hidden className="absolute -top-32 -right-24 w-[420px] h-[420px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(var(--accent-rgb),0.10), transparent 70%)" }} />
        <div aria-hidden className="absolute -bottom-32 -left-24 w-[420px] h-[420px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(var(--accent-rgb),0.06), transparent 70%)" }} />
        <div className="container-site relative text-center">
          <span className="section-tag mx-auto inline-block">Want one like this?</span>
          <h2 className="mt-2 mb-5">Free estimate.<br /><em>Honest pricing.</em></h2>
          <p className="text-cream-50 text-[1rem] max-w-[560px] mx-auto mb-10">
            Send the space, the timeline, the rough vision. We will come back with a real range and a real build date — usually within one business day.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href={`/contact?service=${item.slug}`} className="btn btn-primary btn-large jbw-magnetic">Get a Free Quote</Link>
            <Link href="/contact" className="btn btn-ghost btn-large jbw-magnetic">Contact us</Link>
          </div>
        </div>
      </section>

      <section className="py-16 relative overflow-hidden" style={{ background: "linear-gradient(135deg, var(--accent), var(--accent-deep))" }}>
        <div aria-hidden className="absolute inset-0 pointer-events-none bg-cover bg-center mix-blend-multiply" style={{ backgroundImage: "url(/img/generated/cta-shavings.png)", opacity: 0.30 }} />
        <div className="container-site flex items-center justify-between gap-8 flex-wrap relative">
          <div>
            <h2 className="text-ink">Or just call us.</h2>
            <p className="text-ink/80 mt-2">Sometimes a five-minute conversation beats a contact form.</p>
          </div>
          <a href="tel:4075611453" className="btn btn-large bg-ink text-white hover:bg-ink-3 jbw-magnetic">(407) 561-1453</a>
        </div>
      </section>
    </>
  );
}
