// Author: RKOJ-ELENO :: 2026-05-23
// JB Woodworks - global site facts, threaded everywhere via the SITE constant.

export const SITE = {
  name: "JB Woodworks",
  tagline: "Custom decks, docks, furniture, and outdoor builds — Orlando, FL since 2025.",
  subtagline:
    "Residential craftsmanship and commercial fabrication, all built custom in-house: decks, docks, pergolas, outdoor living, hardwoods, custom furniture, plus branded displays and event builds.",
  phone: "(407) 561-1453",
  phoneTel: "4075611453",
  email: "jbwoodworks8@gmail.com",
  serviceArea: "Orlando, Florida and surrounding areas",
  socials: {
    instagram: "https://www.instagram.com/jb.woodworkss",
    facebook: "https://www.facebook.com/people/JB-Woodworks/61581118061434",
    tiktok: "https://www.tiktok.com/@jbwoodworks_",
    twitter: "https://x.com/jbwoodworks8"
  },
  url: process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"
} as const;
