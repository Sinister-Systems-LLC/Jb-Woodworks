// Author: RKOJ-ELENO :: 2026-05-23
// /rss.xml - RSS 2.0 feed of blog posts. Aggregator-friendly, no deps.
import { NextResponse } from "next/server";
import { blogPostsByDate } from "@/lib/content/blog/posts";
import { SITE } from "@/lib/site";

export const dynamic = "force-static";

function escape(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function rfc822(iso: string): string {
  return new Date(iso + "T12:00:00Z").toUTCString();
}

export async function GET() {
  const posts = blogPostsByDate();
  const latest = posts[0];
  const lastBuild = latest ? rfc822(latest.updatedAt ?? latest.publishedAt) : new Date().toUTCString();

  const items = posts.map((p) => {
    const url = `${SITE.url}/blog/${p.slug}`;
    return `<item>
  <title>${escape(p.title)}</title>
  <link>${url}</link>
  <guid isPermaLink="true">${url}</guid>
  <description>${escape(p.description)}</description>
  <category>${escape(p.category)}</category>
  <pubDate>${rfc822(p.publishedAt)}</pubDate>
  <author>noreply@jbwoodworks.example (${escape(p.author)})</author>
</item>`;
  }).join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${escape(SITE.name)} - Field Notes</title>
    <link>${SITE.url}/blog</link>
    <atom:link href="${SITE.url}/rss.xml" rel="self" type="application/rss+xml" />
    <description>Materials guides, build process, Florida-specific advice from the JB Woodworks shop.</description>
    <language>en-us</language>
    <lastBuildDate>${lastBuild}</lastBuildDate>
    <generator>JB Woodworks site (Next.js 15)</generator>
    ${items}
  </channel>
</rss>`;

  return new NextResponse(xml, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
      "Cache-Control": "public, max-age=3600, s-maxage=3600"
    }
  });
}
