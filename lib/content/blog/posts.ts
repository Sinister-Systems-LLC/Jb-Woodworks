// Author: RKOJ-ELENO :: 2026-05-23
// JB Woodworks blog posts — zero-dep, pre-rendered HTML so we never need a
// markdown library in the runtime. Add a new post by appending to the array.
// Body HTML uses the same Tailwind utility classes that style the rest of
// the site (text-cream-50, em → gold italic, h2/h3 → display).

export type BlogPost = {
  slug: string;
  title: string;
  /** SEO meta description + OG description. Aim for ~155 chars. */
  description: string;
  /** Card excerpt on /blog (and any cross-page features). ~200 chars. */
  excerpt: string;
  category: string;
  tags: readonly string[];
  /** ISO date - first publish. */
  publishedAt: string;
  /** ISO date - latest edit. */
  updatedAt?: string;
  /** Author display name. Use "JB Woodworks" for in-house posts. */
  author: string;
  /** Cover image path (under /public). Falls back to a NB atmospheric. */
  cover?: string;
  /** Optional OG/Twitter card image (1200x630). Defaults to cover. */
  ogImage?: string;
  /** Estimated reading time in minutes (manual; ~225 wpm). */
  readingTimeMinutes: number;
  /** Pre-rendered HTML body. Wrap user prose in <p>...</p>. */
  bodyHtml: string;
};

