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
    slug: "outdoor-furniture-wood-florida-humidity",
    title: "The best wood for outdoor furniture in Florida humidity",
    description:
      "Florida humidity destroys most outdoor furniture in 3-5 years. Here is which woods actually survive Orlando's climate, ranked by lifespan and look.",
    excerpt:
      "Big-box patio sets fail in 3 years here. The wood matters more than the brand. Here is a real-world ranking of teak, ipe, cypress, cedar, and white oak for Florida outdoor furniture.",
    category: "Materials",
    tags: ["outdoor-furniture", "teak", "ipe", "cypress", "cedar", "white-oak", "florida", "humidity"],
    publishedAt: "2026-05-24",
    author: "JB Woodworks",
    cover: "/img/projects/Custom Furniture/IMG_1248_00.jpg",
    ogImage: "/img/projects/Custom Furniture/IMG_1248_00.jpg",
    readingTimeMinutes: 7,
    bodyHtml: `
<p class="lead">In Florida the question is not "what wood looks good?" — it is "what wood is still here in 2035?" Humidity, UV, and salt air pick the winners. Here is the honest ranking we give every outdoor-furniture customer in Orlando.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">1. Teak — the obvious answer</h2>
<p>Teak (real Burmese teak, not "Asian teak" which is a different species) is naturally oily, which means it shrugs off water without sealing. Outdoor teak furniture in Florida lasts <em class="text-gold">30 to 50 years</em> with zero maintenance. Left alone, it weathers to a soft silver-gray. Oiled annually, it stays the warm honey color from day one.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> the highest of any common outdoor wood. A teak dining table seats 6 for $3,500-$6,000 in our shop.</li>
  <li><strong class="text-white">Look:</strong> golden brown new, silver-gray weathered. Both look intentional.</li>
  <li><strong class="text-white">Best for:</strong> furniture you want to pass to your kids. The buy-once option.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">2. Ipe — the tropical hardwood underdog</h2>
<p>Brazilian ironwood. Twice as dense as oak. It is so heavy it does not float. Termites do not eat it. UV does not bleach it. In Florida ipe outdoor furniture realistically lasts <em class="text-gold">40 to 75 years</em>. The catch: it is brutal to work with — dulls every blade we own — so the labor cost is high.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> roughly 0.75x teak in materials, but 1.2x in labor. Net: comparable to teak.</li>
  <li><strong class="text-white">Look:</strong> dark chocolate, often with subtle grain figure. Weathers gray like teak.</li>
  <li><strong class="text-white">Best for:</strong> dock seating, pool surrounds, any piece that has to fight standing water.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">3. White oak — the value pick</h2>
<p>Northern white oak (not red oak — red oak rots in Florida). The closed grain keeps water out, and a polyurethane spar varnish every 3-5 years takes care of UV. <em class="text-gold">15 to 25 years</em> of life with that maintenance schedule.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> about half of teak. A 6-seat dining table runs $1,800-$2,800.</li>
  <li><strong class="text-white">Look:</strong> pale tan when new, golden honey under oil finish, weathers to silver-gray if left bare.</li>
  <li><strong class="text-white">Best for:</strong> covered-patio dining sets where you can re-coat every few years.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">4. Western red cedar — light + soft</h2>
<p>Cedar is light enough to drag across a lawn one-handed, which is a real feature for benches and Adirondacks. <em class="text-gold">10 to 15 years</em> outdoor life in Orlando without re-oiling, longer if you keep up with an oil coat every two years.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> roughly 0.5x white oak. A cedar Adirondack runs $400-$700.</li>
  <li><strong class="text-white">Look:</strong> reddish-pink new, silver-gray weathered. Smells like a cedar closet for the first year.</li>
  <li><strong class="text-white">Best for:</strong> casual seating, garden benches, planter boxes.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">5. Bald cypress — Florida's native answer</h2>
<p>Cypress is what Florida originally built itself with — it grows in swamps so it is genuinely rot-resistant. <em class="text-gold">20 to 30 years</em> outdoor life with no chemical treatment. Becoming harder to source as the old-growth stands run out, but new-growth cypress is still real cypress; the lifespan is just a touch shorter.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> similar to white oak.</li>
  <li><strong class="text-white">Look:</strong> pale yellow new, weathers to a warm gray with reddish undertones.</li>
  <li><strong class="text-white">Best for:</strong> Florida-vernacular pieces — porch swings, swamp-house furniture, anything that wants the regional vibe.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What never to use outdoors in Florida</h2>
<p>Pine (any species, untreated), red oak, soft maple, poplar, walnut. Walnut in particular looks great in the showroom and disintegrates within 3 years on a porch. The store furniture you regret buying is almost always one of these woods with a thin veneer.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Our default recommendation</h2>
<p>For dining + entertaining furniture you actually use, we lead with <em class="text-gold">white oak under a marine-grade spar varnish</em> — the cost-to-lifespan ratio is unbeatable. For pieces that sit in standing water (dock benches, planters near a sprinkler) we go ipe. For the "buy it once" customer, teak. We will quote all three so you can pick eyes-open.</p>

<p class="mt-8 text-cream-30 italic">Send us the rooms and the pieces you are thinking about — we will come back with a wood-species recommendation and a real cost range, usually within one business day.</p>
`.trim()
  },
  {
    slug: "boat-dock-pilings-wood-concrete-composite",
    title: "Boat dock pilings: wood vs. concrete vs. composite — what we use on Florida lakes",
    description:
      "Pilings are 70% of what makes a dock last. Here is the real-world breakdown of pressure-treated, concrete, and composite pilings on Orlando-area lakes.",
    excerpt:
      "The pilings under your dock decide whether it is still here in 30 years. Here is what we have learned installing on Conway, Butler, the Chain of Lakes — and which option is worth the money.",
    category: "Boat Docks",
    tags: ["boat-docks", "pilings", "florida-lakes", "marine-construction", "orlando"],
    publishedAt: "2026-05-21",
    author: "JB Woodworks",
    cover: "/img/projects/Boat Dock/IMG_1577.jpg",
    ogImage: "/img/projects/Boat Dock/IMG_1577.jpg",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">A dock is a deck that lives in water. The piling is the thing fighting that water 24/7. Pick the piling wrong and the deck above it is just a delivery system for repair calls. Here is what we use on Orlando-area lakes.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Pressure-treated southern yellow pine — the default</h2>
<p>Treated to .60 CCA retention (the marine-grade spec), 8-10 inch diameter, driven 8-12 feet into the lake bed depending on what we hit. Around <em class="text-gold">25 to 35 years</em> of useful life on a fresh-water lake before the section between waterline and mud line starts to lose meat.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> the cheapest option. Roughly $150-$250 per piling installed.</li>
  <li><strong class="text-white">Look:</strong> green when fresh, weathers brown then gray.</li>
  <li><strong class="text-white">Watch-out:</strong> the .40 retention pine you can buy at a big-box lumber yard is yard-grade, not marine-grade. Same color, very different lifespan. We only use marine-grade.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Concrete — the buy-once option</h2>
<p>Pre-cast concrete pilings, octagonal cross-section, 10-12 inch face. Driven the same depth as wood. <em class="text-gold">75+ years</em> of service life. The only thing that takes them out is a barge hit.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> roughly 2.5x the wood bill. $400-$650 per piling installed.</li>
  <li><strong class="text-white">Look:</strong> gray, industrial. We can dress the cap with a wood collar so the visible portion looks like the deck above.</li>
  <li><strong class="text-white">Best for:</strong> primary residences where the dock is part of the property value, anywhere you want the "and you never touch it again" answer.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Composite (fiberglass / HDPE) — the lightweight specialist</h2>
<p>Hollow fiberglass or solid HDPE pilings. Same lifespan as concrete (50-75 years) at about 60% the weight, which matters when access is tight and a piling truck cannot get to the install site. Used to cost roughly 3x wood; the gap is closing.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> $350-$550 per piling installed. Closer to concrete than to wood now.</li>
  <li><strong class="text-white">Look:</strong> available in wood-grain wrap or smooth charcoal.</li>
  <li><strong class="text-white">Best for:</strong> shoreline installs with no truck access, eco-sensitive areas that prohibit CCA-treated wood, owners who want a 50+ year structure.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What we actually install</h2>
<p>For most residential docks on Conway, Butler, the Chain of Lakes, we lead with <em class="text-gold">marine-grade pressure-treated</em>. 30 years is more than long enough that the deck surface will need replacement before the pilings do, and the cost difference funds a better deck and a roof.</p>
<p>For lakefront homes where the dock is part of the listing price, we lead with concrete. We have re-decked owner-built concrete-piling docks that were installed in the 1970s and the pilings are still straight.</p>
<p>We do not generally recommend "untreated cypress" or "marine plywood" pilings that some pre-fab dock kits ship with — neither holds up in our water table.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Five things to verify in any dock quote</h2>
<ul>
  <li><strong class="text-white">CCA retention rating</strong> (.60 for marine, .40 for yard).</li>
  <li><strong class="text-white">Drive depth.</strong> 8-12 feet is normal for our lake beds. Anything less is a red flag.</li>
  <li><strong class="text-white">Hardware grade.</strong> Hot-dip galvanized or 316 stainless. Electroplated rusts in 2 years.</li>
  <li><strong class="text-white">Permits.</strong> St. Johns River Water Management District plus county. Required on every Orlando-area lake.</li>
  <li><strong class="text-white">Warranty terms.</strong> What is covered, for how long, transferable to the next owner?</li>
</ul>

<p class="mt-8 text-cream-30 italic">Considering a new dock or replacing pilings on an existing one? Send us the lake, the rough length, and a photo from the shore. We will come back with permit guidance and a real quote, usually within two business days.</p>
`.trim()
  },
  {
    slug: "pergola-design-styles-florida-sun",
    title: "Pergola design styles for Florida sun (and which actually shade you)",
    description:
      "Open-top pergolas look pretty in catalogs. In Orlando sun they shade nothing at 1 pm. Here is which pergola design actually keeps the heat off in Florida.",
    excerpt:
      "Most pergolas look great on Pinterest and shade nothing during peak Orlando sun. Here is the breakdown of beam spacing, louvered tops, slat angle, and shade percentage — so the pergola you buy actually works.",
    category: "Pergolas",
    tags: ["pergolas", "outdoor-living", "shade", "florida", "design", "orlando"],
    publishedAt: "2026-05-20",
    author: "JB Woodworks",
    cover: "/img/projects/Pergola/IMG_0037.jpg",
    ogImage: "/img/projects/Pergola/IMG_0037.jpg",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">A pergola in a magazine looks fine because the photographer waited until 5 pm. In Orlando, 1 pm is the test. Here is how we design pergolas that actually shade — and which styles only look like they do.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The shade math nobody mentions</h2>
<p>Sun angle in Orlando peaks around 84 degrees in June and bottoms around 38 degrees in December. A pergola with open spacing on top shades the ground for about <em class="text-gold">15 minutes a day</em> in summer — when the sun is directly overhead. The other 11 hours, light comes in at an angle and slips between the beams.</p>
<p>To actually shade, the top either needs to be tight (high coverage), oriented to the sun path (angled slats), or operable (louvers you tilt).</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Style 1: Traditional open-top — pretty, not shade</h2>
<p>The classic pergola — square posts, beams every 16-24 inches, rafters running perpendicular. Looks great. Casts striped shadows that move with the sun. <em class="text-gold">Shade percentage: ~25%.</em></p>
<p>Best use: an architectural feature where you actually want dappled light, like over a planter bed or a pathway. Not where you want to sit at noon.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Style 2: Tight-slat pergola — real shade, fixed</h2>
<p>Same form factor but slat spacing under 4 inches and slats angled 15-25 degrees against the typical sun path. <em class="text-gold">Shade percentage: 65-80%.</em></p>
<p>Best use: dining patios where the table sits in one place and you want consistent shade during meal times. Fixed orientation means you commit to one sun direction — we typically angle for 12-3 pm coverage since that is when people actually use the patio.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Style 3: Louvered roof — adjustable, the modern answer</h2>
<p>Aluminum or wood louvers that pivot. Open in the morning, close at noon. Open again at 4 pm when you want golden hour to come through. <em class="text-gold">Shade percentage: 5-100% on demand.</em></p>
<p>Cost is real — a louvered pergola runs 2-3x a traditional one. Worth it if the patio is a daily-use space. We typically pair them with integrated LED + a fan beam so the whole structure is multi-mode (shade + light + air movement).</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Style 4: Solid roof + skylight — pergola that lies about being one</h2>
<p>Technically not a pergola, but it solves the same problem. A solid roof (matching the house) over the patio, with one or two skylights to keep it from feeling cave-like. <em class="text-gold">Shade percentage: 95%.</em></p>
<p>You lose the "open-air" feeling but gain a usable outdoor room during summer storms. We build a lot of these for clients who tried a traditional pergola first and gave up on it.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Hurricane considerations</h2>
<p>Anything we build in Orlando is engineered to <em class="text-gold">130 mph wind load minimum</em> — that is the Florida Building Code requirement for our zone. The post sizing, footing depth (24-36 inches with a concrete pier), and hurricane-clip hardware all come out of that number.</p>
<p>Some pre-fab kits sold online are rated for 80 mph. They are illegal to install in Florida. If a contractor offers to assemble one for you, ask for the permit. If they cannot pull one, walk.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Cost ranges (Orlando, 2026)</h2>
<ul>
  <li><strong class="text-white">Traditional open-top pergola, 12&apos;x14&apos;:</strong> $6,500-$11,000 in cedar; $9,000-$15,000 in white oak.</li>
  <li><strong class="text-white">Tight-slat angled, same size:</strong> +$2,500-$4,000 over traditional.</li>
  <li><strong class="text-white">Louvered, same size:</strong> $22,000-$38,000 depending on motor + integration.</li>
  <li><strong class="text-white">Solid roof + skylight, same size:</strong> $14,000-$24,000.</li>
</ul>

<p class="mt-8 text-cream-30 italic">Want help picking the right style? Tell us where the patio faces (north / south / east / west), when you actually use it (mornings? evenings?), and what you usually do out there. We will steer you to the version that fits your day.</p>
`.trim()
  },
  {
    slug: "trex-vs-timbertech-vs-azek-composite-deck-2026",
    title: "Trex vs. TimberTech vs. Azek: which composite decking wins in Florida (2026)",
    description:
      "Three top composite deck brands, head-to-head: heat retention, warranty fine print, fade resistance, and what we actually install in Orlando.",
    excerpt:
      "All three claim 25-year warranties. Florida sun separates them fast. Here is what each brand actually delivers on heat retention, color fade, and the warranty exclusions you should read first.",
    category: "Materials",
    tags: ["decks", "trex", "timbertech", "azek", "composite", "comparison", "orlando"],
    publishedAt: "2026-05-19",
    author: "JB Woodworks",
    cover: "/img/projects/Deck/IMG_1649.jpg",
    ogImage: "/img/projects/Deck/IMG_1649.jpg",
    readingTimeMinutes: 7,
    bodyHtml: `
<p class="lead">Trex, TimberTech, and Azek all sell composite decking with 25-50 year warranties. The brochures look identical. Five years in our climate, they are not. Here is the side-by-side we use when a customer asks us to pick.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What "composite" actually means</h2>
<p>Trex and TimberTech AZEK Reserve / Edge are <em class="text-gold">wood-plastic composite</em> — recycled HDPE plus wood flour, capped with a PVC shell. Azek (and AZEK Vintage / Cortex) is <em class="text-gold">cellular PVC</em> — no wood content at all, just structured plastic. The difference matters in Florida because wood content holds moisture and the plastic shell either holds up to UV or it does not.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Heat retention — the Florida killer</h2>
<p>Dark composite gets hot. We have measured <em class="text-gold">158°F</em> on a black Trex board at 2 pm in July. The same Azek board next to it: 138°F. Lighter colors close the gap; in light gray all three brands come in around 115-125°F.</p>
<ul>
  <li><strong class="text-white">Coolest in dark colors:</strong> Azek (pure PVC reflects more IR).</li>
  <li><strong class="text-white">Hottest in dark colors:</strong> Trex Transcend (the wood flour absorbs heat).</li>
  <li><strong class="text-white">In light colors:</strong> all three are walkable barefoot.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Color fade — what the warranty does not cover</h2>
<p>All three warrant against "significant fade" — and define "significant" as a Delta-E shift greater than 5 over the warranty period. Most customers notice fade at Delta-E 2-3, which is well below the warranty trigger. Translation: visible fading does not mean you get a replacement.</p>
<p>In our 5-year side-by-side on a south-facing Orlando deck, the rank order:</p>
<ul>
  <li><strong class="text-white">Best fade resistance:</strong> Azek Vintage (no wood content, deepest UV inhibitor package).</li>
  <li><strong class="text-white">Middle:</strong> TimberTech AZEK Reserve (light wood content, full PVC cap).</li>
  <li><strong class="text-white">Worst:</strong> Trex Enhance (entry-level Trex line). Trex Transcend is on par with TimberTech.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Scratch + dent resistance</h2>
<p>Dragging a patio chair across composite leaves a mark on all three brands. The mark is most visible on Azek (because the color is uniform through; the scratch shows depth). The wood-composite brands hide scratches slightly better.</p>
<p>If you have dogs and they drag toys across the deck, lean composite. If you have heavy furniture you slide around for cleaning, Azek wins on look.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Warranty fine print</h2>
<p>All three offer 25-50 year limited warranties on the material. Watch for:</p>
<ul>
  <li><strong class="text-white">Labor.</strong> Trex covers labor for the first 10 years on Transcend. TimberTech is product-only. Azek covers labor for the first 5.</li>
  <li><strong class="text-white">Transferable.</strong> Trex transfers to a second owner once. TimberTech transfers once. Azek does not transfer.</li>
  <li><strong class="text-white">Installation requirement.</strong> All three require approved fastener systems (hidden clips). Use a face screw and the warranty is void.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Cost (installed, Orlando 2026)</h2>
<ul>
  <li><strong class="text-white">Trex Enhance:</strong> $55-$65 / sq ft. Entry composite.</li>
  <li><strong class="text-white">Trex Transcend:</strong> $70-$85 / sq ft. Their flagship.</li>
  <li><strong class="text-white">TimberTech AZEK Reserve:</strong> $75-$90 / sq ft.</li>
  <li><strong class="text-white">Azek Vintage:</strong> $85-$100 / sq ft. The premium tier.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What we actually install</h2>
<p>Our default for an Orlando primary deck is <em class="text-gold">TimberTech AZEK Reserve in a light or medium color</em>. Best fade resistance for the price, walkable barefoot in summer, hidden clip system that hides the fasteners cleanly. If a customer wants the absolute best, we go Azek Vintage. If the budget is tight, Trex Transcend over Trex Enhance — Enhance is sold at warehouse stores and the cap is thinner.</p>

<p class="mt-8 text-cream-30 italic">Pick the wrong composite and you live with the heat / fade / scratch profile for 30 years. We are happy to bring samples to your house so you can put them in the actual sun your deck will see. Just ask.</p>
`.trim()
  },
  {
    slug: "hurricane-rated-outdoor-builds-florida",
    title: "Hurricane-rated outdoor builds in Florida: what changes (and what does not)",
    description:
      "Florida's building code adds real engineering to anything outdoors. Here is what hurricane rating actually means for your deck, pergola, or boat dock.",
    excerpt:
      "Hurricane code is not a marketing word. It changes post sizing, hardware grade, footing depth, and clip count. Here is what the Florida Building Code requires — and what shortcuts cost you in a real storm.",
    category: "Process",
    tags: ["hurricane", "florida-building-code", "engineering", "decks", "pergolas", "permits"],
    publishedAt: "2026-05-17",
    author: "JB Woodworks",
    cover: "/img/generated/process-bench.png",
    ogImage: "/img/generated/process-bench.png",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">Florida Building Code is not optional and it is not gentle. For outdoor builds in Orange and Seminole counties, the wind-load minimum is <em class="text-gold">130 mph</em>. Here is what that number changes in your project, and what it should change in your quote.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Post sizing — the most common shortcut</h2>
<p>A backyard pergola in a state without a hurricane code uses 4x4 posts. Florida code on a 12x14 pergola requires <em class="text-gold">6x6 minimum</em>, and we typically go 8x8 for anything spanning further than 12 feet. The extra material is 8-12% of the total bill; the structural difference is the difference between "still standing" and "now decorating the next yard over" after a Cat 2.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Footing depth + concrete spec</h2>
<p>Code minimum is 24 inches deep + below frost line (irrelevant here) + bell-bottom flare to spread load. For posts taller than 8 feet we go to 36 inches with a 12-inch sonotube + #4 rebar cage. Concrete is 3,000 PSI minimum, 4,000 PSI for anything load-bearing on a slope or near water.</p>
<p>A "Quikrete bag, mix it dry in the hole, hose it down" install is what gets pergolas in YouTube videos. It is not legal here and the inspector will fail it.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Hardware — the cheap mistake</h2>
<p>The code calls for Simpson Strong-Tie or equivalent hurricane straps + post bases at every load-path joint. Galvanized minimum, <em class="text-gold">316 stainless steel</em> within 1 mile of salt water or on any boat dock. Electroplated hardware looks the same and rusts in 2 years.</p>
<p>Roughly $200-$400 of hardware on a typical deck or pergola. We have replaced decks where the previous builder saved $150 on hardware and the homeowner had to spend $9,000 fixing the deck-to-house ledger connection after Hurricane Ian.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Ledger board — where decks fail</h2>
<p>The ledger board attaches the deck to the house. In a hurricane this connection takes both wind uplift (lifting the deck) and wind pull (yanking it sideways). Code requires <em class="text-gold">5/8 inch through-bolts every 16 inches</em>, lag screws are not acceptable, and flashing must be Z-flashed under the house siding so water cannot get behind it.</p>
<p>A surprising number of decks built before 2000 use lag screws straight through the siding into the rim joist with no flashing. Those are the decks that come off the house in storms.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Permit pull — required, not optional</h2>
<p>Orange County requires a permit for any structure over 100 sq ft, any pergola, any dock, any deck attached to a house. Permit pulls in our area run $250-$650 plus the engineering stamp ($400-$800 if a structural engineer needs to sign).</p>
<p>"Permit-free" is contractor-speak for "uninsured." A real shop pulls the permit. We pull every permit and include it in the quote line item.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Insurance + resale</h2>
<p>Two things to know if you skip the permit:</p>
<ul>
  <li><strong class="text-white">Homeowner&apos;s insurance.</strong> Unpermitted structures are often excluded from coverage. A tree falls on an unpermitted deck and you pay out of pocket.</li>
  <li><strong class="text-white">Resale.</strong> Title companies pull permit history during closing. Unpermitted structures show up as a defect and either need to be removed, retroactively permitted (often impossible), or the sale price gets renegotiated.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What hurricane rating costs vs. saves</h2>
<p>On a typical $25,000 deck project the code-compliant build adds roughly $2,000-$3,500 over a "lowest-bid" non-permitted version. Over 30 years of ownership including one major hurricane event (statistically nearly certain in our area), the math works out comfortably in favor of doing it right the first time.</p>

<p class="mt-8 text-cream-30 italic">Every quote we send breaks out the structural line items so you can see exactly what you are paying for. If another shop is significantly cheaper, ask them to do the same. The line items will tell you the story.</p>
`.trim()
  },
  {
    slug: "hardwood-floor-refinish-vs-replace",
    title: "Hardwood floor refinishing in Orlando: when to refinish vs. replace",
    description:
      "Old hardwood can usually be saved. Sometimes it cannot. Here is how to tell which side of the line your floor is on — and what each option costs.",
    excerpt:
      "Refinishing saves 60-70% over replacement. But not every floor is a refinish candidate. Here is how we evaluate floors in Orlando homes, and what we see week to week that surprises homeowners.",
    category: "Floors",
    tags: ["hardwood-floors", "refinishing", "renovation", "orlando", "maintenance"],
    publishedAt: "2026-05-15",
    author: "JB Woodworks",
    cover: "/img/generated/grain-texture.png",
    ogImage: "/img/generated/grain-texture.png",
    readingTimeMinutes: 5,
    bodyHtml: `
<p class="lead">Most hardwood floors can be refinished 4-6 times in their life. Once they are out of meat above the tongue, they are out. Here is how we tell whether your floor is a refinish or a replacement before we start sanding.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">First check: what kind of floor is it?</h2>
<p>The single biggest factor — and the one most homeowners do not know about their own floor — is whether it is <em class="text-gold">solid hardwood</em> or <em class="text-gold">engineered hardwood</em>. Solid is one species, 3/4 inch thick, can be refinished 4-6 times. Engineered is a hardwood veneer (1-4 mm) over a plywood core; depending on the veneer thickness it can be refinished 0-2 times.</p>
<p>Pull a vent register. Look at the cross-section of the board at the edge of the duct opening. If you see plywood laminations underneath the top layer, it is engineered. If it is uniform wood all the way down, it is solid.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Solid hardwood — usually refinish</h2>
<p>Even with deep dog scratches, water rings, and 30 years of UV bleach, a solid floor with at least 3/16 inch above the tongue is a refinish candidate. We sand down to bare wood, fill gouges as needed, and recoat. Cost in Orlando: <em class="text-gold">$3.50-$5.50 per sq ft</em>. A 1,200 sq ft house runs $4,200-$6,600 for a full refinish.</p>
<p>Replacement cost for the same area in matching new solid hardwood: $12,000-$18,000 installed. The math is not close.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Engineered hardwood — usually replace</h2>
<p>If your engineered floor has a thin veneer (2 mm or less, which is most pre-finished engineered installed since 2010), it is not really refinishable. We can do a light screen-and-recoat to refresh the finish, but the underlying wood is the underlying wood; you cannot sand it.</p>
<p>If the veneer is 4 mm+ (typical of pre-2005 engineered or the high-end stuff today), one refinish is possible. After that, replace.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Water damage — the make-or-break test</h2>
<p>Cupping (boards arched up at the edges) and crowning (boards arched up in the middle) come from moisture. Mild cupping flattens after a few weeks once the source is fixed and the floor dries — we then refinish normally. Severe cupping or any black staining means the wood is compromised; replacement of the affected area is the only fix, and we have to color-match the new boards to the surrounding sanded floor.</p>

<h2 class="font-density text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Pet stains — the hidden problem</h2>
<p>Cat urine in particular soaks deep and turns wood black. Sanding will not remove it because the stain is in the wood, not on it. We can sometimes bleach pet stains out with oxalic acid; for severe cases the boards need to be replaced.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Process timeline</h2>
<p>A typical 1,200 sq ft refinish takes 4-5 days:</p>
<ul>
  <li><strong class="text-white">Day 1:</strong> coarse sand (36-grit), then progressively finer (60, 80, 100).</li>
  <li><strong class="text-white">Day 2:</strong> edging (around the perimeter where the drum sander does not reach), corner sand, vacuum.</li>
  <li><strong class="text-white">Day 3:</strong> stain (if changing color) + first poly coat.</li>
  <li><strong class="text-white">Day 4-5:</strong> second + third poly coat, light buff between.</li>
</ul>
<p>You can usually walk on the floor in socks 24 hours after the last coat. Furniture goes back 72 hours after. Rugs at 30 days (rugs trap solvents and can leave a haze).</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Stain colors — what holds up in Florida</h2>
<p>Light + medium tones (provincial, golden oak, natural) hold their look the longest because they hide UV-bleaching better. Dark espresso and ebony stains look great new but start showing scratches and sun-fade within 18 months in a Florida living room with east-facing windows. If you want dark, plan on a refinish every 5-7 years; if you want set-and-forget, go natural or provincial.</p>

<p class="mt-8 text-cream-30 italic">Considering a refinish? We do free in-home evaluations in the Orlando area — pull a vent register before we come and we can confirm solid vs. engineered in 30 seconds.</p>
`.trim()
  },
  {
    slug: "front-porch-curb-appeal-20-year",
    title: "Front porch upgrades that last 20+ years (and which ones do not)",
    description:
      "Front porches are the curb-appeal lever. Most upgrades fall apart in 5 years. Here are the ones that survive a decade-plus in Orlando weather.",
    excerpt:
      "A great front porch sells the whole house. A bad one signals deferred maintenance from the curb. Here is what we have learned about which materials, finishes, and details hold up — and which do not.",
    category: "Front Porches",
    tags: ["front-porch", "curb-appeal", "renovation", "orlando", "exterior"],
    publishedAt: "2026-05-13",
    author: "JB Woodworks",
    cover: "/img/projects/Front Porch/IMG_1236.jpg",
    ogImage: "/img/projects/Front Porch/IMG_1236.jpg",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">The front porch is the first thing your guests, your delivery driver, and your real-estate appraiser see. It is also the part of the exterior that gets the worst combination of sun, rain, and foot traffic. Here is what holds up over a decade in Orlando — and what to skip.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Decking — the surface you stand on</h2>
<p>For a covered front porch, our default is <em class="text-gold">tongue-and-groove fir or southern yellow pine</em>, painted with a porch enamel. Holds up 15-20 years before recoating. Looks intentional in a way that composite does not on a porch (composite reads as deck; T&amp;G painted reads as porch).</p>
<p>For uncovered or partly-exposed porches we lean composite — same reasoning as a deck.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Columns + posts — where most porches fail</h2>
<p>Standard 4x4 wood posts rot at the base where they meet the floor — water wicks up the end grain. Within 5-8 years of install they are pulpy. We use two solutions:</p>
<ul>
  <li><strong class="text-white">PVC column wraps over 6x6 PT cores.</strong> The structural post is pressure-treated; the PVC wrap is decorative + waterproof. Lasts indefinitely.</li>
  <li><strong class="text-white">Solid cellular PVC columns (Endura-Stone, Permacast).</strong> No wood inside. Higher cost but no rot risk.</li>
</ul>
<p>Skip the hollow plastic "fluted columns" from big-box stores — they crack in UV and cannot support real load.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Railings — the legal piece</h2>
<p>Anything more than 30 inches off the ground requires a railing in Florida — 36 inch minimum height, 4-inch maximum baluster spacing. The two materials that actually last:</p>
<ul>
  <li><strong class="text-white">Powder-coated aluminum.</strong> 25+ year life, available in any color, never needs maintenance. Our default.</li>
  <li><strong class="text-white">PVC-wrapped wood (Westbury, etc).</strong> Same lifespan, looks more traditional. Higher cost.</li>
</ul>
<p>Plain wood balusters work but expect to repaint every 3-4 years. Wrought iron looks great in catalogs and rusts at every weld within 5 years here.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Ceiling — the detail everyone forgets</h2>
<p>If your front porch has a ceiling, it is the part that defines whether it reads "intentional" or "deferred." Three options that hold up:</p>
<ul>
  <li><strong class="text-white">Bead-board PVC.</strong> $-$$. Looks like painted wood. Will not rot.</li>
  <li><strong class="text-white">Tongue-and-groove cypress, oiled.</strong> $$$. Warmest look. 20+ years if oiled every 5 years.</li>
  <li><strong class="text-white">Painted T&amp;G fir.</strong> $$. Classic look. Repaint every 8-10 years.</li>
</ul>
<p>Southern tradition: paint the ceiling <em class="text-gold">haint blue</em>. It is a soft sky color said to keep evil spirits (and wasps) away. The wasps part is true — the color confuses them so they do not build nests on it.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Lighting — the multiplier</h2>
<p>One overhead fixture is the bare minimum. The porches that look intentional have <em class="text-gold">three sources of light</em>:</p>
<ul>
  <li>A centered overhead fixture (lantern style or flush-mount).</li>
  <li>Wall sconces flanking the door.</li>
  <li>Either string lighting along the ceiling perimeter or low-voltage uplights on the columns.</li>
</ul>
<p>All on a dimmer. The porch gets used at twilight more than any other time, and dim-warm is much more inviting than full-bright.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The "small" details that compound</h2>
<ul>
  <li><strong class="text-white">House numbers.</strong> 4-inch minimum, visible from the street. Brass or matte black ages well.</li>
  <li><strong class="text-white">Mailbox or mail slot.</strong> If wall-mounted, secure it to a stud, not the siding.</li>
  <li><strong class="text-white">Door hardware.</strong> Solid brass (will patina) or oil-rubbed bronze (will hold its finish). Powder-coated steel chips.</li>
  <li><strong class="text-white">Kick plate.</strong> Saves the bottom 8 inches of the door from luggage and shoe scuffs.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Budget orientation (Orlando, 2026)</h2>
<ul>
  <li><strong class="text-white">Refresh existing porch (paint, new railings, light fixture):</strong> $2,500-$6,000.</li>
  <li><strong class="text-white">Replace decking + railings + columns, same footprint:</strong> $8,000-$16,000.</li>
  <li><strong class="text-white">Build a new covered porch on existing slab:</strong> $18,000-$32,000.</li>
  <li><strong class="text-white">Tear down and rebuild from footings:</strong> $25,000-$55,000.</li>
</ul>

<p class="mt-8 text-cream-30 italic">Want curb-appeal advice specific to your house? Send us 3-4 photos (front straight-on, both side angles, a close-up of the existing porch). We will reply with a punch list and a budget range, usually within one business day.</p>
`.trim()
  },
  {
    slug: "custom-kitchen-island-cost-process-timing",
    title: "Custom kitchen islands: real cost, real timing, what we build",
    description:
      "Kitchen islands have a 5x cost spread between off-the-shelf and built-in-place. Here is what each tier actually delivers and what drives the price.",
    excerpt:
      "Same kitchen, two islands, $4,500 vs. $24,000. Where does that 5x go? Here is what each tier of custom island includes, how long it takes, and which features are worth the upcharge.",
    category: "Furniture",
    tags: ["kitchen-island", "custom-furniture", "cabinetry", "interior", "orlando"],
    publishedAt: "2026-05-11",
    author: "JB Woodworks",
    cover: "/img/projects/Custom Furniture/IMG_1248_00.jpg",
    ogImage: "/img/projects/Custom Furniture/IMG_1248_00.jpg",
    readingTimeMinutes: 7,
    bodyHtml: `
<p class="lead">"Custom kitchen island" covers a spread from $4,500 to $40,000. Here is what each tier actually includes, what features drive the upcharge, and which ones we tell our customers to skip.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Tier 1: Standalone furniture island — $4,500 to $9,000</h2>
<p>Built like a piece of furniture in the shop, delivered as one unit, sits on the floor (not bolted to it). Has feet or legs you can see under it. Stainless top or butcher block. Maybe one outlet if you ran power before install.</p>
<ul>
  <li><strong class="text-white">Best for:</strong> renters, kitchens where you might want to rearrange, smaller homes.</li>
  <li><strong class="text-white">Build time:</strong> 4-6 weeks shop, 2 hour install.</li>
  <li><strong class="text-white">Watch-outs:</strong> not a structural part of the kitchen — does not anchor a range or sink.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Tier 2: Built-in cabinetry island — $9,000 to $18,000</h2>
<p>Cabinet boxes meet the floor with a toe-kick (like the rest of the kitchen), bolted down, plumbed for power and water if needed. Quartz, soapstone, or butcher-block top. Includes drawers, a trash pullout, often a beverage drawer or wine rack.</p>
<p>This is the tier most homeowners actually want. It looks like part of the kitchen, not an add-on. Permanent, but you can specify it for the kitchen you have, not a generic size.</p>
<ul>
  <li><strong class="text-white">Best for:</strong> primary residences, anyone re-doing a kitchen.</li>
  <li><strong class="text-white">Build time:</strong> 6-8 weeks shop, 1-2 day install.</li>
  <li><strong class="text-white">Common upcharges:</strong> hidden hood for cooktop ($1,500-$3,000), undercounter wine fridge ($800-$2,000), pop-up outlets ($300-$600 each).</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Tier 3: Statement / waterfall island — $18,000 to $40,000</h2>
<p>The kind of island you see in design magazines. Waterfall stone (the countertop turns down on the ends), full-height storage, integrated appliance bay, fluted or paneled exterior wrap. Usually two-tone — different finish from the perimeter cabinets — to signal that the island is the centerpiece.</p>
<ul>
  <li><strong class="text-white">Best for:</strong> open-plan homes where the island is also the visual anchor from the living room, primary residences expected to be lived in 10+ years.</li>
  <li><strong class="text-white">Build time:</strong> 8-12 weeks shop, 2-3 day install (plus stone fabrication scheduling).</li>
  <li><strong class="text-white">Where the cost goes:</strong> stone fabrication (waterfall edges require a single slab + miter), specialty drawers (Blum SPACE TOWER, etc), integrated appliances.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Counter material — the biggest budget lever</h2>
<ul>
  <li><strong class="text-white">Butcher block (maple, walnut):</strong> $40-$80 / sq ft. Warm, can be sanded + re-oiled. Will show knife marks.</li>
  <li><strong class="text-white">Quartz (engineered stone):</strong> $80-$140 / sq ft. Zero maintenance. Many color options. Most popular choice.</li>
  <li><strong class="text-white">Quartzite (natural stone):</strong> $110-$180 / sq ft. Looks like marble, performs like granite.</li>
  <li><strong class="text-white">Soapstone:</strong> $90-$160 / sq ft. Patinas over time. Heat-proof.</li>
  <li><strong class="text-white">Marble:</strong> $90-$200 / sq ft. Etches with acid (lemon juice, wine). Beautiful, high-maintenance.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Size — the one place we push back</h2>
<p>The "more is more" instinct gets a lot of islands too big. The right size:</p>
<ul>
  <li><strong class="text-white">At least 42 inches of clearance</strong> on all sides for traffic. 48 if it has seating.</li>
  <li><strong class="text-white">Cap usable length at 9 feet</strong> for a single slab. Past that you need a seam, which compromises a waterfall look.</li>
  <li><strong class="text-white">Seating overhang:</strong> 12 inches for casual, 15 inches for actual dining.</li>
</ul>
<p>If your kitchen forces an island below 30 inches deep, skip the island and do a peninsula. A too-small island reads cramped.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Features worth the money</h2>
<ul>
  <li><strong class="text-white">Pop-up outlets.</strong> Standing outlets on the side of an island always look bad. Pop-ups disappear.</li>
  <li><strong class="text-white">Soft-close drawers + hinges.</strong> Cheap kitchens skip these. The 10-year cost difference is small.</li>
  <li><strong class="text-white">Trash pullout.</strong> One double bin near the prep zone. Saves walking trips.</li>
  <li><strong class="text-white">Drawer dividers in the silverware/utensil zone.</strong> Sounds small. Used hourly.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Features that usually do not pay off</h2>
<ul>
  <li><strong class="text-white">Built-in microwave drawer.</strong> Looks clean. Costs ~$1,500 over a countertop microwave. If you cook a lot, sure. If not, skip.</li>
  <li><strong class="text-white">Pop-up cutting board.</strong> Sounds great. Almost never used after month two.</li>
  <li><strong class="text-white">Integrated charging drawer.</strong> Useful for one year, then your phones change connectors and the drawer is dead.</li>
</ul>

<p class="mt-8 text-cream-30 italic">Thinking about an island? Send us a floor plan or even a rough sketch + photos of the kitchen. We will come back with a 1-page concept and a real budget range for the tier you actually want.</p>
`.trim()
  },
  {
    slug: "built-in-shelving-specify-without-looking-generic",
    title: "Built-in shelving: how to specify yours so it does not look generic",
    description:
      "Most built-ins look the same because most are spec'd the same. Here are the 6 design decisions that separate a custom built-in from a fancier IKEA.",
    excerpt:
      "Most built-ins in Orlando homes look the same because they were spec'd from the same showroom catalog. Here are the six decisions that separate a piece that reads custom from one that reads like a kit.",
    category: "Furniture",
    tags: ["built-ins", "shelving", "custom-furniture", "design", "interior"],
    publishedAt: "2026-05-09",
    author: "JB Woodworks",
    cover: "/img/generated/cta-shavings.png",
    ogImage: "/img/generated/cta-shavings.png",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">Walk into any new-build home in the Orlando area and you will see the same built-in: white shaker doors below, open shelves above, crown molding at the top. It is not bad. It is just not custom. Here is how to spec yours so it actually reads as one-of-a-kind.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">1. Stop centering everything</h2>
<p>The kit-look comes from perfect symmetry — center cabinet, two flanking columns, even spacing. Real custom plays with rhythm. Try:</p>
<ul>
  <li>A taller central section flanked by shorter wing cabinets.</li>
  <li>Open shelves on one side, closed cabinets on the other.</li>
  <li>A built-in bench seat with shelves above on just one side.</li>
</ul>
<p>Asymmetry reads as "designed for this room," not "ordered from a catalog."</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">2. Skip the crown molding (or replace it with something honest)</h2>
<p>Crown molding on top of a built-in is the architectural equivalent of clip-art. Two better moves:</p>
<ul>
  <li><strong class="text-white">Run the unit to the ceiling</strong> with a 1-inch reveal. Clean, modern, no molding required.</li>
  <li><strong class="text-white">Top with a single beefy header</strong> (a 6-inch tall piece of trim) and skip the crown entirely. Reads as "built piece of furniture," not "casework."</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">3. Pick one wood species and run it</h2>
<p>Showrooms often mix species — painted poplar boxes with stained oak fronts, for example. It saves the showroom money. It reads as compromise to anyone who has seen real custom work. Pick one species (white oak, walnut, cherry, fir) and use it everywhere visible. We will run inside boxes in maple ply because nobody sees them; everything visible is the chosen species.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">4. Get the shelf thickness right</h2>
<p>The default in factory built-ins is 3/4-inch shelves. That is a structural minimum, not an aesthetic choice. For a 30+ inch span, 3/4 inch shelves sag visibly within 3 years under any real book load.</p>
<p>Our default for open shelves is <em class="text-gold">1-1/4 inch</em> if the span is over 30 inches, or 1-1/2 inch for the "this is the focal shelf" piece. Costs slightly more in materials, dramatically more in visual presence. Thick shelves read as expensive even if everything else is plain.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">5. Light the shelves</h2>
<p>Open shelving without light is shelving you cannot see at night. Built-in puck lights or LED strips behind the front edge of each shelf cost $40-$80 per shelf installed and change the room entirely. They run on a dimmer; we tie them to the same dimmer as the room's ambient lighting so it all moves together.</p>
<p>Skip color-changing RGB. The hardware ages out within 5 years and the warm-only puck lights age out around 20.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">6. Hide the screws</h2>
<p>The detail nobody talks about that everyone notices subconsciously. Cabinet adjustable shelf supports come in three flavors:</p>
<ul>
  <li><strong class="text-white">Plastic pins:</strong> default. Visible. Look cheap.</li>
  <li><strong class="text-white">Brass or nickel pins:</strong> $5 per shelf. Visible but intentional. Better.</li>
  <li><strong class="text-white">Routed dadoes (no pins at all):</strong> shelves slide into slots cut into the cabinet sides. Fixed but invisible. Furniture-grade.</li>
</ul>
<p>For the upper-end of custom we route dadoes for the fixed shelves and use brass pins only for the adjustable ones.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Common applications + budget ranges (Orlando, 2026)</h2>
<ul>
  <li><strong class="text-white">Living room TV wall (cabinets below, open shelves above, 10-12 ft wide):</strong> $9,000-$18,000.</li>
  <li><strong class="text-white">Home office wall-to-wall:</strong> $7,500-$15,000.</li>
  <li><strong class="text-white">Mudroom / bench + lockers:</strong> $4,500-$9,000.</li>
  <li><strong class="text-white">Bedroom wall of wardrobes with built-in dresser:</strong> $9,000-$20,000.</li>
  <li><strong class="text-white">Stairwell library wall, floor to ceiling:</strong> $6,500-$14,000.</li>
</ul>

<p class="mt-8 text-cream-30 italic">Send us a photo of the wall + rough dimensions and what you want to store there. We will reply with a sketch concept and a real budget range, usually within one business day.</p>
`.trim()
  },
  {
    slug: "new-deck-first-year-and-lifetime-care",
    title: "Caring for your new deck: the first year and the next twenty",
    description:
      "What to do (and not do) in the first 12 months of a new deck so it still looks new at year five — and the long-term maintenance schedule.",
    excerpt:
      "The first 12 months of a deck's life decide what it looks like at year five. Here is the maintenance schedule we send every customer for pressure-treated, cedar, and composite — and the mistakes to avoid.",
    category: "Maintenance",
    tags: ["decks", "maintenance", "care", "trex", "cedar", "pressure-treated", "orlando"],
    publishedAt: "2026-05-07",
    author: "JB Woodworks",
    cover: "/img/projects/Deck/IMG_1649.jpg",
    ogImage: "/img/projects/Deck/IMG_1649.jpg",
    readingTimeMinutes: 5,
    bodyHtml: `
<p class="lead">A deck's first year is the year you set the next twenty. Skip the first-year care and the deck never quite catches up. Here is the schedule we send home with every job, by material.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Pressure-treated decks — first year</h2>
<p>The wood ships wet from the treatment plant. It needs to dry before you seal it or stain takes patchy.</p>
<ul>
  <li><strong class="text-white">Weeks 1-12:</strong> let it dry. Walk on it, use it normally. Do not seal.</li>
  <li><strong class="text-white">Month 4-6:</strong> sprinkle test. Drop water on a board; if it beads up, the wood is not ready. If it soaks in within 30 seconds, you can stain.</li>
  <li><strong class="text-white">Month 4-6 once it passes the sprinkle test:</strong> apply a transparent or semi-transparent oil-based stain. We like Cabot or TWP. Two coats. Let dry 48 hours between.</li>
  <li><strong class="text-white">Month 9-12:</strong> sweep clean every 2 weeks. Pollen and oak debris ferment on wet wood and stain it.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Pressure-treated — lifetime schedule</h2>
<ul>
  <li><strong class="text-white">Year 2:</strong> light wash (garden hose + deck brush). Re-coat stain in spring.</li>
  <li><strong class="text-white">Years 3-5:</strong> annual wash. Re-stain every 24-36 months depending on UV exposure.</li>
  <li><strong class="text-white">Year 8-10:</strong> inspect for soft spots near posts and ledger. Treat or replace boards as needed.</li>
  <li><strong class="text-white">Year 12+:</strong> consider re-decking with the existing frame if framing is still solid.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Cedar — first year</h2>
<p>Cedar ships dry. You can finish it the same week we install it.</p>
<ul>
  <li><strong class="text-white">Week 1-2:</strong> wipe boards with a damp rag, let dry overnight, apply a penetrating oil (we use Penofin or Sikkens Cetol). Two coats, 24 hours apart.</li>
  <li><strong class="text-white">Months 1-12:</strong> sweep biweekly, hose off as needed. Avoid pressure washing — it raises the grain.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Cedar — lifetime schedule</h2>
<ul>
  <li><strong class="text-white">Annual:</strong> re-oil in spring. Cedar drinks oil; it is not a one-and-done finish.</li>
  <li><strong class="text-white">Every 5-7 years:</strong> light sand with a 60-grit pad to remove weathered surface, then re-oil.</li>
  <li><strong class="text-white">Year 12-18:</strong> evaluate. Cedar in Florida ages out around 15 years if you keep up with oil.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Composite (Trex / TimberTech / Azek) — first year</h2>
<p>The "no maintenance" claim is mostly true. Caveat: it is "no maintenance" only if you actually clean it. Mildew on the surface looks the same on a $80/sq ft composite as on a $30/sq ft pine.</p>
<ul>
  <li><strong class="text-white">Months 1-3:</strong> sweep weekly. Pollen + oak debris + summer heat cooks into a sticky film if it sits.</li>
  <li><strong class="text-white">Month 6:</strong> first deep clean. Garden hose + soft brush + Dawn dish soap. Do not use bleach on the cap; it eats the UV coating.</li>
  <li><strong class="text-white">Month 12:</strong> walk the deck and check for hidden-clip movement. Some clips back out under thermal cycling; one drop of thread-locker per affected clip and it is back to permanent.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Composite — lifetime schedule</h2>
<ul>
  <li><strong class="text-white">Every 4-6 months:</strong> hose-and-soft-brush clean. 20 minutes. Done.</li>
  <li><strong class="text-white">Annual:</strong> walk the frame from below. Check the joist hangers and ledger for any galvanic corrosion. (Composite + steel can corrode if water sits.)</li>
  <li><strong class="text-white">Year 10:</strong> evaluate for clip + screw replacement. Warranty period for many systems.</li>
  <li><strong class="text-white">Year 25-30:</strong> usually still in service. Plan board-by-board swap only as needed.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Things to NOT do (on any deck)</h2>
<ul>
  <li><strong class="text-white">Pressure wash above 1,500 PSI.</strong> Cuts the wood fiber. Lifts composite caps.</li>
  <li><strong class="text-white">Park rubber-backed mats long-term.</strong> Traps moisture, leaves a permanent square. Use rubber mats with feet that let air through, or move them monthly.</li>
  <li><strong class="text-white">Run gas grills directly on the deck without a heat shield.</strong> Drips burn into composite; drips fire-stain wood.</li>
  <li><strong class="text-white">Apply ice melt.</strong> Not really an Orlando problem, but worth knowing — chlorides corrode hidden hardware.</li>
</ul>

<p class="mt-8 text-cream-30 italic">We send this guide home with every deck install, customized to the specific material. If you have a deck we built and want a free check-in at year 1, just ask — we drop by, walk the surface and the substructure, and tell you what (if anything) needs attention.</p>
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
