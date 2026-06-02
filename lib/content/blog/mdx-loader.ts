// Author: RKOJ-ELENO :: 2026-06-02
// Reads MDX files from content/blog/ and returns BlogPost objects.
// Zero external deps — frontmatter parsed by hand, MD-to-HTML by inline converter.
// Runs server-side only (fs / path are safe here; this file is never bundled for client).

import fs from "fs";
import path from "path";

// Inline BlogPost shape to avoid circular dep with posts.ts
type BlogPost = {
  slug: string; title: string; description: string; excerpt: string;
  category: string; tags: readonly string[]; publishedAt: string;
  updatedAt?: string; author: string; cover?: string; ogImage?: string;
  readingTimeMinutes: number; bodyHtml: string;
};

// ---------------------------------------------------------------------------
// Frontmatter parser
// ---------------------------------------------------------------------------

type FM = {
  slug?: string;
  title?: string;
  description?: string;
  date?: string;
  publishedAt?: string;
  author?: string;
  category?: string;
  tags?: string[];
  readingTimeMinutes?: number;
  cover?: string;
  ogImage?: string;
};

function parseFrontmatter(raw: string): { fm: FM; body: string } {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) return { fm: {}, body: raw };

  const yamlBlock = match[1];
  const body = match[2];
  const fm: FM = {};

  for (const line of yamlBlock.split(/\r?\n/)) {
    const colon = line.indexOf(":");
    if (colon === -1) continue;
    const key = line.slice(0, colon).trim() as keyof FM;
    const raw = line.slice(colon + 1).trim();

    if (key === "tags") {
      const inner = raw.replace(/^\[/, "").replace(/\]$/, "");
      (fm as Record<string, unknown>).tags = inner
        .split(",")
        .map((t) => t.trim().replace(/^["']|["']$/g, ""))
        .filter(Boolean);
    } else if (key === "readingTimeMinutes") {
      (fm as Record<string, unknown>).readingTimeMinutes = parseInt(raw, 10) || 5;
    } else {
      (fm as Record<string, unknown>)[key] = raw.replace(/^["']|["']$/g, "");
    }
  }

  return { fm, body };
}

// ---------------------------------------------------------------------------
// Inline markdown → HTML
// ---------------------------------------------------------------------------

function inlineMd(text: string): string {
  return text
    .replace(/\*\*\*(.*?)\*\*\*/g, '<strong class="text-white font-bold"><em class="text-gold not-italic">$1</em></strong>')
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-bold">$1</strong>')
    .replace(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/g, '<em class="text-gold not-italic">$1</em>')
    .replace(/`([^`]+)`/g, '<code class="font-mono text-[0.88em] bg-ink-3 text-gold px-1.5 py-0.5 rounded">$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-gold underline underline-offset-2 hover:text-gold-light transition-colors">$1</a>');
}

function renderTable(rows: string[]): string {
  const isSep = (row: string) => /^\|[-: |]+\|$/.test(row.trim());
  const dataRows = rows.filter((r) => !isSep(r));
  if (dataRows.length === 0) return "";

  const parseRow = (row: string) =>
    row
      .split("|")
      .map((c) => c.trim())
      .filter((_, i, arr) => i > 0 && i < arr.length - 1);

  const headerCells = parseRow(dataRows[0]);
  const bodyRows = dataRows.slice(1);

  const th = headerCells
    .map(
      (c) =>
        `<th class="px-3 py-2 text-left text-[0.65rem] tracking-[0.18em] uppercase font-bold text-gold border-b border-line whitespace-nowrap">${inlineMd(c)}</th>`
    )
    .join("");

  const tb = bodyRows
    .map((row) => {
      const cells = parseRow(row);
      const tds = cells
        .map(
          (c) =>
            `<td class="px-3 py-2 text-cream-50 text-[0.88rem] border-b border-line/40">${inlineMd(c)}</td>`
        )
        .join("");
      return `<tr class="hover:bg-ink-3/40 transition-colors">${tds}</tr>`;
    })
    .join("");

  return `<div class="overflow-x-auto mb-8 rounded-lg border border-line">\n<table class="w-full text-left">\n<thead><tr>${th}</tr></thead>\n<tbody>${tb}</tbody>\n</table>\n</div>\n`;
}

function mdToHtml(md: string): string {
  const lines = md.split(/\r?\n/);
  let html = "";
  let inUl = false;
  let inOl = false;
  let tableBuffer: string[] = [];

  const closeList = () => {
    if (inUl) { html += "</ul>\n"; inUl = false; }
    if (inOl) { html += "</ol>\n"; inOl = false; }
  };

  const flushTable = () => {
    if (tableBuffer.length > 0) {
      html += renderTable(tableBuffer);
      tableBuffer = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trimEnd();

    // Table rows
    if (trimmed.startsWith("|")) {
      closeList();
      tableBuffer.push(trimmed);
      continue;
    } else if (tableBuffer.length > 0) {
      flushTable();
    }

    // H2
    if (trimmed.startsWith("## ")) {
      closeList();
      html += `<h2 class="font-display text-[clamp(1.5rem,3vw,2rem)] text-white mt-12 mb-4 leading-tight">${inlineMd(trimmed.slice(3))}</h2>\n`;
      continue;
    }

    // H3
    if (trimmed.startsWith("### ")) {
      closeList();
      html += `<h3 class="font-display text-[1.15rem] text-white mt-8 mb-3 leading-snug">${inlineMd(trimmed.slice(4))}</h3>\n`;
      continue;
    }

    // H4
    if (trimmed.startsWith("#### ")) {
      closeList();
      html += `<h4 class="font-sans text-[0.88rem] font-bold tracking-[0.12em] uppercase text-gold mt-6 mb-2">${inlineMd(trimmed.slice(5))}</h4>\n`;
      continue;
    }

    // Horizontal rule
    if (trimmed === "---" || trimmed === "***" || trimmed === "___") {
      closeList();
      html += '<hr class="my-10 border-0 h-px bg-gradient-to-r from-transparent via-gold/30 to-transparent" />\n';
      continue;
    }

    // Unordered list item
    const ulMatch = trimmed.match(/^[-*+] (.+)/);
    if (ulMatch) {
      if (inOl) { html += "</ol>\n"; inOl = false; }
      if (!inUl) { html += '<ul class="list-disc pl-5 text-cream-50 leading-[1.8] mb-6 space-y-1.5">\n'; inUl = true; }
      html += `  <li>${inlineMd(ulMatch[1])}</li>\n`;
      continue;
    }

    // Ordered list item
    const olMatch = trimmed.match(/^\d+\. (.+)/);
    if (olMatch) {
      if (inUl) { html += "</ul>\n"; inUl = false; }
      if (!inOl) { html += '<ol class="list-decimal pl-5 text-cream-50 leading-[1.8] mb-6 space-y-1.5">\n'; inOl = true; }
      html += `  <li>${inlineMd(olMatch[1])}</li>\n`;
      continue;
    }

    // Empty line
    if (trimmed === "") {
      closeList();
      continue;
    }

    // Regular paragraph
    closeList();
    html += `<p class="text-cream-50 leading-[1.85] mb-5">${inlineMd(trimmed)}</p>\n`;
  }

  flushTable();
  closeList();
  return html;
}

// ---------------------------------------------------------------------------
// Public loader
// ---------------------------------------------------------------------------

let _cache: BlogPost[] | null = null;

export function loadMdxBlogPosts(): BlogPost[] {
  // Module-level cache — valid for the lifetime of a prod server process.
  // In dev, Next.js hot-reloads modules so this re-runs on change.
  if (_cache) return _cache;

  const dir = path.join(process.cwd(), "content", "blog");
  if (!fs.existsSync(dir)) return [];

  const files = fs.readdirSync(dir).filter((f) => f.endsWith(".mdx") || f.endsWith(".md"));

  const posts: BlogPost[] = [];

  for (const file of files) {
    try {
      const raw = fs.readFileSync(path.join(dir, file), "utf-8");
      const { fm, body } = parseFrontmatter(raw);

      const slug = fm.slug ?? file.replace(/\.(mdx|md)$/, "");
      const publishedAt = fm.publishedAt ?? (fm as Record<string, unknown>).date as string ?? "2026-01-01";
      const author = fm.author === "RKOJ-ELENO" ? "JB Woodworks" : (fm.author ?? "JB Woodworks");
      const description = fm.description ?? fm.title ?? "";
      const bodyHtml = mdToHtml(body.trim());

      // Extract first sentence of body as excerpt if no dedicated field
      const excerpt = description;

      posts.push({
        slug,
        title: fm.title ?? slug,
        description,
        excerpt,
        category: fm.category ?? "Field Notes",
        tags: (fm.tags ?? []) as readonly string[],
        publishedAt,
        author,
        cover: fm.cover,
        ogImage: fm.ogImage,
        readingTimeMinutes: fm.readingTimeMinutes ?? 6,
        bodyHtml,
      });
    } catch {
      // Skip malformed files silently
    }
  }

  _cache = posts;
  return posts;
}
