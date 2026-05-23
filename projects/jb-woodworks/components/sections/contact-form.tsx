// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { useState, useEffect, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";

type State = "idle" | "submitting" | "success" | "error";

export function ContactForm() {
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
      className="bg-ink-3 border border-line p-9 rounded-xl flex flex-col gap-5"
      noValidate
    >
      <Field label="Name" name="name" required autoComplete="name" />
      <Field label="Email address" name="email" type="email" required autoComplete="email" />
      <Field label="Phone number" name="phone" type="tel" autoComplete="tel" />
      <div className="flex flex-col gap-2">
        <label htmlFor="service" className="text-[0.78rem] font-semibold tracking-wider uppercase text-cream-50">Project type</label>
        <select id="service" name="service" defaultValue={serviceHint ? params.get("service") || "" : ""} className="bg-white/5 border border-line-strong rounded-md px-4 py-3.5 text-white text-[0.95rem] focus:outline-none focus:border-gold focus:ring-4 focus:ring-gold/10 transition">
          <option value="">- Select -</option>
          <option value="docks">Docks</option>
          <option value="custom-decks">Custom Decks</option>
          <option value="furniture-tables">Furniture and Tables</option>
          <option value="interior-trim-millwork">Interior Trim and Millwork</option>
          <option value="outdoor-living">Outdoor Living Spaces</option>
          <option value="repairs-staining">Repairs and Staining</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div className="flex flex-col gap-2">
        <label htmlFor="message" className="text-[0.78rem] font-semibold tracking-wider uppercase text-cream-50">What are you looking to get done?</label>
        <textarea
          id="message"
          name="message"
          rows={5}
          required
          defaultValue={serviceHint ? `I'm interested in: ${serviceHint}.\n\n` : ""}
          placeholder="Describe your project, timeline, etc."
          className="bg-white/5 border border-line-strong rounded-md px-4 py-3.5 text-white text-[0.95rem] font-sans resize-y min-h-[130px] focus:outline-none focus:border-gold focus:ring-4 focus:ring-gold/10 transition"
        />
      </div>
      {/* honeypot */}
      <input type="text" name="_honey" tabIndex={-1} autoComplete="off" className="hidden" />

      {state === "error" && (
        <p className="text-[#ff7a59] text-[0.85rem]">Send failed: {errMsg}. You can also call {`(407) 561-1453`}.</p>
      )}

      <button type="submit" className="btn btn-primary btn-large w-full" disabled={state === "submitting"}>
        {state === "submitting" ? "Sending..." : "Send Inquiry"}
      </button>
      <p className="text-cream-30 text-[0.8rem]">We never sell or share your information.</p>
    </motion.form>
  );
}

function Field({ label, name, type = "text", required, autoComplete }: { label: string; name: string; type?: string; required?: boolean; autoComplete?: string }) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={name} className="text-[0.78rem] font-semibold tracking-wider uppercase text-cream-50">{label}</label>
      <input
        id={name}
        name={name}
        type={type}
        required={required}
        autoComplete={autoComplete}
        className="bg-white/5 border border-line-strong rounded-md px-4 py-3.5 text-white text-[0.95rem] focus:outline-none focus:border-gold focus:ring-4 focus:ring-gold/10 transition"
      />
    </div>
  );
}
