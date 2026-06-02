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
  },
  {
    slug: "cedar-vs-ipe-vs-composite-decking-florida-salt-air-10-year",
    title: "Cedar vs IPE vs composite decking — a 10-year salt-air comparison for FL",
    description:
      "Florida salt air, UV, and afternoon storms put decking through hell. Here is how cedar, IPE, and capped composite actually compare after a decade on the coast.",
    excerpt:
      "Ten years on the FL coast tells the truth about decking. Western red cedar, IPE, and capped composite — costs, lifespan, what fails first, what we install when the customer is two blocks from the ocean.",
    category: "Materials",
    tags: ["decks", "cedar", "ipe", "composite", "salt-air", "florida", "coastal"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    cover: "/img/generated/services-accent.png",
    ogImage: "/img/generated/services-accent.png",
    readingTimeMinutes: 7,
    bodyHtml: `
<p class="lead">Catalog brochures get cute on the FL coast. Salt mist, 90% summer RH, and direct UV pick the winner — not the marketing copy. Here is the honest 10-year breakdown of cedar, IPE, and capped composite from a shop that has pulled and replaced every one of them.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Western red cedar — the warm one</h2>
<p>Cedar's natural extractives (thujaplicins) resist fungal decay without chemicals. The USDA Forest Service Wood Handbook (FPL-GTR-282, 2021) lists western red cedar heartwood as "resistant to very resistant" to decay. In real FL coastal life that translates to <em class="text-gold">8-12 years</em> on a deck surface if you re-oil every 18-24 months. Skip the oil and you will see graying and surface checks by year 3.</p>
<ul>
  <li><strong class="text-white">Cost installed:</strong> ~$45-$70 / sq ft.</li>
  <li><strong class="text-white">Fails at:</strong> surface checking, soft fastener bleed-out, end-grain rot at cuts.</li>
  <li><strong class="text-white">Best for:</strong> pool decks, low-traffic shaded patios, anywhere bare feet matter.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">IPE (Brazilian walnut) — the tank</h2>
<p>IPE is dense enough to sink (specific gravity ~1.05) and rated Class 1 — "very durable" — by the Forest Products Lab (FPL Gen. Tech. Rep. 190). On the coast a properly installed IPE deck makes <em class="text-gold">25-40 years</em> with nothing but an annual rinse and a UV-oil refresh every 2-3 years to keep the brown (skip the oil and it silvers like teak — same lifespan).</p>
<ul>
  <li><strong class="text-white">Cost installed:</strong> ~$75-$120 / sq ft. Carbide blades only; pre-drill every fastener.</li>
  <li><strong class="text-white">Fails at:</strong> almost never — usually a substructure failure under it.</li>
  <li><strong class="text-white">Best for:</strong> oceanfront primary decks where you want hardwood and forget-about-it lifespan.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Capped composite — the warranty bet</h2>
<p>Trex Transcend, TimberTech AZEK, Fiberon — all capped PVC or polyethylene over a wood-flour core. Trex's 50-year residential warranty covers fade and stain. After 10 years on Anna Maria Island, the capped boards we pulled looked virtually identical to year-one. The failures we have seen are <em class="text-gold">uncapped composite</em> (1990s-era Trex) — they bled mildew and the surface mushroomed.</p>
<ul>
  <li><strong class="text-white">Cost installed:</strong> ~$55-$95 / sq ft.</li>
  <li><strong class="text-white">Fails at:</strong> surface heat (140-160°F in direct FL sun — barefoot caution), fastener punch-through at undersized joists.</li>
  <li><strong class="text-white">Best for:</strong> primary residences, dock decking, anyone who refuses to re-oil.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What we install two blocks from the water</h2>
<p>Default is IPE. The math: $90/sq ft once, vs $55/sq ft composite + 50-year warranty. Both will outlast the substructure. We pick IPE when the customer wants natural wood, capped composite when they want zero maintenance, cedar only when the budget caps and the deck is shaded. Salt air is not the decking's enemy on these — it is the <em class="text-gold">fasteners and joist hangers</em>. Use 316 stainless or hot-dip galv per the AWPA M4-22 standard.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/fpl_gtr282.pdf" rel="noopener">USDA Forest Service Wood Handbook (FPL-GTR-282, 2021)</a></li>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr190/" rel="noopener">FPL Gen. Tech. Rep. 190 — Wood as an Engineering Material</a></li>
  <li><a href="https://awpa.com/standards/" rel="noopener">AWPA M4-22 — Care of Preservative-Treated Wood Products</a></li>
  <li><a href="https://www.trex.com/our-company/warranty/" rel="noopener">Trex 50-year Limited Residential Warranty</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">On the water and weighing decking? Send us the address and we will pull recent satellite shots to gauge salt exposure, then come back with a real cost spread.</p>
`.trim()
  },
  {
    slug: "hurricane-tie-deck-design-fbc-2026-compliance",
    title: "Hurricane-tie deck design for FL Building Code (FBC 2026) compliance",
    description:
      "FBC 2026 Section R507 spells out deck load paths. Here is how we engineer hurricane-tie connections that pass inspection in FL coastal counties.",
    excerpt:
      "Decks fail at the connections, not the wood. FBC 2026 R507 + ASCE 7-22 uplift loads dictate the ties. Here is the load-path map we use to pass inspection in Brevard, Pinellas, and Lee.",
    category: "Code",
    tags: ["fbc", "hurricane", "decks", "code", "uplift", "florida", "engineering"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 8,
    bodyHtml: `
<p class="lead">A deck does not blow off in a hurricane — the <em class="text-gold">connections</em> do. FBC 2026 Section R507 prescribes the entire load path from board to ground. Miss one tie and the inspector red-tags you. Here is the map we follow.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The five connections that matter</h2>
<ol>
  <li><strong class="text-white">Board-to-joist:</strong> stainless screws or hidden clips rated for the species. FBC R507.2.</li>
  <li><strong class="text-white">Joist-to-ledger/beam:</strong> Simpson LUS or LSSU hangers, 316 SS in coastal exposure.</li>
  <li><strong class="text-white">Ledger-to-house band:</strong> 1/2" hot-dip galv lag with washer, max 16" o.c., per FBC R507.9.1.3.</li>
  <li><strong class="text-white">Beam-to-post:</strong> Simpson AC or LCE caps; hurricane uplift requires a continuous strap (Simpson MSTA / LSTA) per ASCE 7-22 Chapter 26.</li>
  <li><strong class="text-white">Post-to-footing:</strong> ABU66Z standoff base, embedded anchor bolt, 1/2" minimum diameter, 7" embedment in 3000 psi concrete.</li>
</ol>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Uplift load math (the inspector check)</h2>
<p>FL Risk Cat II structures in 150 mph Exposure C (most coastal lots from Sarasota south) hit roughly <em class="text-gold">35-45 psf uplift</em> on an open deck surface per ASCE 7-22 Figure 26.5-1. For a 12'×16' deck that is ~7,700 lbs of uplift the connections must absorb. A Simpson MSTA36 strap rated 1,225 lbs at each post pair clears it with a 2x safety factor — that is the spec we draw on every set.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Coastal corrosion — the fastener call</h2>
<p>Within 3,000 ft of saltwater, FBC R317.3.4 requires 316 SS or G-185 hot-dip galv. We default to 316 on the coast because Simpson's ZMAX (G-185) starts pitting in salt spray testing at ~1,000 hours per ASTM B117. 316 SS goes 5,000+ hours clean. The cost delta is ~$300 per deck — irrelevant when the connector is what keeps your kids safe.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Ledger-to-house — the most-failed connection</h2>
<p>Two-thirds of deck collapses in FBC plan-review failures trace to the ledger. Code requires through-bolts (not lags) into solid framing, with 1/2" min diameter, max 24" o.c. staggered, AND flashing per FBC R507.9.1.4. We add a continuous Z-flashing under house siding, then a self-adhered HardieWrap or Vycor strip over the ledger top. Water gets in there or the framing rots in 4 years.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://codes.iccsafe.org/content/FLRC2026" rel="noopener">Florida Building Code, Residential 2026 (R507)</a></li>
  <li><a href="https://www.asce.org/publications-and-news/asce-7" rel="noopener">ASCE 7-22 — Minimum Design Loads</a></li>
  <li><a href="https://www.strongtie.com/resources/literature/deck-construction-guide" rel="noopener">Simpson Strong-Tie Deck Construction Guide DCAB23</a></li>
  <li><a href="https://www.astm.org/b0117-19.html" rel="noopener">ASTM B117 — Salt Spray Test</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Building in a high-wind zone? Send us the address and we will pull the FBC wind map + flood zone for the lot before the first sketch.</p>
`.trim()
  },
  {
    slug: "marine-grade-fasteners-316-stainless-silicon-bronze-galvanized",
    title: "Marine-grade fasteners — 316 stainless vs silicon bronze vs hot-dip galv",
    description:
      "Choosing the wrong fastener on a coastal FL build means a rebuild in 5 years. Honest comparison: 316 SS, silicon bronze, and G-185 hot-dip galv.",
    excerpt:
      "The fastener outlives the wood — or it doesn't. 316 stainless, silicon bronze, hot-dip galv. Real corrosion data, real cost math, real pick for FL coastal docks and decks.",
    category: "Materials",
    tags: ["fasteners", "stainless", "bronze", "galvanized", "marine", "salt-air", "florida"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">The deck board rots in 20 years. The fastener rots in 2. On the FL coast the metal choice decides whether the whole structure makes it. Here is the honest read.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Type 316 stainless steel</h2>
<p>Austenitic stainless with 2-3% molybdenum added to resist chloride pitting. Per the Nickel Institute Tech Series 11003, 316 SS shows essentially no corrosion in marine atmosphere after 26 years of exposure on the Kure Beach NC test rack. <em class="text-gold">Standard fastener for our oceanfront work.</em></p>
<ul>
  <li><strong class="text-white">Cost:</strong> ~$0.55 per #10×3" screw.</li>
  <li><strong class="text-white">Use for:</strong> deck screws, hidden clips, joist hangers (Simpson SS series), pile bolts.</li>
  <li><strong class="text-white">Caution:</strong> avoid 304 SS at the coast — chloride pitting starts within 18 months.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Silicon bronze</h2>
<p>96% copper, 3% silicon — the traditional boatbuilder's screw. Develops a verdigris patina that actually <em class="text-gold">stops further corrosion</em>. Beats 316 SS in fully submerged saltwater (no crevice corrosion). The Forest Products Lab Research Note FPL-RN-0382 documents bronze fasteners pulled from cedar siding after 80 years still structurally sound.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> ~$1.20 per #10×3" screw. 2x stainless.</li>
  <li><strong class="text-white">Use for:</strong> underwater pile work, traditional boat-deck builds, anywhere a galvanic match with copper-treated lumber matters.</li>
  <li><strong class="text-white">Caution:</strong> softer than steel — strip easily under power drivers. Pre-drill mandatory.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Hot-dip galvanized (G-185 / ASTM A153)</h2>
<p>Steel dipped in molten zinc to ASTM A153 Class D — minimum 1.85 oz/sq ft of zinc. Sacrificial coating: the zinc corrodes first, protecting the steel underneath. Service life in FL coastal exposure (per ASTM B117 salt-spray + AAMA 2604 cycling) is <em class="text-gold">8-15 years</em> before red rust appears. Cheap and code-compliant but not best.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> ~$0.18 per #10×3" screw.</li>
  <li><strong class="text-white">Use for:</strong> inland builds, pressure-treated lumber connections (galv is compatible with ACQ/MCA treatment — stainless is best, electro-galv WILL fail).</li>
  <li><strong class="text-white">Caution:</strong> never mix galv with 316 SS in the same connection — galvanic couple eats the zinc fast.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The galvanic-couple rule</h2>
<p>Per the Anodic Index (MIL-STD-889C) any two metals more than 0.25V apart in the same connection will form a galvanic cell. 316 SS (-0.05V) and galv (-1.05V) are 1V apart — the galv vanishes in months. Pick ONE family per connection and stay there.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://nickelinstitute.org/library/" rel="noopener">Nickel Institute Tech Series 11003 — Stainless Steels in Architecture</a></li>
  <li><a href="https://www.fpl.fs.usda.gov/" rel="noopener">FPL Research Note FPL-RN-0382 — Fastener Corrosion</a></li>
  <li><a href="https://www.astm.org/a0153_a0153m-23.html" rel="noopener">ASTM A153/A153M — Zinc Coating on Iron and Steel Hardware</a></li>
  <li><a href="https://landandmaritime.dla.mil/Documents/MilSpec/MIL-STD/MIL-STD-889C.pdf" rel="noopener">MIL-STD-889C — Dissimilar Metals</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Specifying fasteners for a coastal build? Send us the elevation drawing and the salt-water distance — we will spec every screw, bolt, and hanger to FBC R317 + AWPA M4.</p>
`.trim()
  },
  {
    slug: "cedar-care-florida-coastal-humidity-sealers-oils-mildew",
    title: "Cedar care in FL coastal humidity — sealers, oils, and mildew control",
    description:
      "Cedar in Florida needs a maintenance rhythm. Here are the sealers and oils we actually use, plus how to stop mildew before it gets a foothold.",
    excerpt:
      "Cedar is a 30-year wood in Vermont and a 7-year wood in Florida — unless you maintain it. The honest schedule for sealers, penetrating oils, and mildew control on FL coastal cedar.",
    category: "Maintenance",
    tags: ["cedar", "maintenance", "sealers", "oils", "mildew", "florida", "humidity"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">Cedar handles inland FL fine. Cedar at the coast asks for a schedule. Here is the rotation we hand every customer who picks cedar in Brevard or Pinellas.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Why FL is harder on cedar than the Pacific Northwest</h2>
<p>Cedar evolved in cool, damp Pacific air. FL summer dewpoint runs 73-77°F for weeks — the wood never fully dries. Forest Products Lab studies (FPL-GTR-190 Ch. 14) document that moisture cycling above 19% MC accelerates surface checking 3-4x. Add direct UV at ~5 kWh/m²/day and the lignin photodegrades within 6 months unsealed.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Penetrating oils vs film-forming sealers</h2>
<p>For FL we run <em class="text-gold">penetrating oil only</em>. Film-forming products (varnish, urethane, latex stain) trap moisture under the film, lift, and peel within 18 months. Penetrating oils — TWP 1500 series, Messmer's UV Plus, Cutek Extreme — soak in, do not film, and re-coat without sanding.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The 18-month rotation</h2>
<ol>
  <li><strong class="text-white">Month 0:</strong> install + apply TWP 1500 (cedar tone) at 250-300 sq ft/gal.</li>
  <li><strong class="text-white">Month 6:</strong> rinse with soft brush + low-pressure water (under 1,500 psi).</li>
  <li><strong class="text-white">Month 12:</strong> oxalic-acid brightener (Restore-A-Deck or similar) + cedar tone touch-up on south/west faces.</li>
  <li><strong class="text-white">Month 18:</strong> full re-coat. Surface should drink ~75% of the original coat.</li>
</ol>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Mildew control</h2>
<p>Mildew is the visible early indicator that lignin is breaking down. Per the Western Red Cedar Lumber Association (WRCLA) Care Guide, a 3:1 water-to-oxygen-bleach mix (NOT chlorine — chlorine darkens cedar) kills surface mildew in 10 minutes. Rinse, let dry 48 hours, re-oil. Avoid pressure washing above 1,500 psi — it raises the grain and accelerates the next mildew event.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What we DO NOT recommend</h2>
<ul>
  <li><strong class="text-white">Linseed oil:</strong> feeds mildew. Period.</li>
  <li><strong class="text-white">Tung oil alone:</strong> no UV inhibitors — bleaches to silver in 4 months.</li>
  <li><strong class="text-white">Solid-color stains:</strong> film-forming. Peels.</li>
  <li><strong class="text-white">Chlorine bleach:</strong> breaks down lignin, makes future oil adhesion fail.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr190/" rel="noopener">FPL-GTR-190 Ch. 14 — Finishing of Wood</a></li>
  <li><a href="https://www.realcedar.com/care-and-maintenance/" rel="noopener">WRCLA Cedar Care and Maintenance Guide</a></li>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplrp/fplrp558.pdf" rel="noopener">FPL Research Paper 558 — UV Degradation of Wood</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Inheriting a tired cedar deck? Send us 3 photos — we can usually tell from the surface whether it is a re-oil or a board replacement before we drive out.</p>
`.trim()
  },
  {
    slug: "pressure-treated-alternatives-ground-contact-florida",
    title: "Pressure-treated alternatives for ground-contact applications in FL",
    description:
      "Modern PT lumber has trade-offs. Here are the alternatives — naturally rot-resistant species, plastic composites, and concrete piers — for FL ground-contact work.",
    excerpt:
      "Pressure-treated is the default, not the only choice. Cypress, IPE, black locust, plastic lumber, and concrete piers — when each makes sense for FL ground-contact builds.",
    category: "Materials",
    tags: ["pressure-treated", "ground-contact", "alternatives", "florida", "cypress", "locust"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">Pressure-treated southern yellow pine is cheap, code-compliant, and everywhere. It also leaches copper, looks industrial, and warps if it dries too fast. Here are the alternatives we use when the customer wants something else for ground-contact work in FL.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What "ground contact" means under AWPA</h2>
<p>AWPA U1-22 Use Category UC4A (general ground contact) requires 0.40 pcf retention of MCA/ACQ in southern pine. UC4B (heavy duty, sustained ground contact like critical structural piers) demands 0.60 pcf. Most "ground-contact" PT at the big-box is UC4A — check the end tag.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Naturally rot-resistant alternatives</h2>
<ul>
  <li><strong class="text-white">Bald cypress (Taxodium distichum):</strong> Florida-native, Class 2 durability per FPL. Heartwood lasts 30+ years in FL ground contact. ~$5-$8/bf.</li>
  <li><strong class="text-white">Black locust (Robinia pseudoacacia):</strong> Class 1 durability — outperforms PT pine in head-to-head USDA fence-post studies (FPL-RP-558). Hard to source large sections in FL but specialty mills carry it.</li>
  <li><strong class="text-white">IPE (Handroanthus spp.):</strong> Class 1, dense enough to defeat termites mechanically. ~$12-$18/bf for ground-contact rated stock.</li>
  <li><strong class="text-white">Old-growth heart redwood:</strong> Class 1 but supply is gone; reclaimed only.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Non-wood alternatives</h2>
<ul>
  <li><strong class="text-white">Plastic lumber (HDPE/PVC):</strong> Tangent, Bedford, Trex Structural. Spans shorter than PT pine — design accordingly. Zero rot, zero termite risk. ~3x PT cost but lifetime.</li>
  <li><strong class="text-white">Concrete piers + standoff bases:</strong> the right answer for pergola and pavilion posts. Simpson ABU66Z or ABA66Z gets the post 1" off the slab so it never reaches FSP (fiber saturation point).</li>
  <li><strong class="text-white">Galvanized steel C-channel sleepers:</strong> for deck under-structures over slab — we use these on commercial work.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What we actually pick</h2>
<p>For visible posts: cypress, sealed with TWP. For invisible buried posts: PT UC4B (the 0.60 pcf stuff, not the cheap stuff). For piers: poured concrete + standoff base. For dock pilings: CCA-C 2.5 pcf (still legal for marine use per AWPA U1-22 footnote — the residential ban does not apply to marine pilings).</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://awpa.com/standards/" rel="noopener">AWPA U1-22 — Use Category System</a></li>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplrp/fplrp558.pdf" rel="noopener">FPL-RP-558 — Service Life of Treated and Untreated Fence Posts</a></li>
  <li><a href="https://www.epa.gov/ingredients-used-pesticide-products/chromated-arsenicals-cca" rel="noopener">EPA CCA-C Marine Use Exemption</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Building something that touches dirt? Tell us what and where — we will spec the right material so it outlasts the warranty period.</p>
`.trim()
  },
  {
    slug: "pergola-post-anchoring-concrete-piers-vs-in-ground-vs-anchor-bolts",
    title: "Pergola post anchoring — concrete piers vs in-ground PT vs anchor bolts",
    description:
      "Pergola failures start at the post base. Here is how we anchor in FL — concrete piers, buried PT, and anchor-bolt standoffs — and when each is right.",
    excerpt:
      "Three ways to plant a pergola post in Florida soil. Concrete pier, buried PT, anchor-bolt standoff. The lifespan, wind-rating, and code call for each.",
    category: "Construction",
    tags: ["pergola", "anchoring", "concrete", "anchor-bolts", "florida", "code"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">A pergola is wind-load and rot resistance, nothing else. Both decisions live at the post base. Here are the three approaches we use and the call we make for each project.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Option A — Concrete pier with anchor-bolt standoff</h2>
<p>Our default for FL. Pour a 12" diameter × 36" deep pier in 3,000 psi concrete (FBC R403.1.4 frost depth N/A in FL — the depth is for uplift, not frost). Set a 5/8" J-bolt or Simpson SB58 anchor with 7" embedment. Mount a Simpson ABU66Z standoff base after cure. <em class="text-gold">Post sits 1" above the concrete</em> — never wets out, never rots at the base.</p>
<ul>
  <li><strong class="text-white">Lifespan:</strong> 40+ years (the wood post is replaceable; the pier outlives it).</li>
  <li><strong class="text-white">Wind:</strong> rated to 5,200 lbs uplift per Simpson ICC-ES ESR-2523.</li>
  <li><strong class="text-white">Cost:</strong> ~$180 per post all-in.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Option B — Buried PT post</h2>
<p>6×6 UC4B (0.60 pcf retention) PT post in a 36" hole, surrounded by gravel (NOT concrete — concrete around a wood post traps water and accelerates rot). Service life in FL: <em class="text-gold">15-25 years</em> per the FPL ground-contact study. Cheap, fast, looks clean. Failure mode is at the soil-air interface — that 4" band rots first.</p>
<ul>
  <li><strong class="text-white">Lifespan:</strong> 15-25 years.</li>
  <li><strong class="text-white">Wind:</strong> excellent uplift if depth is right (D = 1/3 × post height minimum).</li>
  <li><strong class="text-white">Cost:</strong> ~$95 per post all-in.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Option C — Surface-mount anchor bolt into existing slab</h2>
<p>Customer has a 4"+ concrete patio they refuse to bust up. We drill, drop Simpson Titen HD 5/8"×6" wedge anchors, mount ABU66Z. <em class="text-gold">Only if</em> the slab tests >= 2,500 psi (we core-sample) and has rebar. Otherwise the slab cracks at the anchor under wind load.</p>
<ul>
  <li><strong class="text-white">Lifespan:</strong> matches slab.</li>
  <li><strong class="text-white">Wind:</strong> 3,800 lbs uplift per Titen HD ICC-ES ESR-2713.</li>
  <li><strong class="text-white">Cost:</strong> ~$110 per post — but only if the slab cooperates.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The FBC wind call</h2>
<p>FBC R301.2.1 + ASCE 7-22 Chapter 26 — for a 12'×16' pergola in 150 mph Exposure C, design uplift is ~2,400 lbs per post. All three options clear it. Choose on lifespan and aesthetics, not wind rating, in most FL coastal counties.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://codes.iccsafe.org/content/FLRC2026/chapter-4-foundations" rel="noopener">FBC Residential 2026 — Chapter 4 Foundations</a></li>
  <li><a href="https://www.strongtie.com/resources/literature" rel="noopener">Simpson ICC-ES ESR-2523 (ABU) and ESR-2713 (Titen HD)</a></li>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplrp/fplrp558.pdf" rel="noopener">FPL-RP-558 — Service Life of Posts in Ground</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Pergola on the calendar? Send us a sketch with rough dimensions — we will pick the anchoring before we price the rafters.</p>
`.trim()
  },
  {
    slug: "dock-pile-maintenance-oyster-fouling-marine-borer-prevention",
    title: "Dock pile maintenance — Eastern oyster fouling and marine borer prevention",
    description:
      "FL dock piles get hit by oysters above and Teredo navalis below. Here is how we treat, sleeve, and inspect pilings to survive the gulf and Atlantic.",
    excerpt:
      "Oyster fouling above the waterline, shipworms below — FL dock piles get attacked from both sides. The treatment, the sleeve, the inspection cycle we run.",
    category: "Maintenance",
    tags: ["dock", "piles", "marine-borers", "oysters", "florida", "maintenance"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 7,
    bodyHtml: `
<p class="lead">FL dock piles fight two battles. Above the waterline, Eastern oyster (Crassostrea virginica) cement on and crack the pile from the outside. Below, the shipworm (Teredo navalis) and gribble (Limnoria) eat from the inside. Here is what we do.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The treatment baseline — CCA-C 2.5 pcf</h2>
<p>Marine pilings remain the one residential use of CCA-C (chromated copper arsenate) the EPA permits under the 2003 Voluntary Cancellation footnote. AWPA U1-22 UC5C requires 2.5 pcf retention for severe marine duty. Cheaper UC5A (1.5 pcf) is gulf-side only — the Atlantic side eats it faster. <em class="text-gold">Spec 2.5 pcf on every new pile.</em></p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The sleeve — PVC pile wrap</h2>
<p>Marine Bottom Paint by itself fails in 18 months. We sleeve the splash zone (mean low tide to 24" above mean high tide) with 80-mil PVC pile wrap, banded with 316 SS straps. Per the National Marine Manufacturers Association (NMMA) Best Practices, this stops oyster cementing entirely and adds 15-20 years of life. ~$45 per pile installed.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The inspection cycle</h2>
<ol>
  <li><strong class="text-white">Year 1:</strong> visual inspection above waterline, no diving needed.</li>
  <li><strong class="text-white">Year 3:</strong> dive inspection — sound pile at -3 ft with a hammer for hollow tone (shipworm tunnels).</li>
  <li><strong class="text-white">Year 5:</strong> increment-borer sample of any suspect pile. Send to FPL Madison for borer ID.</li>
  <li><strong class="text-white">Year 10:</strong> full survey + plan for splash-zone re-sleeve.</li>
</ol>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">When to replace vs jacket</h2>
<p>If a pile loses more than 30% of its cross-section at any depth, replace. Below that we jacket: drive a steel form around the pile, fill with epoxy grout (Sika MonoTop or equivalent). Lifespan gain: 20+ years. FL DEP Form 62-330 permitting is required for any pile replacement in tidal waters — we file it; the customer signs.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The fouling — why oysters matter</h2>
<p>Oysters grow ~2" per year on a FL pile. After 5 years a cluster can weigh 40+ lbs concentrated at the mean high tide line. That bending moment cracks PT pine. We scrape annually with a long-handled chisel scraper from the dock deck — no diving — and re-paint the splash zone with copper bottom paint after every scrape.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://awpa.com/standards/" rel="noopener">AWPA U1-22 UC5 — Marine Use</a></li>
  <li><a href="https://floridadep.gov/water/submerged-lands-environmental-resources-coordination" rel="noopener">FL DEP Submerged Lands &amp; Environmental Resources</a></li>
  <li><a href="https://www.fpl.fs.usda.gov/" rel="noopener">FPL Marine Borer Research</a></li>
  <li><a href="https://www.epa.gov/ingredients-used-pesticide-products/chromated-arsenicals-cca" rel="noopener">EPA CCA Marine Use Footnote</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Dock looking tired? We do free above-water inspections within 30 miles of the shop and quote sleeve-vs-replace before the dive.</p>
`.trim()
  },
  {
    slug: "outdoor-furniture-finishing-salt-air-exposure-florida",
    title: "Custom outdoor furniture finishing for salt-air exposure",
    description:
      "Salt-air destroys most outdoor finishes in 2 seasons. Here are the finishes we apply to custom teak, ipe, and cypress furniture for FL coastal homes.",
    excerpt:
      "Teak silvers, ipe browns, cypress grays — under salt air all three need help. The finish schedule we apply in the shop and re-coat in the field for FL coastal furniture.",
    category: "Finishing",
    tags: ["finishing", "outdoor-furniture", "salt-air", "teak", "ipe", "cypress", "florida"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">A teak chair on Sanibel Island gets 6 hours of direct UV, 90% humidity, and a salt mist most evenings. Standard furniture finishes give up. Here is what we use.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The choice — leave it raw or finish it</h2>
<p>Teak, ipe, cumaru, and cypress all weather to a silver-gray with no structural loss. <em class="text-gold">Raw is a valid spec</em> — Adirondack and Cape Cod teak does it on purpose. We finish only when the customer wants the original warm tone preserved.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Our finish stack for FL coastal furniture</h2>
<ol>
  <li><strong class="text-white">Surface prep:</strong> sand to 180 grit. Wipe with acetone to strip teak's natural oils (otherwise top-coat will not bond).</li>
  <li><strong class="text-white">Penetrating sealer:</strong> Cutek Extreme CD50 — phenolic resin in solvent carrier. Two coats, wet-on-wet, 30 min apart. Penetrates 1/8" deep.</li>
  <li><strong class="text-white">UV top-coat:</strong> Sikkens Cetol Marine (or Epifanes Clear Gloss for tropical hardwoods). Three coats minimum. UV inhibitors at 4-6% loading — verifiable on the SDS.</li>
  <li><strong class="text-white">Re-coat:</strong> annually with one coat of Cetol on south/west exposures, every 18 months on north/east.</li>
</ol>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Why no polyurethane</h2>
<p>Standard exterior poly (Helmsman, Spar-Urethane) cracks within one FL summer. Reason: outdoor wood expands/contracts ~3% across the grain seasonally. Poly's elongation-at-break is ~5%. One bad expansion event and the film cracks — water gets under, finish lifts. <em class="text-gold">Marine varnishes have 15-20% elongation</em> built-in.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The salt-air gotcha</h2>
<p>NaCl crystals are hygroscopic — they pull moisture out of the air and trap it against the finish. Per ASTM B117 salt-spray testing, marine varnish on teak shows first surface crystallization at ~2,000 hours (~3 months continuous coastal exposure). Solution: rinse the furniture with fresh water monthly. A garden hose pass takes 30 seconds and doubles the re-coat interval.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr190/" rel="noopener">FPL-GTR-190 Ch. 16 — Finishing of Wood for Exterior Use</a></li>
  <li><a href="https://www.astm.org/b0117-19.html" rel="noopener">ASTM B117 — Salt Spray Test Methodology</a></li>
  <li><a href="https://www.sikkens.com/" rel="noopener">Sikkens Cetol Marine Technical Data Sheet</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Commissioning a piece for the coast? We will spec the finish for your exact exposure and include a maintenance card with the delivery.</p>
`.trim()
  },
  {
    slug: "kiln-dried-vs-air-dried-lumber-florida-outdoor",
    title: "Kiln-dried vs air-dried lumber for FL outdoor use",
    description:
      "KD and AD lumber behave differently in FL humidity. Here is which one we order for outdoor furniture, decks, and trim — and why it matters.",
    excerpt:
      "Kiln-dried hits 6-8% MC, air-dried sits around 14-16%. FL equilibrium moisture content is 12%. Which one moves less once installed? The answer is project-specific.",
    category: "Materials",
    tags: ["lumber", "kiln-dried", "air-dried", "moisture", "florida", "humidity"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 5,
    bodyHtml: `
<p class="lead">"Kiln-dried" sounds premium. For outdoor FL work it sometimes is — and sometimes it is exactly wrong. The right choice depends on what equilibrium moisture content (EMC) your project will live at.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The EMC reality in Florida</h2>
<p>The FPL Wood Handbook Table 13-1 puts Florida outdoor EMC at <em class="text-gold">12-13% year-round</em>, with summer humidity pushing surface MC to 14-15%. Indoor conditioned spaces average 8-10%. So:</p>
<ul>
  <li><strong class="text-white">Kiln-dried lumber at 6-8% MC:</strong> will absorb moisture and swell ~4-6% across the grain when installed outdoors.</li>
  <li><strong class="text-white">Air-dried lumber at 14-16% MC:</strong> will lose moisture and shrink ~2-4% when installed outdoors during dry months.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">When KD is the right call</h2>
<ul>
  <li>Outdoor furniture pieces with tight joinery (mortise-and-tenon, dovetails) — the joint cuts are dimensioned at KD MC and need to swell into the joint, not shrink out of it.</li>
  <li>Painted or finished surfaces — moisture content above 12% blocks finish adhesion.</li>
  <li>Anything heading into a screened porch or covered area where it will live closer to indoor EMC.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">When AD is the right call</h2>
<ul>
  <li>Deck boards — pin-down to EMC. AD lumber moves less after install.</li>
  <li>Pergola structural members.</li>
  <li>Anything full-sun-exposed where KD will swell and crack open.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The acclimation rule</h2>
<p>National Wood Flooring Association (NWFA) and the FPL both call for <em class="text-gold">14 days minimum</em> of on-site acclimation before milling/installation. We stack flat with stickers between layers, in the same exposure the wood will live in, and check MC with a Delmhorst BD-2100 pin meter before cutting. Below 13% MC = ready for outdoor install in FL.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/fpl_gtr282.pdf" rel="noopener">FPL Wood Handbook Ch. 13 — Drying and Control of Moisture Content</a></li>
  <li><a href="https://nwfa.org/technical-resources/" rel="noopener">NWFA Installation Guidelines — Acclimation</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Specifying lumber for an outdoor build? We will tell you KD or AD per piece, not per order.</p>
`.trim()
  },
  {
    slug: "ipe-installation-pre-drilling-hidden-fasteners-expansion-gaps",
    title: "IPE installation: pre-drilling, hidden fasteners, expansion gaps",
    description:
      "IPE is the most durable decking on the FL market — and the easiest to install wrong. Pre-drilling specs, hidden-fastener picks, and FL-specific expansion gaps.",
    excerpt:
      "IPE is a 40-year deck if you install it right and a 5-year deck if you don't. Pre-drill specs, hidden fastener choice, and the FL expansion-gap call we use on every job.",
    category: "Construction",
    tags: ["ipe", "decking", "installation", "fasteners", "florida"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 7,
    bodyHtml: `
<p class="lead">IPE (Handroanthus serratifolius) at ~3,684 Janka is harder than most steel screws. Skip the pre-drill and the screw snaps. Skip the gap and the deck buckles in August. Here are the install specs that work in FL.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Pre-drilling — pilot AND countersink</h2>
<p>For #8 stainless deck screws we drill a 1/8" pilot through the IPE, then a 5/16" countersink 1/4" deep. The countersink lets the head seat without splitting the surface. <em class="text-gold">Use carbide bits only</em> — HSS dulls in 50 holes. We run Bosch Pro DareDevil multi-construction bits and replace every 200-300 holes.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Hidden fasteners — what we actually use</h2>
<ul>
  <li><strong class="text-white">Ipe Clip Extreme (Ipe Clip Co):</strong> 316 SS, biscuit-style cut into the board edge. Our standard for surface-finished IPE.</li>
  <li><strong class="text-white">Camo Edge:</strong> screws at an angle through the board edge into the joist. Works on grooved IPE pre-milled at the mill.</li>
  <li><strong class="text-white">Tiger Claw TC-G:</strong> for grooved IPE — fast install, lifetime stainless warranty.</li>
</ul>
<p>Avoid plug-and-glue systems on FL coast work. The plug expands at a different rate than the IPE and pops within 3 summers.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Expansion gaps — the FL math</h2>
<p>IPE moves ~0.0023 inch per inch of width per percent MC change (FPL Wood Handbook Table 4-3). In FL the seasonal MC swing is 9-15% — so a 5.5" wide IPE board moves <em class="text-gold">~0.09" or 3/32"</em> across the grain seasonally.</p>
<ul>
  <li><strong class="text-white">Side-to-side gap:</strong> 1/8" with hidden fasteners. The clip system sets this.</li>
  <li><strong class="text-white">Butt-end gap:</strong> 1/8" between boards, 1/4" at any wall/post.</li>
  <li><strong class="text-white">Joist spacing:</strong> 16" o.c. for 1x6, 12" o.c. for diagonal layouts.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">End-grain sealing — the step everyone skips</h2>
<p>Every fresh cut in IPE exposes end-grain that wicks water 12x faster than face grain. Seal with Anchorseal 2 (paraffin wax emulsion) or DEFY Extreme End Grain Sealer immediately after cutting. Skip this and the boards check radially within 2 years.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/fpl_gtr282.pdf" rel="noopener">FPL Wood Handbook Ch. 4 — Moisture Relations and Physical Properties</a></li>
  <li><a href="https://ipeclip.com/" rel="noopener">Ipe Clip Extreme Installation Guide</a></li>
  <li><a href="https://nadra.org/" rel="noopener">NADRA Deck Installation Guidelines</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Speccing an IPE deck? Send the plan view and we will quote with material loss factor and proper expansion gaps built into the BOM.</p>
`.trim()
  },
  {
    slug: "cypress-florida-outdoor-projects-pros-cons-sustainability",
    title: "Cypress for FL outdoor projects — pros, cons, sustainability",
    description:
      "Bald cypress is FL's native rot-resistant softwood. Here is when to spec it, when to skip it, and how to source it from sustainable second-growth mills.",
    excerpt:
      "Bald cypress grew in FL swamps for 5,000 years for a reason. Pros, cons, sustainability — and the second-growth supply chain we buy from.",
    category: "Materials",
    tags: ["cypress", "florida", "native", "sustainable", "siding", "trim"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">Bald cypress (Taxodium distichum) is Florida's native rot-resistant softwood — grew in the Everglades and Big Cypress swamp for millennia. Today's lumber is mostly second-growth from LA, MS, and the FL panhandle. Here is the honest read.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What cypress is good at</h2>
<ul>
  <li><strong class="text-white">Heartwood decay resistance:</strong> Class 2 (resistant) per FPL Wood Handbook. Old-growth heart was Class 1; modern second-growth is solidly Class 2.</li>
  <li><strong class="text-white">Dimensional stability:</strong> tangential shrinkage 6.2%, radial 3.8%. Less movement than most softwoods.</li>
  <li><strong class="text-white">Insect resistance:</strong> the cypressene oil discourages termites and powder-post beetles. Not bulletproof but better than pine.</li>
  <li><strong class="text-white">Weight:</strong> ~32 lbs/cu ft dry — light enough to hand-carry on the job site.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What cypress is NOT good at</h2>
<ul>
  <li><strong class="text-white">Sapwood is not rot-resistant.</strong> Modern mills sell mixed-grain "Select Heart" and "Sap Cypress" — only the heart deserves outdoor use.</li>
  <li><strong class="text-white">UV bleaches it fast.</strong> Unsealed cypress goes silver in 4-6 months in FL sun.</li>
  <li><strong class="text-white">It dents.</strong> Soft enough that pets and patio chairs leave marks.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Where we spec it</h2>
<ul>
  <li><strong class="text-white">Board-and-batten siding</strong> on coastal cottages — looks period-correct, weathers beautifully.</li>
  <li><strong class="text-white">Pergola rafters</strong> when the customer wants warmer wood than PT.</li>
  <li><strong class="text-white">Outdoor trim and corbels</strong> on screened porches.</li>
  <li><strong class="text-white">Buried fence posts</strong> in heartwood-only orders.</li>
</ul>
<p>We do NOT spec cypress for ground-contact when budget allows IPE, and we do NOT spec it for deck surfaces with heavy foot traffic.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Sustainability — the second-growth question</h2>
<p>The old-growth cypress swamps were logged out by 1940. Modern supply is second-growth on 60-80 year rotations from regenerated stands. FSC-certified cypress is available from Goodwin Heart Pine (Micanopy, FL) and Southern Cypress Manufacturers Association (SCMA) member mills. Per the FL Forest Service 2024 sustainability report, in-state cypress is harvested at rates below 60% of growth — supply is sustainable for the next century.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/fpl_gtr282.pdf" rel="noopener">FPL Wood Handbook Ch. 2 — Characteristics and Availability of Commercially Important Woods</a></li>
  <li><a href="https://www.cypressinfo.org/" rel="noopener">Southern Cypress Manufacturers Association (SCMA)</a></li>
  <li><a href="https://www.fdacs.gov/Forest-Wildfire" rel="noopener">FL Forest Service Sustainability Reports</a></li>
  <li><a href="https://www.goodwincompany.com/" rel="noopener">Goodwin Heart Pine — Cypress Supply</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Want cypress on your build? We can source FSC-certified select-heart through our mill partners with a 2-3 week lead.</p>
`.trim()
  },
  {
    slug: "saltwater-dock-construction-pile-driving-batter-piles-jet-pumps",
    title: "Salt-water dock construction — pile driving, batter piles, jet pumps",
    description:
      "Building a salt-water dock means understanding pile driving methods, batter pile geometry, and jet-pump installation. Here is how we engineer FL coastal docks.",
    excerpt:
      "A salt-water dock is a small marine engineering project. Pile driving impact vs jetting, batter pile angles, and how we engineer for FL hurricane storm surge.",
    category: "Construction",
    tags: ["dock", "piles", "marine", "construction", "florida", "engineering"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 7,
    bodyHtml: `
<p class="lead">A residential salt-water dock is small but serious engineering. The piles do the work — driving method, batter angle, and depth all decide whether the dock outlasts hurricane season. Here is what we do.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Pile driving methods</h2>
<ul>
  <li><strong class="text-white">Impact driving:</strong> diesel or hydraulic hammer. Best for cohesive (clay) bottoms. Most accurate depth. Loud — neighbors hear it half a mile away.</li>
  <li><strong class="text-white">Vibratory driving:</strong> hydraulic vibrator clamps the pile and shakes it down. Best for sandy bottoms. Faster but less accurate depth — easy to under-drive.</li>
  <li><strong class="text-white">Jetting:</strong> high-pressure water pump (300-500 psi) liquefies sand around the pile while it sinks under its own weight. Fastest but the pile loses 25-40% of skin friction — must be jetted AND tamped at finish depth.</li>
</ul>
<p>Our default on FL sand bottoms is <em class="text-gold">jet + impact finish</em>: jet to 80% of final depth, then 4-6 impact blows with a 1,500 lb hammer to seat the pile and restore skin friction.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Pile depth — the storm surge math</h2>
<p>FBC R4407 (private docks) requires piles driven to refusal OR a minimum 8 ft below mudline, whichever is deeper. For storm surge resistance we go deeper: ASCE 7-22 Chapter 5 (Flood Loads) calls for embedment = surge height + 6 ft minimum. A 6-ft storm surge dock needs <em class="text-gold">12 ft of embedment</em>. We go 14 ft on every gulf-side build.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Batter piles — the lateral-load fix</h2>
<p>A vertical pile resists vertical load but not much lateral (boat impact, wave action, current). Batter piles — driven at 1:6 to 1:4 angle off vertical — convert lateral load into axial load. Per FBC R4407.5 we batter every 4th pile on a residential dock, alternating direction. On exposed gulf-side piers we batter every other pile.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Pile size and spacing</h2>
<ul>
  <li><strong class="text-white">10" tip diameter CCA-C 2.5 pcf SYP:</strong> standard for 6 ft wide residential dock, 8 ft spacing.</li>
  <li><strong class="text-white">12" tip:</strong> 8 ft wide dock or boat lift support.</li>
  <li><strong class="text-white">14" tip:</strong> commercial pier or pile-supported building.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Permitting</h2>
<p>FL DEP Form 62-330 (Environmental Resource Permit) plus Army Corps of Engineers Section 10 / 404 Nationwide Permit 36 (commercial / recreational docks) on tidal waters. Lead time: 6-12 weeks. We file; the property owner signs. Manatee zones add another 4-8 weeks for FWC review.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://codes.iccsafe.org/content/FLRC2026" rel="noopener">FBC Residential 2026 Section R4407 — Docks and Piers</a></li>
  <li><a href="https://www.asce.org/publications-and-news/asce-7" rel="noopener">ASCE 7-22 Chapter 5 — Flood Loads</a></li>
  <li><a href="https://floridadep.gov/water/submerged-lands-environmental-resources-coordination/content/environmental-resource" rel="noopener">FL DEP Form 62-330 ERP</a></li>
  <li><a href="https://www.saj.usace.army.mil/Missions/Regulatory/" rel="noopener">USACE Jacksonville District NWP 36</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Dock on the planning board? We will pull mudline surveys, current charts, and surge maps before the first sketch.</p>
`.trim()
  },
  {
    slug: "outdoor-kitchen-counters-concrete-teak-sealed-pine",
    title: "Outdoor kitchen counters — concrete vs teak vs sealed pine",
    description:
      "FL outdoor kitchens need counter materials that handle sun, rain, and grease. Honest comparison of cast concrete, end-grain teak, and sealed pine.",
    excerpt:
      "Three counter materials we install in FL outdoor kitchens. Cast concrete, teak butcher block, sealed pine. Heat resistance, cost, lifespan, real maintenance.",
    category: "Materials",
    tags: ["outdoor-kitchen", "counters", "concrete", "teak", "florida"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">Outdoor kitchens get the same abuse as a deck plus the additional load of grill heat, raw food acids, and cleaning chemicals. Here are the three counter materials we install and the call we make for each.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Cast concrete</h2>
<p>4,000-6,000 psi mix, polypropylene fiber reinforced, ground and polished to 800-1500 grit. Sealed with a penetrating siloxane (Prosoco SC-1) plus a sacrificial wax. <em class="text-gold">Heat tolerance: 500°F+ direct contact with no damage.</em> Indefinite lifespan with annual wax.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> $85-$150 / sq ft installed.</li>
  <li><strong class="text-white">Pros:</strong> custom shape, embedded drainage grooves, color through.</li>
  <li><strong class="text-white">Cons:</strong> 12-15 lbs/sq ft — heavy substructure required.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">End-grain teak butcher block</h2>
<p>Teak (Tectona grandis) end-grain stands up to knives — fibers compress instead of cutting. Natural oils block water 30-50% better than face grain. For outdoor kitchens we use 2.5" thick blocks finished with food-safe Odie's Oil + monthly mineral oil.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> $180-$250 / sq ft installed.</li>
  <li><strong class="text-white">Pros:</strong> warmth, knife-friendly, beautiful patina.</li>
  <li><strong class="text-white">Cons:</strong> not heat-resistant — pull hot pans onto a trivet. Re-oil monthly.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Sealed pine — the budget call</h2>
<p>Heart pine (Pinus palustris) sealed with marine epoxy (West System 105/207) then top-coated with food-safe ArmorSeal. Indoor lifespan is decades; outdoor in FL is <em class="text-gold">6-10 years</em> before re-seal. The cheap honest option for utility outdoor counters.</p>
<ul>
  <li><strong class="text-white">Cost:</strong> $45-$80 / sq ft installed.</li>
  <li><strong class="text-white">Pros:</strong> warm look, budget-friendly.</li>
  <li><strong class="text-white">Cons:</strong> not heat-tolerant, requires re-seal every 3-4 years.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What we typically install</h2>
<p>Concrete on the grill side (heat), teak end-grain on the prep side (knives), and we call it a day. The mixed-material approach beats single-material every time on an outdoor kitchen. Cost-balanced, function-balanced.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://www.nsf.org/knowledge-library/food-equipment-materials" rel="noopener">NSF/ANSI 51 — Food Equipment Materials</a></li>
  <li><a href="https://www.fda.gov/food/food-ingredients-packaging" rel="noopener">FDA 21 CFR 178.3650 — Food-Contact Substances</a></li>
  <li><a href="https://prosoco.com/product/sc-1-natural-stone-treatment/" rel="noopener">Prosoco SC-1 Siloxane Sealer TDS</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Outdoor kitchen on the project list? Send us the layout and the appliance brands — we will spec counters per zone.</p>
`.trim()
  },
  {
    slug: "wood-vinyl-aluminum-florida-coastal-fencing",
    title: "Wood vs vinyl vs aluminum for FL coastal fencing",
    description:
      "Coastal FL fences face salt, wind, and HOA rules. Honest comparison of cedar/cypress wood, vinyl, and powder-coated aluminum for FL coastal lots.",
    excerpt:
      "Three fence materials for FL coastal lots. Cedar/cypress wood, PVC vinyl, powder-coated aluminum. Wind ratings, salt resistance, HOA compliance, real-world lifespan.",
    category: "Materials",
    tags: ["fencing", "vinyl", "aluminum", "wood", "florida", "coastal"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">A 6-ft FL coastal fence has to clear three checks: hurricane wind rating, salt-air corrosion resistance, and the HOA aesthetic letter. Here is the comparison across the three materials we install.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Wood — cedar or cypress</h2>
<p>Western red cedar or FL bald cypress, 5/4 pickets on 4×4 PT posts in concrete with standoff base. Sealed with TWP 1500 annually.</p>
<ul>
  <li><strong class="text-white">Lifespan:</strong> 12-20 years on the coast with maintenance.</li>
  <li><strong class="text-white">Wind:</strong> shadow-box style rated to 150 mph per FBC R301 if posts are 8 ft o.c. and concrete-set 36" deep.</li>
  <li><strong class="text-white">Cost:</strong> $35-$55 / linear ft installed.</li>
  <li><strong class="text-white">HOA call:</strong> universal yes for cedar; some HOAs require stain color match.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Vinyl (PVC)</h2>
<p>Bufftech, ActiveYards, CertainTeed — extruded PVC with co-extruded UV cap. Zero salt corrosion, zero rot. Fades slightly over 15-20 years; brittle in low temps (irrelevant in FL).</p>
<ul>
  <li><strong class="text-white">Lifespan:</strong> 25-35 years.</li>
  <li><strong class="text-white">Wind:</strong> good vinyl is rated to 130-160 mph per ASTM F964; cheap vinyl panels blow apart in tropical storms.</li>
  <li><strong class="text-white">Cost:</strong> $40-$70 / linear ft installed.</li>
  <li><strong class="text-white">HOA call:</strong> often restricted to white or tan; check rules before ordering.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Powder-coated aluminum</h2>
<p>6063-T5 aluminum extrusion, 0.060" wall minimum, AAMA 2604 powder coat (5-7 year fade warranty, 20+ year real-world). The premium pool-code-compliant fence — also satisfies FL pool barrier requirements (FBC 454.2.17).</p>
<ul>
  <li><strong class="text-white">Lifespan:</strong> 30-50 years.</li>
  <li><strong class="text-white">Wind:</strong> 150 mph standard rating; open pattern reduces sail effect.</li>
  <li><strong class="text-white">Cost:</strong> $55-$95 / linear ft installed.</li>
  <li><strong class="text-white">HOA call:</strong> universally accepted; black is the default.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The salt-air call</h2>
<p>Within 1,500 ft of saltwater we recommend powder-coated aluminum first, vinyl second, wood only if HOA requires it. AAMA 2604 powder coat passes 2,000 hours salt-spray (ASTM B117); cheaper AAMA 2603 fails at ~1,000 hours. Always ask for the AAMA spec.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://codes.iccsafe.org/content/FLBC2026" rel="noopener">FBC 2026 Section 454.2.17 — Pool Barriers</a></li>
  <li><a href="https://www.astm.org/f0964-13r19.html" rel="noopener">ASTM F964 — PVC Fence Panel Wind Loads</a></li>
  <li><a href="https://aamanet.org/" rel="noopener">AAMA 2604 — High-Performance Organic Coatings</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Fencing a coastal lot? Tell us the salt-water distance and the HOA — we will narrow it to two options.</p>
`.trim()
  },
  {
    slug: "boat-dock-decking-traditional-planks-vs-permadeck-composite",
    title: "Boat dock decking: traditional planks vs Permadeck composite",
    description:
      "Boat dock decking takes UV, fish guts, dropped tackle, and storm surge. Real comparison of PT pine planks vs Permadeck and other marine composites.",
    excerpt:
      "Two ways to deck a FL boat dock. Traditional PT pine vs Permadeck-style marine composite. Hot underfoot, slippery wet, full-sun lifespan — the honest comparison.",
    category: "Materials",
    tags: ["dock", "decking", "permadeck", "composite", "florida", "marine"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">Dock decking is a different problem than backyard decking. UV is harsher (water reflects), wet feet are mandatory, and fish-blood + sunscreen attack the surface. Here is the call.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Traditional PT pine planks</h2>
<p>5/4×6 UC4A southern yellow pine, 1/4" gaps, stainless ring-shank nails or screws into the joist. The default for FL boat docks for 60 years.</p>
<ul>
  <li><strong class="text-white">Pros:</strong> cheap, fast, replaceable plank-by-plank, less hot underfoot than composite (~120°F vs 150°F at noon).</li>
  <li><strong class="text-white">Cons:</strong> splinters at year 3-4, requires re-stain every 2 years, surface mildew in humid microclimates.</li>
  <li><strong class="text-white">Lifespan:</strong> 10-15 years with maintenance.</li>
  <li><strong class="text-white">Cost:</strong> $14-$22 / sq ft installed.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Permadeck and marine-rated composites</h2>
<p>Permadeck, GatorDock, ThruFlow — extruded PVC or HDPE with through-flow grates that let water and debris pass. Designed specifically for marine use. <em class="text-gold">Through-flow composites are now our default</em> on new builds.</p>
<ul>
  <li><strong class="text-white">Pros:</strong> never splinters, zero maintenance, debris falls through, lifetime structural warranty (most brands).</li>
  <li><strong class="text-white">Cons:</strong> hot underfoot (light colors mandatory in FL — white or tan only), 2.5x cost of PT pine.</li>
  <li><strong class="text-white">Lifespan:</strong> 30+ years.</li>
  <li><strong class="text-white">Cost:</strong> $35-$55 / sq ft installed.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The hot-deck math</h2>
<p>Per ASHRAE 55-2020 thermal comfort, surface temperatures above 140°F cause skin burn in <2 seconds. Capped composite in direct FL noon sun hits 145-160°F (light colors stay 25-30°F cooler than dark). Through-flow grates run 10-15°F cooler than solid composite because air flows under and through. PT pine peaks ~120°F.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The fish-blood test</h2>
<p>Permadeck and through-flow grates rinse to bare PVC with a 5-second hose pass. PT pine absorbs the stain — by year 3 it looks like a butcher block. For active fishermen we recommend composite. For pleasure docks the pine looks more traditional and the staining is part of the look.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://awpa.com/standards/" rel="noopener">AWPA U1-22 — Marine Use Categories</a></li>
  <li><a href="https://www.ashrae.org/technical-resources/bookstore/standard-55-thermal-environmental-conditions" rel="noopener">ASHRAE 55-2020 — Thermal Environmental Conditions</a></li>
  <li><a href="https://www.permadeck.com/" rel="noopener">Permadeck Installation Specifications</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Re-decking an existing dock? Send the dimensions — we can quote both options side by side.</p>
`.trim()
  },
  {
    slug: "florida-wood-borer-prevention-termites-powder-post-carpenter-bees",
    title: "FL wood-borer prevention — termites, powder-post beetles, carpenter bees",
    description:
      "Three insect threats to FL outdoor wood: Formosan termites, powder-post beetles, carpenter bees. Identification, prevention, treatment — what works.",
    excerpt:
      "Three FL wood-borer threats. Formosan subterranean termite, anobiid powder-post beetle, eastern carpenter bee. ID, prevention, treatment — what works in the field.",
    category: "Maintenance",
    tags: ["termites", "wood-borers", "carpenter-bees", "pest", "florida"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 7,
    bodyHtml: `
<p class="lead">FL hosts three serious wood-borers. Each takes a different prevention approach. Here is what we treat for on every outdoor build, and what we tell customers to watch for.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Formosan subterranean termite (Coptotermes formosanus)</h2>
<p>The bad one. Established in coastal FL since the 1980s. A mature colony eats 1 lb of wood per day. Mud tubes are the ID — pencil-thick tunnels of soil and saliva on foundation walls.</p>
<ul>
  <li><strong class="text-white">Prevention:</strong> AWPA UC4 PT lumber for any wood within 18" of soil, plus a chemical barrier (Termidor SC fipronil) at construction.</li>
  <li><strong class="text-white">Detection:</strong> Sentricon or Trelona ATBB bait stations 10 ft o.c. around the perimeter.</li>
  <li><strong class="text-white">Treatment:</strong> if active — local injection of Termidor + bait stations. Whole-structure fumigation only if hidden infestation.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Powder-post beetles (Anobiidae, Lyctidae)</h2>
<p>Two families. <em class="text-gold">Anobiidae</em> attack softwoods (PT pine, cypress). <em class="text-gold">Lyctidae</em> attack hardwoods with large pores (oak, hickory, ash). Detection: pin-sized exit holes (1/16"-1/8") with fine powdery frass below them.</p>
<ul>
  <li><strong class="text-white">Prevention:</strong> keep wood MC below 12% (most beetles need >15% MC to lay eggs). Penetrating sealers (TWP, Cutek) block egg-laying mechanically.</li>
  <li><strong class="text-white">Detection:</strong> fresh frass = active. Old frass = past. Tap and listen.</li>
  <li><strong class="text-white">Treatment:</strong> Bora-Care (disodium octaborate tetrahydrate) sprayed on unfinished wood. Penetrates 1/4" — kills larvae in situ. EPA-registered, low toxicity.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Eastern carpenter bee (Xylocopa virginica)</h2>
<p>Females drill perfectly round 3/8" holes into soffits, fascia, pergola rafters. They prefer untreated softwoods — cedar, cypress, pine. Damage is usually cosmetic but woodpecker pursuit can expand the gallery into structural loss.</p>
<ul>
  <li><strong class="text-white">Prevention:</strong> paint or solid-stain the wood. Carpenter bees skip painted surfaces. PT lumber: deterrent but not absolute.</li>
  <li><strong class="text-white">Treatment:</strong> dust the hole with diatomaceous earth or boric acid powder, plug with dowel after 48 hours. Spring application catches new females.</li>
  <li><strong class="text-white">Note:</strong> carpenter bees are important native pollinators; treat the wood, not the bees, when possible.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://edis.ifas.ufl.edu/" rel="noopener">UF IFAS Extension — Wood-Boring Pests</a></li>
  <li><a href="https://www.epa.gov/pesticide-registration" rel="noopener">EPA Termidor SC Registration (CAS 120068-37-3 fipronil)</a></li>
  <li><a href="https://www.fpl.fs.usda.gov/" rel="noopener">FPL — Insects That Damage Wood in Service</a></li>
  <li><a href="https://www.fdacs.gov/Consumer-Resources/Pesticides/Structural-Pest-Control" rel="noopener">FL FDACS Structural Pest Control Rules</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Notice fresh holes or mud tubes? Send 2 close-up photos — we can usually tell from the frass which species and how aggressive.</p>
`.trim()
  },
  {
    slug: "outdoor-furniture-survives-atlantic-hurricanes",
    title: "Building outdoor furniture that survives Atlantic hurricanes",
    description:
      "Outdoor furniture that survives a 130 mph wind event. Material weight, fastening, tie-down strategy, and ASCE 7-22 design loads for FL coastal pieces.",
    excerpt:
      "Most outdoor furniture becomes flying debris in a Cat 3. Here is how we design and build pieces that ride out Atlantic hurricanes — material weight, fastening, tie-down anchors.",
    category: "Construction",
    tags: ["outdoor-furniture", "hurricane", "wind-load", "florida", "atlantic"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 7,
    bodyHtml: `
<p class="lead">A 50-lb Adirondack chair in a 130 mph wind becomes a wrecking ball. Most FL homeowners drag chairs inside before the storm — but some pieces are too heavy or built-in. Here is how we design hurricane-survivable outdoor furniture.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The wind-load problem</h2>
<p>Per ASCE 7-22 Chapter 29 (Building Appurtenances and Other Structures), free-standing objects in a 150 mph Exposure C zone experience ~45 psf design pressure. A 30" tall chair with 6 sq ft of windward area sees 270 lbs of horizontal load. <em class="text-gold">A 50-lb chair flips at any wind above 65 mph.</em></p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Strategy 1 — make it heavy</h2>
<ul>
  <li><strong class="text-white">Material:</strong> IPE, cumaru, garapa — all 65-75 lbs/cu ft dry. A 60-lb solid IPE chair stays put through tropical-storm winds.</li>
  <li><strong class="text-white">Massing:</strong> aggregate furniture into a single heavier piece (dining set with bench) — wind capture per pound drops.</li>
  <li><strong class="text-white">Caveat:</strong> still relocate before a Cat 2+ landfall.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Strategy 2 — tie it down</h2>
<p>Built-in benches, pergola swings, dining tables on a covered porch — we design with hurricane straps that connect the furniture to the structure or slab.</p>
<ul>
  <li><strong class="text-white">Concealed straps:</strong> Simpson MSTA strap from underside of bench to floor joist or sleeper.</li>
  <li><strong class="text-white">Anchor-bolt mounts:</strong> 3/8" stainless lag screws into concrete with Hilti HIT-RE 500 epoxy — pull-out strength 4,000 lbs per anchor.</li>
  <li><strong class="text-white">Drop-in pins:</strong> hidden steel pins into pre-drilled deck — removable for cleaning, locked-in for storms.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Strategy 3 — minimize sail area</h2>
<p>Open-back chairs (Adirondack, ladderback) catch <em class="text-gold">half</em> the wind of solid-back chairs (Cape Cod). Slat tables vs solid tables — slat wins. Aerodynamic profile matters more than people think; per Cermak Peterka Petersen wind tunnel studies, an Adirondack catches ~3.5 sq ft effective area vs ~5.5 for a solid-back lounger.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The reality — pre-storm protocol</h2>
<p>Even our heaviest builds get the same advice: at 72 hours from landfall of a Cat 2+, move furniture inside or to a leeward wall. Hurricane straps are for the once-a-decade fast-moving Cat 1 that no one saw coming. <em class="text-gold">Design for the unexpected; respect the forecast.</em></p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://www.asce.org/publications-and-news/asce-7" rel="noopener">ASCE 7-22 Chapter 29 — Wind Loads on Other Structures</a></li>
  <li><a href="https://codes.iccsafe.org/content/FLRC2026" rel="noopener">FBC 2026 R301.2.1 — Wind Loads</a></li>
  <li><a href="https://www.strongtie.com/" rel="noopener">Simpson Strong-Tie Anchor Specifications</a></li>
  <li><a href="https://www.nhc.noaa.gov/" rel="noopener">NOAA NHC — Hurricane Wind Scale</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Commissioning built-in outdoor furniture? We will spec tie-downs as part of the design at no upcharge.</p>
`.trim()
  },
  {
    slug: "repairing-storm-damaged-decks-keep-replace",
    title: "Repairing storm-damaged decks — what to keep, what to replace",
    description:
      "Post-hurricane deck triage. How to evaluate what survived structurally, what is cosmetic, what needs the chainsaw, and what the insurance adjuster will pay for.",
    excerpt:
      "After Idalia, Helene, Milton — the calls came in. Here is our triage process for storm-damaged decks: what to keep, what to replace, what insurance covers.",
    category: "Repair",
    tags: ["storm-damage", "repair", "insurance", "hurricane", "florida"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 7,
    bodyHtml: `
<p class="lead">After a hurricane the phone rings non-stop. Some decks need a chainsaw and a dumpster. Some need one screw. Here is the triage process we run on every storm-damage call.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Step 1 — structural assessment from below</h2>
<p>Before touching the deck surface we inspect from underneath. We are looking for:</p>
<ul>
  <li><strong class="text-white">Ledger pull:</strong> any visible separation between ledger and house = condemn-and-replace, full stop. FBC R507.9 fail.</li>
  <li><strong class="text-white">Joist hangers:</strong> bent, twisted, or with bent nails = replace the hanger.</li>
  <li><strong class="text-white">Post bases:</strong> shifted off the standoff = re-anchor or replace.</li>
  <li><strong class="text-white">Beam splits:</strong> any split through more than 1/3 of the beam depth = replace the beam.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Step 2 — fastener pull test</h2>
<p>Surface screws that have lifted ~1/8"+ have lost holding power. Per ANSI/AF&amp;PA NDS Withdrawal values, a #10 stainless screw at 1.5" embedment pulls ~150 lbs new and ~70-80 lbs after fastener fatigue from wind cycling. We sample-test 10% of screws on the windward edge — if more than 20% fail to re-seat, the whole field gets new fasteners.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Step 3 — board-by-board call</h2>
<ul>
  <li><strong class="text-white">Cracked but seated:</strong> can stay if crack does not run >50% across the board. Seal with end-grain sealer at the crack.</li>
  <li><strong class="text-white">Cupped or twisted:</strong> if more than 1/4" of cup across 5.5", replace.</li>
  <li><strong class="text-white">Sheared at fastener:</strong> replace.</li>
  <li><strong class="text-white">Composite cap delamination:</strong> replace the board (cap separation is the failure mode that compounds).</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Step 4 — railing systems</h2>
<p>Per FBC R312, railings must withstand 200 lbs concentrated load + 50 plf uniform load. Post-storm we pull every post laterally with a strap gauge to that spec. If any post fails, the entire run gets re-anchored. Top-rail caps that have loosened are non-structural but get re-screwed with longer fasteners (going one size up).</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The insurance call</h2>
<p>Florida insurance under FS 627.4137 requires named-storm wind damage coverage on most policies. Documentation matters: we send the customer a written assessment with FBC code references and photos of every failed connection. Adjusters who see "FBC R507.9.1.3 — ledger separation, ASCE 7-22 design load exceeded" pay faster than the ones who get "looks bad to me." <em class="text-gold">Code citation is leverage.</em></p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://codes.iccsafe.org/content/FLRC2026" rel="noopener">FBC Residential 2026 — R312 Guards / R507 Decks</a></li>
  <li><a href="https://awc.org/codes-standards/publications/nds-2024" rel="noopener">ANSI/AWC NDS 2024 — Fastener Withdrawal Tables</a></li>
  <li><a href="https://www.flsenate.gov/Laws/Statutes/2024/627.4137" rel="noopener">FL Statutes 627.4137 — Insurance Coverage Disclosures</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Storm-damaged deck? Send 6-10 photos (above + below) and we will return a written triage usually same-day during storm season.</p>
`.trim()
  },
  {
    slug: "teak-cumaru-garapa-outdoor-furniture-comparison",
    title: "Choosing between teak, cumaru, and garapa for outdoor furniture",
    description:
      "Three tropical hardwoods, three price points, three personalities. Honest comparison of teak, cumaru, and garapa for FL outdoor furniture.",
    excerpt:
      "Teak is the legend. Cumaru is the bargain. Garapa is the wildcard. Real comparison of hardness, color, oil content, sustainability, and price for FL outdoor furniture.",
    category: "Materials",
    tags: ["teak", "cumaru", "garapa", "hardwood", "outdoor-furniture", "florida"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">Three tropical hardwoods we stock for outdoor furniture. Each has a clear use case. Here is the honest read on teak, cumaru, and garapa.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Teak (Tectona grandis) — the legend</h2>
<ul>
  <li><strong class="text-white">Janka:</strong> 1,070 lbf.</li>
  <li><strong class="text-white">Decay class:</strong> Class 1 — very durable.</li>
  <li><strong class="text-white">Natural oils:</strong> high silica + tectoquinones — the reason for boat-deck reputation.</li>
  <li><strong class="text-white">Color:</strong> warm honey-brown, weathers silver.</li>
  <li><strong class="text-white">Cost:</strong> $25-$45 / bf (plantation Burmese; lower for Indonesian).</li>
  <li><strong class="text-white">Sustainability:</strong> FSC-certified plantation supply is sustainable. Old-growth Burmese teak — avoid, often illegally logged.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Cumaru (Dipteryx odorata) — the bargain</h2>
<ul>
  <li><strong class="text-white">Janka:</strong> 3,330 lbf — over 3x teak.</li>
  <li><strong class="text-white">Decay class:</strong> Class 1.</li>
  <li><strong class="text-white">Natural oils:</strong> high, with the same coumarin compounds that give it the "Brazilian teak" nickname (and a vanilla scent when freshly milled).</li>
  <li><strong class="text-white">Color:</strong> medium-to-dark brown with reddish undertones, weathers gray.</li>
  <li><strong class="text-white">Cost:</strong> $10-$18 / bf.</li>
  <li><strong class="text-white">Sustainability:</strong> FSC-certified supply from managed Amazon concessions. Check for FSC chain-of-custody (IFA Trees, Tigerwood Tropical, Trinity Hardwoods all carry).</li>
</ul>
<p>If teak's looks are not the point and you want maximum durability per dollar, cumaru wins.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Garapa (Apuleia leiocarpa) — the wildcard</h2>
<ul>
  <li><strong class="text-white">Janka:</strong> 1,820 lbf.</li>
  <li><strong class="text-white">Decay class:</strong> Class 2 — durable.</li>
  <li><strong class="text-white">Natural oils:</strong> moderate. Less than teak or cumaru.</li>
  <li><strong class="text-white">Color:</strong> light golden-yellow, weathers to soft gray.</li>
  <li><strong class="text-white">Cost:</strong> $7-$12 / bf.</li>
  <li><strong class="text-white">Sustainability:</strong> FSC-certified through Tropical Forest Trust members.</li>
</ul>
<p>Garapa is the lightest-color of the three — useful when you want a warmer FL beach-cottage look without going to cedar's softness. Lifespan is 15-20 years vs 25-40 for cumaru, vs 30-50 for teak.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Our default picks</h2>
<ul>
  <li><strong class="text-white">Customer wants "teak" look + has the budget:</strong> teak.</li>
  <li><strong class="text-white">Customer wants the longest-lasting hardwood at moderate cost:</strong> cumaru.</li>
  <li><strong class="text-white">Customer wants a lighter color that weathers naturally:</strong> garapa.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/fpl_gtr282.pdf" rel="noopener">FPL Wood Handbook — Tropical Hardwoods</a></li>
  <li><a href="https://us.fsc.org/" rel="noopener">FSC US — Chain-of-Custody Search</a></li>
  <li><a href="https://cites.org/" rel="noopener">CITES Appendix Listings — Tropical Timber</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Picking a hardwood for a custom piece? We will share FSC chain-of-custody docs with the quote.</p>
`.trim()
  },
  {
    slug: "florida-lumber-supply-chain-local-mills-sustainable-sourcing",
    title: "Florida lumber supply chain — local mills and sustainable sourcing",
    description:
      "Where the wood actually comes from. FL lumber supply chain mapped — local mills, sustainable forestry, what to ask before you buy.",
    excerpt:
      "The lumberyard is the last stop, not the source. Here is the FL lumber supply chain — local mills, sustainable forestry, FSC certification, what we ask before we buy.",
    category: "Materials",
    tags: ["supply-chain", "mills", "sustainable", "fsc", "florida", "sourcing"],
    publishedAt: "2026-06-01",
    author: "JB Woodworks",
    readingTimeMinutes: 6,
    bodyHtml: `
<p class="lead">Most FL lumber arrives via Lowe's, Home Depot, or a local building-supply yard. Behind them is a multi-step supply chain that decides what species, what grade, and what sustainability story comes with the wood. Here is the map.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The four-step chain</h2>
<ol>
  <li><strong class="text-white">Forest:</strong> southern pine plantations across FL/GA/AL/MS; cypress from FL panhandle + LA swamps.</li>
  <li><strong class="text-white">Mill:</strong> rough lumber sawn, kiln-dried (or air-dried), graded to SPIB or NHLA rules.</li>
  <li><strong class="text-white">Treatment plant:</strong> ACQ, MCA, or CCA pressure-treatment via Osmose, Koppers, or Arch.</li>
  <li><strong class="text-white">Distributor/retail:</strong> 84 Lumber, Sherwood, ProBuild, or direct to box stores.</li>
</ol>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">FL local mills we buy from</h2>
<ul>
  <li><strong class="text-white">Goodwin Heart Pine (Micanopy):</strong> reclaimed heart pine and FSC cypress.</li>
  <li><strong class="text-white">Mid-State Lumber (Mulberry):</strong> southern yellow pine, locally milled and KD'd.</li>
  <li><strong class="text-white">Pittman Lumber (Daytona Beach):</strong> rough cypress, locally sourced.</li>
  <li><strong class="text-white">Trinity Hardwoods (Sarasota):</strong> imported tropical hardwoods with FSC chain-of-custody.</li>
  <li><strong class="text-white">Southern Cypress Manufacturers Association (SCMA):</strong> directory of FSC member mills.</li>
</ul>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">What "FSC certified" actually means</h2>
<p>Forest Stewardship Council certification covers three levels: FSC 100% (all wood from certified forests), FSC Mix (≥70% certified + controlled wood), and FSC Recycled. For outdoor projects we accept FSC 100% or FSC Mix. <em class="text-gold">"FSC controlled wood"</em> alone is the weakest tier — usable but not the gold standard.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">Domestic vs imported</h2>
<p>Per the FL Forest Service 2024 Strategic Plan, FL has 17 million acres of timberland — about 50% of the state. Domestic supply for southern pine, cypress, and oak is robust. We import only tropical hardwoods (teak, cumaru, garapa, IPE). For those we require: (1) FSC chain-of-custody, (2) Lacey Act compliance documentation, (3) CITES clearance where applicable.</p>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">The five questions we ask every mill</h2>
<ol>
  <li>What is the species and grade rule (SPIB, NHLA, WCLIB)?</li>
  <li>Kiln-dried or air-dried, and to what MC%?</li>
  <li>FSC certificate number?</li>
  <li>For PT — what retention level and treatment chemistry?</li>
  <li>Lead time and minimum order?</li>
</ol>

<h2 class="font-display text-[clamp(1.6rem,3.2vw,2.2rem)] text-white mt-12 mb-4">References</h2>
<ul>
  <li><a href="https://us.fsc.org/find-products" rel="noopener">FSC US Certificate Search</a></li>
  <li><a href="https://www.fdacs.gov/Forest-Wildfire/Florida-Forest-Service" rel="noopener">FL Forest Service Strategic Plan</a></li>
  <li><a href="https://spib.org/" rel="noopener">Southern Pine Inspection Bureau (SPIB) Grading Rules</a></li>
  <li><a href="https://www.aphis.usda.gov/aphis/ourfocus/planthealth/import-information/lacey-act" rel="noopener">USDA APHIS Lacey Act Compliance</a></li>
</ul>

<p class="mt-8 text-cream-30 italic">Want FSC-certified wood on your project? Tell us the species and we will source through certified mills only, with paperwork.</p>
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
