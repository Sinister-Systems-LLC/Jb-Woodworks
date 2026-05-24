// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { blogPosts, getBlogPost } from "@/lib/content/blog/posts";
import { SITE } from "@/lib/site";
import { Icon } from "@/components/ui/icon";
import { BackLink } from "@/components/ui/back-link";

type Props = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  return blogPosts.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = getBlogPost(slug);
  if (!post) return { title: "Post not found" };

  const url = `${SITE.url}/blog/${post.slug}`;
  const ogImage = post.ogImage ? `${SITE.url}${post.ogImage}` : `${SITE.url}/img/og-image.svg`;

  return {
    title: post.title,
    description: post.description,
    keywords: [...post.tags],
    authors: [{ name: post.author }],
    alternates: { canonical: url },
    openGraph: {
      type: "article",
      url,
      siteName: SITE.name,
      title: post.title,
      description: post.description,
      publishedTime: new Date(post.publishedAt + "T12:00:00Z").toISOString(),
      modifiedTime: new Date((post.updatedAt ?? post.publishedAt) + "T12:00:00Z").toISOString(),
      authors: [post.author],
      images: [{ url: ogImage, width: 1200, height: 630, alt: post.title }],
      tags: [...post.tags]
    },
    twitter: {
      card: "summary_large_image",
      title: post.title,
      description: post.description,
      images: [ogImage]
    }
  };
}

export default async function BlogPostPage({ params }: Props) {
  const { slug } = await params;
  const post = getBlogPost(slug);
  if (!post) notFound();

  const url = `${SITE.url}/blog/${post.slug}`;
  const ogImageAbs = post.ogImage ? `${SITE.url}${post.ogImage}` : `${SITE.url}/img/og-image.svg`;

  // schema.org Article structured data — feeds Google Discover + rich results.
  const ld = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "@id": `${url}#article`,
    headline: post.title,
    description: post.description,
    image: { "@type": "ImageObject", url: ogImageAbs, width: 1200, height: 630 },
    datePublished: new Date(post.publishedAt + "T12:00:00Z").toISOString(),
    dateModified: new Date((post.updatedAt ?? post.publishedAt) + "T12:00:00Z").toISOString(),
    author: { "@type": "Organization", "@id": `${SITE.url}/#business`, name: post.author },
    publisher: {
      "@type": "Organization",
      "@id": `${SITE.url}/#business`,
      name: SITE.name,
      logo: { "@type": "ImageObject", url: `${SITE.url}/img/favicon-512.png`, width: 512, height: 512 }
    },
    mainEntityOfPage: { "@type": "WebPage", "@id": url },
    articleSection: post.category,
    keywords: post.tags.join(", "),
    wordCount: countWords(post.bodyHtml),
    inLanguage: "en-US",
    isPartOf: { "@type": "Blog", "@id": `${SITE.url}/blog#blog` }
  };

  // BreadcrumbList — helps Google show the breadcrumb in SERPs.
  const breadcrumb = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: `${SITE.url}/` },
      { "@type": "ListItem", position: 2, name: "Blog", item: `${SITE.url}/blog` },
      { "@type": "ListItem", position: 3, name: post.title, item: url }
    ]
  };

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumb) }} />

      <article>
        <header className="pt-40 pb-12 bg-gradient-to-b from-ink-2 to-ink border-b border-line relative overflow-hidden">
          {post.cover && (
            <div
              aria-hidden
              className="absolute inset-0 pointer-events-none bg-cover bg-center"
              style={{ backgroundImage: `url(${encodeURI(post.cover)})`, opacity: 0.18 }}
            />
          )}
          <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "linear-gradient(180deg, rgba(8,8,8,0.55) 0%, rgba(8,8,8,0.85) 70%, #080808 100%)" }} />
          <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%)" }} />

          <div className="container-site relative max-w-[840px]">
            <BackLink href="/blog" label="Back to Field Notes" section={post.category} />

            {/* Hidden semantic breadcrumb for SEO + screen-readers (JSON-LD
                handles SERP rendering; this is the a11y / browser-history
                fallback) */}
            <nav aria-label="Breadcrumb" className="sr-only">
              <ol>
                <li><Link href="/">Home</Link></li>
                <li><Link href="/blog">Blog</Link></li>
                <li aria-current="page">{post.title}</li>
              </ol>
            </nav>

            <span className="section-tag">{post.category}</span>
            <h1 className="mb-6 max-w-[800px]">{post.title}</h1>

            <div className="flex flex-wrap items-center gap-4 text-[0.78rem] text-cream-50">
              <span className="font-semibold">By {post.author}</span>
              <span aria-hidden>·</span>
              <time dateTime={post.publishedAt}>{formatDate(post.publishedAt)}</time>
              <span aria-hidden>·</span>
              <span>{post.readingTimeMinutes} min read</span>
              {post.updatedAt && post.updatedAt !== post.publishedAt && (
                <>
                  <span aria-hidden>·</span>
                  <span>Updated {formatDate(post.updatedAt)}</span>
                </>
              )}
            </div>
          </div>
        </header>

        {post.cover && (
          <div className="container-site mt-12 max-w-[1080px]">
            <div className="relative aspect-[16/9] rounded-2xl overflow-hidden border border-line bg-ink-3">
              <Image
                src={post.cover}
                alt={post.title}
                fill
                sizes="(max-width: 1024px) 100vw, 1080px"
                quality={88}
                priority
                className="object-cover cinematic-image"
              />
            </div>
          </div>
        )}

        <section className="py-14 sm:py-16">
          <div className="container-site max-w-[760px]">
            <div
              className="jbw-prose"
              dangerouslySetInnerHTML={{ __html: post.bodyHtml }}
            />

            {post.tags.length > 0 && (
              <ul className="mt-12 flex flex-wrap gap-2 list-none p-0">
                {post.tags.map((t) => (
                  <li key={t}>
                    <span className="inline-flex items-center px-3 py-1.5 bg-ink-3 border border-line rounded-full text-[0.65rem] tracking-[0.18em] uppercase font-bold text-cream-50">
                      #{t}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </article>

      {/* Bottom CTA — Get Free Quote + Contact us */}
      <section className="py-20 sm:py-24 bg-ink-2 border-t border-line relative overflow-hidden">
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.08), transparent 70%)" }} />
        <div className="container-site relative text-center">
          <span className="section-tag mx-auto inline-block">Ready to build</span>
          <h2 className="mt-2 mb-5">Want one of these?<br /><em>Tell us about it.</em></h2>
          <p className="text-cream-50 text-[1rem] max-w-[560px] mx-auto mb-10">
            Free estimate. Honest pricing. We will give you a real range usually within one business day.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href="/contact" className="btn btn-primary btn-large jbw-magnetic">Get a Free Quote</Link>
            <Link href="/blog" className="btn btn-ghost btn-large jbw-magnetic">More field notes</Link>
          </div>
        </div>
      </section>
    </>
  );
}

function countWords(html: string): number {
  return html.replace(/<[^>]+>/g, " ").trim().split(/\s+/).length;
}

function formatDate(iso: string): string {
  const d = new Date(iso + "T12:00:00Z");
  return d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
}
