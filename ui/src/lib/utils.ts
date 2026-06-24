// cn: merge conditional class names with Tailwind conflict resolution.
// Role: tiny utility used by every component. In: clsx values. Out: a class string.
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
