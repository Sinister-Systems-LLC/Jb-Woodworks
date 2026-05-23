// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: { default: "Legal", template: "%s - JB Woodworks Legal" }
};

export default function LegalSectionLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