export const blogPosts: readonly BlogPost[] = [
  {
    slug: "deck-materials-orlando-pressure-treated-cedar-composite",
    title: "Picking a deck material in Orlando — pressure-treated, cedar, or composite?",
    description:
      "Florida sun, summer rain, and salt-tinged air decide your deck more than any catalog. A real shop's take on PT pine, cedar, and Trex / TimberTech composite.",
    excerpt:
      "Florida sun and summer rain decide your deck more than the catalog does. Here is the honest breakdown of pressure-treated pine, cedar, and composite — cost, lifespan, look, and what we recommend in Orlando.",
    category: "Materials",
    tags: ["decks", "trex", "timbertech", "cedar", "pressure-treated", "orlando", "materials"],
    publishedAt: "2026-05-23",
    author: "JB Woodworks",
    cover: "/img/generated/services-accent.png",
    ogImage: "/img/generated/services-accent.png",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">Most deck quotes get won or lost on one decision — what the boards are made of. Here is the read we give every customer in Orlando, in the order they ask.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Pressure-treated southern yellow pine</h2>
<p>The cheapest option. Soaked with a copper-based preservative so termites and rot stay off it. In our climate a well-built PT deck lasts <em class="text-gold">12 to 18 years</em> before the boards start cupping or splintering enough to call it. You will need to re-seal every 2 to 3 years to keep the look.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> roughly $30-$45 / sq ft installed.</li>
  <li><strong class="text-white">Look:</strong> light green when fresh, weathers gray within 6 months unless you stain.</li>
  <li><strong class="text-white">Best for:</strong> rental properties, secondary patios, tight budgets where 12 to 15 years is fine.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Western red cedar</h2>
<p>Naturally rot-resistant from the tannins in the wood itself — no chemical bath required. Cedar smells like a cedar closet for the first six months. Same lifespan as PT in Florida if you keep up with the oil, but the surface stays softer underfoot and looks warmer.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> $45-$70 / sq ft installed. Roughly 1.5x the PT bill.</li>
  <li><strong class="text-white">Look:</strong> warm reddish-brown, weathers to silver-gray.</li>
  <li><strong class="text-white">Best for:</strong> pool decks where bare feet matter, primary entertaining areas, anywhere the look is the point.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Composite — Trex, TimberTech, Azek</h2>
<p>A wood-plastic blend (or pure PVC in the case of Azek). Zero rot, zero termites, zero re-staining. Looks like wood at three feet, like plastic at six inches. In Florida the killer feature is the <em class="text-gold">25 to 50 year warranty</em> — the manufacturer is betting their R&amp;D against your sun.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> $55-$90 / sq ft installed. About 2x the PT bill.</li>
  <li><strong class="text-white">Look:</strong> whatever you pick; the color is the color, forever.</li>
  <li><strong class="text-white">Best for:</strong> primary residences, anyone who wants to never touch the deck again, dock surfaces that take a beating from sun and water.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What we usually recommend</h2>
<p>In Orlando our default suggestion for a primary deck is <em class="text-gold">capped composite</em> — Trex Transcend or TimberTech AZEK Vintage. The first-year cost stings, but five years later when your neighbor is restaining their PT pine for the third time you will be hosing yours off with a garden sprayer.</p>
<p>If the budget will not stretch, we go to pressure-treated and tell you straight that re-seal is on the calendar every 2 years. We will not sell cedar for a backyard pad your dog drags across — it scratches. We will sell cedar all day for a pool deck.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Quick decision matrix</h2>
<p>If you want it cheap and you accept the maintenance, pick PT. If you want it warm to walk on and look custom, pick cedar. If you want to stop thinking about it, pick composite. Every quote we send lists all three so you can pick eyes-open.</p>

<p class="mt-8 text-cream-30 italic">Got a project in mind? Send us the rough square footage and a photo of the space — we will come back with material options and a real range, usually within one business day.</p>
`.trim()
  },
  {
    slug: "why-we-still-build-pool-tables-by-hand",
    title: "Why we still build pool tables by hand",
    description:
      "Slate, hardwood frame, hand-stretched felt — what goes into a tournament-quality pool table and why we have not shifted to factory imports.",
    excerpt:
      "Factory imports cost less. They also last about ten years before the slate shifts. Here is what a hand-built pool table actually involves, why we still do it, and what to ask any maker before you commit.",
    category: "Furniture",
    tags: ["pool-tables", "custom-furniture", "hardwoods", "process"],
    publishedAt: "2026-05-22",
    author: "JB Woodworks",
    cover: "/img/projects/Custom Pool Table/Resized_1000014068_733961905721315.jpg",
    ogImage: "/img/projects/Custom Pool Table/Resized_1000014068_733961905721315.jpg",
    readingTimeMinutes: 5,
    bodyHtml: `
<p class="lead">A factory-import pool table from a big-box retailer runs around $1,800. A hand-built table from a shop like ours starts at $7,500. We get asked, often, why.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">It starts with the slate</h2>
<p>The slate is the playing surface — three pieces of half-inch thick stone, ground flat to about <em class="text-gold">0.005 inch tolerance</em>. Factory tables ship MDF (compressed sawdust) painted to look like slate. MDF holds a ball roll for about three years. After that the table starts playing slow on one side and you cannot fix it without replacing the whole top.</p>
<p>We use Italian slate, leveled to the room at install. If your floor settles a quarter inch over a decade, we re-shim it. The slate itself outlasts the house.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The frame is structural, not decorative</h2>
<p>A 7-foot table with three slate panels weighs around 800 pounds before you put a ball on it. A factory table's frame is MDF wrapped in laminate — it sags. Three years in, the cushions are no longer at the right height because the rails have settled.</p>
<p>Our frames are red oak, walnut, or cherry — kiln-dried, mortise-and-tenon joinery, no metal screws in the load path. They do not settle.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The felt is hand-stretched</h2>
<p>Worsted wool, K-66 cushions, hand-stretched with a tucking tool so the surface is uniform corner to corner. A factory stapled felt has visible ripples within a year because the staple line shifts as the table flexes.</p>
<p>We re-felt customers' tables every 4-7 years depending on play volume. The slate and frame stay; only the felt is consumable.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What to ask any builder</h2>
<ul>
  <li><strong class="text-white">"Real slate or MDF?"</strong> The honest answer is on the receipt.</li>
  <li><strong class="text-white">"Joinery type?"</strong> Mortise-and-tenon outlasts pocket screws by decades.</li>
  <li><strong class="text-white">"Cushion specification?"</strong> K-66 is the tournament standard. K-55 is the home spec. K-44 is the toy spec.</li>
  <li><strong class="text-white">"Felt brand?"</strong> Simonis or Championship if you care about play. Anything else is decorative.</li>
  <li><strong class="text-white">"Do you re-level on site?"</strong> If they ship it pre-assembled, the answer is "no" and your room will tell on them.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Worth the cost?</h2>
<p>It is, if you actually play. A hand-built table costs <em class="text-gold">about 4x as much up front</em> and lasts <em class="text-gold">5 to 10x longer</em>. On a per-year basis the factory table is more expensive — you just pay in installments.</p>
<p>If you want a table for the look and your friends will not know the difference, a factory import is fine. Just go in knowing the slate is fake.</p>

<p class="mt-8 text-cream-30 italic">Thinking about a custom table? Tell us the room dimensions and the look you want — oak vs. walnut vs. cherry, leather pockets or shield, traditional or art-deco rails. We can usually give you a real number within a day.</p>
`.trim()
  }
] as const;

export function getBlogPost(slug: string): BlogPost | undefined {
  return blogPosts.find((p) => p.slug === slug);
}

/** Ordered most-recent first */
export function blogPostsByDate(): BlogPost[] {
  return [...blogPosts].sort((a, b) => b.publishedAt.localeCompare(a.publishedAt));
}
