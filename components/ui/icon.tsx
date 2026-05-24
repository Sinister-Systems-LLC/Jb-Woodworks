// Author: RKOJ-ELENO :: 2026-05-23
// Sprite-backed SVG icon. References /img/icons.svg <symbol>s.
import { cn } from "@/lib/utils";

export type IconName =
  | "dock" | "deck" | "table" | "trim" | "pergola" | "wrench"
  | "arrow-right" | "phone" | "mail" | "pin" | "menu"
  | "instagram" | "facebook" | "tiktok" | "twitter"
  | "anvil" | "ruler" | "leaf" | "compass";

type Props = {
  name: IconName;
  size?: number;
  className?: string;
  "aria-hidden"?: boolean;
  "aria-label"?: string;
};

export function Icon({ name, size = 20, className, "aria-hidden": ariaHidden = true, "aria-label": ariaLabel }: Props) {
  return (
    <svg
      width={size}
      height={size}
      aria-hidden={ariaHidden}
      aria-label={ariaLabel}
      role={ariaLabel ? "img" : undefined}
      className={cn("inline-block align-middle", className)}
    >
      <use href={`/img/icons.svg#i-${name}`} />
    </svg>
  );
}
