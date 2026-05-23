// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { Reveal } from "@/components/ui/reveal";
import { Icon } from "@/components/ui/icon";
import { BeforeAfter } from "@/components/sections/before-after";
import { getPortfolioItem, portfolio } from "@/lib/content";

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

  return (
    <>
      <section className="pt-40 pb-16 bg-gradient-to-b from-ink-2 to-ink border-b border-line relative overflow-hidden">
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%)" }} />
        <div className="container-site relative">
          <span className="section-tag">{item.category}</span>
          <h1 className="mb-5"><em>{item.title}.</em></h1>
          <p className="section-subheadline">{item.blurb}</p>
          <p>
            <Link href="/portfolio" className="link-arrow">
              <Icon name="arrow-right" size={14} className="rotate-180" />
              Back to portfolio
            </Link>
          </p>
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
                    style={{ width: "100%", height: "auto" }}
                    className="block"
                  />
                )}
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 relative overflow-hidden" style={{ background: "linear-gradient(135deg, #c9a84c, #a8842f)" }}>
        <div className="container-site flex items-center justify-between gap-8 flex-wrap relative">
          <div>
            <h2 className="text-ink">Want one like this?</h2>
            <p className="text-ink/80 mt-2">Free estimate. Tell us the space and the timeline.</p>
          </div>
          <Link href={`/contact?service=${item.slug}`} className="btn btn-large bg-ink text-white hover:bg-ink-3">Get a Quote</Link>
        </div>
      </section>
    </>
  );
}
