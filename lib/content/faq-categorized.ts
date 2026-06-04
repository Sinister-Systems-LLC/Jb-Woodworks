// Author: RKOJ-ELENO :: 2026-05-24
// Categorized FAQ for the home + about FAQ sections. Layout mirrors the
// tabbed pattern used elsewhere in our portfolio: a pill bar of categories
// across the top, an accordion list below that re-renders when the tab
// changes. Replaces the older flat lib/content/faq.json for the home page
// (faq.json stays around for any legacy consumers).
//
// To add a question: append to the right category array. Tabs only render
// when their array has items — adding a new category is just adding a key.

export type FaqCategory = {
  id: string;
  label: string;
  /** SVG path data for the tab icon. Heroicons 24/outline style. */
  iconPath: string;
  items: { q: string; a: string }[];
};

export const faqCategorized: FaqCategory[] = [
  {
    id: "general",
    label: "General",
    iconPath:
      "M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z",
    items: [
      {
        q: "Where are you located, and how far do you travel?",
        a: "Orlando is home base, but we cover the full surrounding area — Winter Park, Maitland, Apopka, Sanford, Kissimmee, Lake Mary, Clermont, Windermere, and out to the coast for the right job. For larger commercial and event-fabrication work we travel further; ask and we will tell you straight whether it pencils out."
      },
      {
        q: "What is the best way to start a project with you?",
        a: "Call (407) 561-1453, email jbwoodworks8@gmail.com, or use the contact form on this site. Free estimates, no obligation, same-day response on weekdays. Send a few photos of the space if you have them — we can usually shoot back a rough range before we even visit."
      },
      {
        q: "Do I need to be home during the build?",
        a: "Not for most days. We coordinate the start date, walk the site with you on day one, and check in by text or photo for material approvals and milestone decisions. Walk-through and final sign-off are the two days we ask you to be available. We respect your time — we are not going to camp on your driveway."
      },
      {
        q: "Can you repair or restore instead of replacing?",
        a: "Often yes, and we will tell you straight whether it makes financial sense. Dock board replacement, rail repair, deck restaining, furniture refinishing, and water-damage repair are all on the menu. If a piece is not worth the cost of restoration we will say so and refund the consult fee. We would rather lose that job than build you something that does not deserve our name."
      },
      {
        q: "How long have you been doing this?",
        a: "JB Woodworks has been in business since 2025, building decks, docks, pergolas, custom furniture, and commercial fabrication out of Orlando. Every project is designed and built in-house — no subcontracted crews, no shortcuts on materials, no surprises mid-build."
      }
    ]
  },
  {
    id: "process",
    label: "Process",
    iconPath:
      "M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z",
    items: [
      {
        q: "How long from the first call to walking on it?",
        a: "Residential decks and pergolas usually go from signed quote to walk-through in 2-4 weeks. Custom pool tables take 4-8 weeks because slate, felt, and hardwood frame sourcing dictates the schedule. Boat docks and commercial / event fabrication book 6-10 weeks out depending on permits. We will give you a realistic date on the quote, not a sales date."
      },
      {
        q: "Do you pull permits?",
        a: "Yes. Decks over 30 inches, structural pergolas, all dock work, and most outdoor living spaces in Orange County require a permit. We submit the drawings, pay the fees, and schedule the inspections. The cost lives on a separate line on your quote so you can see exactly what the city is charging."
      },
      {
        q: "Do you handle design too, or just build?",
        a: "Both. For most residential builds we sketch a concept based on the space and a quick conversation about how you actually use it. For commercial and event fabrication we can work from your architect or set-designer drawings, or design from a brief and a brand book. Either way you see drawings and material samples before any wood gets cut."
      },
      {
        q: "What happens on install day?",
        a: "We arrive with the crew, the materials, the tools, and a plan. We tarp the work area, protect adjacent surfaces, set up dust control where it matters, and stage materials so the site stays walkable. At end of day the site is swept and safe. The crew lead checks in with you on milestones — material approvals, finish choices, anything that needs a yes/no."
      }
    ]
  },
  {
    id: "pricing",
    label: "Pricing & Quotes",
    iconPath:
      "M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z",
    items: [
      {
        q: "What does a typical project cost?",
        a: "Pricing comes back inside one business day after we see the space. We work fixed-bid whenever we can. Decks generally run $35-$60 per square foot installed depending on material; pergolas $4,000-$15,000; custom dock builds $20,000+ depending on length, pilings, and shoreline. Furniture and pool tables are priced per piece. Every quote breaks down materials, labor, permits, and cleanup so there are no surprises later."
      },
      {
        q: "What is the deposit and payment schedule?",
        a: "Standard schedule is 30% on contract to secure your spot and order materials, 40% the morning materials are delivered to the site, and 30% on walk-through approval when you sign off. Cash, check, ACH, and Zelle accepted; cards on request (a 3% processor fee applies). We do not start fabrication until the deposit clears."
      },
      {
        q: "Are estimates really free, with no obligation?",
        a: "Yes. We come out, look at the space, ask about how you use it, and follow up inside one business day with a written quote. No commitment to move forward. If the project is too small or outside our lane we will say so and point you to a friend who fits better."
      },
      {
        q: "Can I phase the project across budgets?",
        a: "Yes — large projects routinely get split into phases (e.g. dock pilings + framing this year, decking + roof next year). We design each phase so the next one drops in cleanly. You only pay for what you authorize."
      }
    ]
  },
  {
    id: "materials",
    label: "Materials",
    iconPath:
      "M20.25 7.5l-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z",
    items: [
      {
        q: "What kind of wood and materials do you use?",
        a: "Outdoor: pressure-treated southern yellow pine, western red cedar, or composite (Trex, TimberTech, Azek) — your call, we will price all three. Marine-grade stainless hardware on every dock. Indoor furniture and trim: hardwoods (oak, walnut, cherry, maple) or paint-grade poplar. We list the exact spec on the quote so there is zero ambiguity about what arrives on your driveway."
      },
      {
        q: "What kind of warranty do you offer?",
        a: "One-year full workmanship warranty on every build — if a board pops, a fastener fails, or a joint opens up under normal use, we come back and fix it. Material warranties pass through from the manufacturer: Trex/TimberTech composite carries a 25-50 year residential warranty, marine-grade stainless typically 10+ years. We hand over copies of all manufacturer paperwork at the walk-through."
      },
      {
        q: "Can I bring my own materials?",
        a: "Sometimes, depending on the piece and the source. For unique slabs, family hardwoods, or specialty stone we will absolutely work them in. For structural lumber and composite decking we typically want to source the materials ourselves so the warranty chain stays intact. We will tell you straight which makes sense on your project."
      },
      {
        q: "What is the difference between the composite brands?",
        a: "We wrote a full breakdown of Trex vs. TimberTech vs. Azek on the blog — heat retention, fade resistance, warranty fine print, and what we actually install on most Orlando decks. Short version: we lead with TimberTech AZEK Reserve for the cost-to-lifespan balance, Azek Vintage when budget is open, Trex Transcend when budget is tight."
      }
    ]
  },
  {
    id: "services",
    label: "Services",
    iconPath:
      "M11.42 15.17 17.25 21A2.652 2.652 0 0 0 21 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 1 1-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 0 0 4.486-6.336l-3.276 3.277a3.004 3.004 0 0 1-2.25-2.25l3.276-3.276a4.5 4.5 0 0 0-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085m-1.745 1.437L5.909 7.5H4.5L2.25 3.75l1.5-1.5L7.5 4.5v1.409l4.26 4.26m-1.745 1.437 1.745-1.437m6.615 8.206L15.75 15.75M4.867 19.125h.008v.008h-.008v-.008Z",
    items: [
      {
        q: "Do you handle commercial fabrication and event builds?",
        a: "Yes — it is one of our core lanes. Custom branded displays, retail installations, feature walls, locker systems, pop-up and reveal builds, specialty commercial commissions. Recent work includes the New Balance × Foot Locker reveal and the SKU Snipers retail display. Built in-shop, installed on-site, photographable from day one. Send the spec and the deadline; we will tell you fast whether we can hit it."
      },
      {
        q: "Can you work on existing structures, or only new builds?",
        a: "Both. We do new builds, full re-decks on existing framing, pergola retrofits onto existing patios, dock board and piling replacement, furniture refinishing, and porch column wraps. We will assess the substructure first — if the existing framing is sound, we save you the cost of rebuilding it. If it is not, we will tell you why and lay out the options."
      },
      {
        q: "Do you handle only big projects, or small repairs too?",
        a: "Both, with one honest caveat: very small repairs (a single rail post, one broken board) sometimes do not justify a truck roll. We are upfront about that on the call. For anything that needs more than an hour on-site, we are happy to quote it."
      },
      {
        q: "Do you only work residential, or also commercial?",
        a: "Both. Residential is most of our volume (decks, docks, pergolas, outdoor living, custom furniture, pool tables). Commercial and event fabrication is a fast-growing lane — retail displays, brand reveals, pop-ups, feature installs. Same shop, same standard, same crew."
      }
    ]
  }
] as const;

/** Flat fallback for components that have not migrated to the categorized
 *  shape yet. Order: concatenated by category, in the order above. */
export const faqFlat = faqCategorized.flatMap((c) => c.items);
