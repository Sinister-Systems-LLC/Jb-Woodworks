// Author: RKOJ-ELENO :: 2026-06-01
// v2: Contact form v2 — project type, zip code, timeline, budget.
// Backwards-compatible with /api/contact (extra fields are accepted/ignored gracefully).
"use client";
import { useState, useEffect, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";

type State = "idle" | "submitting" | "success" | "error";

export function ContactFormV2() {
  const router = useRouter();
  const params = useSearchParams();
  const [state, setState] = useState<State>("idle");
  const [errMsg, setErrMsg] = useState<string>("");
  const [serviceHint, setServiceHint] = useState<string>("");

  useEffect(() => {
    const svc = params.get("service");
    if (svc) setServiceHint(svc.replace(/-/g, " "));
  }, [params]);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setState("submitting");
    setErrMsg("");
    const form = e.currentTarget;
    const data = new FormData(form);
    try {
      const res = await fetch("/api/contact", { method: "POST", body: data });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.error || `HTTP ${res.status}`);
      }
      setState("success");
      form.reset();
      router.push("/contact/thanks");
    } catch (err) {
      setState("error");
      setErrMsg(err instanceof Error ? err.message : "Send failed. Please call us directly.");
    }
  }

  return (
    <motion.form
      onSubmit={onSubmit}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="bg-ink-3 border border-line p-9 rounded-xl flex flex-col gap-5 relative overflow-hidden"
      noValidate
    >
      <div aria-hidden className="absolute -top-24 -right-24 w-[260px] h-[260px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(58,124,165,0.10), transparent 70%)" }} />

      <Field label="Name" name="name" required autoComplete="name" />
      <div className="grid sm:grid-cols-2 gap-5">
        <Field label="Email address" name="email" type="email" required autoComplete="email" />
        <Field label="Phone number" name="phone" type="tel" autoComplete="tel" />
      </div>

      <div className="grid sm:grid-cols-2 gap-5">
        <div className="flex flex-col gap-2">
          <label htmlFor="service" className="text-[0.78rem] font-semibold tracking-wider uppercase text-cream-50">Project type</label>
          <select id="service" name="service" defaultValue={serviceHint ? params.get("service") || "" : ""} className="bg-white/5 border border-line-strong rounded-md px-4 py-3.5 text-white text-[0.95rem] focus:outline-none focus:border-coastal focus:ring-4 focus:ring-coastal/15 transition">
            <option value="">- Select -</option>
            <option value="custom-decks">Deck (new build)</option>
            <option value="docks">Dock / boardwalk</option>
            <option value="pergolas">Pergola / shade structure</option>
            <option value="furniture-tables">Outdoor furniture</option>
            <option value="repairs-staining">Restoration / re-seal</option>
            <option value="interior-trim-millwork">Interior trim / millwork</option>
            <option value="other">Other</option>
          </select>
        </div>

        <Field label="Zip code" name="zip" inputMode="numeric" pattern="[0-9]{5}" maxLength={5} autoComplete="postal-code" placeholder="e.g. 32801" />
      </div>

      <div className="grid sm:grid-cols-2 gap-5">
        <div className="flex flex-col gap-2">
          <label htmlFor="timeline" className="text-[0.78rem] font-semibold tracking-wider uppercase text-cream-50">Timeline</label>
          <select id="timeline" name="timeline" defaultValue="" className="bg-white/5 border border-line-strong rounded-md px-4 py-3.5 text-white text-[0.95rem] focus:outline-none focus:border-coastal focus:ring-4 focus:ring-coastal/15 transition">
            <option value="">- Select -</option>
            <option value="asap">ASAP (within 30 days)</option>
            <option value="1-3mo">1-3 months</option>
            <option value="3-6mo">3-6 months</option>
            <option value="6-12mo">6-12 months</option>
            <option value="planning">Just planning</option>
          </select>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="budget" className="text-[0.78rem] font-semibold tracking-wider uppercase text-cream-50">Budget range</label>
          <select id="budget" name="budget" defaultValue="" className="bg-white/5 border border-line-strong rounded-md px-4 py-3.5 text-white text-[0.95rem] focus:outline-none focus:border-coastal focus:ring-4 focus:ring-coastal/15 transition">
            <option value="">- Select -</option>
            <option value="under-10k">Under $10k</option>
            <option value="10-25k">$10k - $25k</option>
            <option value="25-50k">$25k - $50k</option>
            <option value="50-100k">$50k - $100k</option>
            <option value="100k+">$100k+</option>
            <option value="not-sure">Not sure yet</option>
          </select>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="message" className="text-[0.78rem] font-semibold tracking-wider uppercase text-cream-50">Tell us about the project</label>
        <textarea
          id="message"
          name="message"
          rows={5}
          required
          defaultValue={serviceHint ? `I'm interested in: ${serviceHint}.\n\n` : ""}
          placeholder="Describe the build, the space, anything we should know..."
          className="bg-white/5 border border-line-strong rounded-md px-4 py-3.5 text-white text-[0.95rem] font-sans resize-y min-h-[130px] focus:outline-none focus:border-coastal focus:ring-4 focus:ring-coastal/15 transition"
        />
      </div>

      {/* honeypot */}
      <input type="text" name="_honey" tabIndex={-1} autoComplete="off" className="hidden" />

      {state === "error" && (
        <p className="text-[#ff7a59] text-[0.85rem]">Send failed: {errMsg}. You can also call (407) 561-1453.</p>
      )}

      <button type="submit" className="btn btn-primary btn-large w-full" disabled={state === "submitting"}>
        {state === "submitting" ? "Sending..." : "Send Inquiry"}
      </button>
      <p className="text-cream-30 text-[0.8rem]">We never sell or share your information.</p>
    </motion.form>
  );
}

function Field({ label, name, type = "text", required, autoComplete, placeholder, inputMode, pattern, maxLength }: {
  label: string; name: string; type?: string; required?: boolean; autoComplete?: string; placeholder?: string;
  inputMode?: "text" | "numeric" | "decimal" | "tel" | "search" | "email" | "url" | "none"; pattern?: string; maxLength?: number;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={name} className="text-[0.78rem] font-semibold tracking-wider uppercase text-cream-50">{label}</label>
      <input
        id={name}
        name={name}
        type={type}
        required={required}
        autoComplete={autoComplete}
        placeholder={placeholder}
        inputMode={inputMode}
        pattern={pattern}
        maxLength={maxLength}
        className="bg-white/5 border border-line-strong rounded-md px-4 py-3.5 text-white text-[0.95rem] focus:outline-none focus:border-coastal focus:ring-4 focus:ring-coastal/15 transition"
      />
    </div>
  );
}
