/**
 * Pitch-type colours. Fastballs are warm, breaking balls cool, offspeed
 * green, so a pitcher's mix reads at a glance. The actual colour values
 * are tokens in `src/index.css`; this file only picks which token.
 */

const TOKEN_BY_CODE: Readonly<Record<string, string>> = {
  FF: "--color-pitch-ff",
  SI: "--color-pitch-si",
  FC: "--color-pitch-fc",
  SL: "--color-pitch-sl",
  ST: "--color-pitch-st",
  SV: "--color-pitch-sv",
  CU: "--color-pitch-cu",
  KC: "--color-pitch-kc",
  CS: "--color-pitch-cu",
  CH: "--color-pitch-ch",
  FS: "--color-pitch-fs",
  FO: "--color-pitch-fs",
};

export function pitchColor(code: string): string {
  return `var(${TOKEN_BY_CODE[code] ?? "--color-pitch-other"})`;
}
