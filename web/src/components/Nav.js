import Link from "next/link";
import { playfair } from "@/lib/fonts";

const LINKS = [
  { href: "/motions", label: "Motions" },
  { href: "/tournaments", label: "Tournaments" },
  { href: "/analytics", label: "Analytics" },
];

export default function Nav({ current }) {
  return (
    <header className="border-b border-gray-100">
      <div className="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
        <Link href="/" className={`${playfair.className} text-lg font-semibold tracking-tight`}>
          <span className="text-gray-900">Motion</span>
          <span className="text-indigo-500">Balance</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={current === l.href.slice(1) ? "text-indigo-500 font-medium" : "text-gray-500 hover:text-gray-900"}
            >
              {l.label}
            </Link>
          ))}
          <Link href="/motions" aria-label="Search motions" className="text-gray-400 hover:text-indigo-500">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <circle cx="11" cy="11" r="7" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </Link>
        </nav>
      </div>
    </header>
  );
}