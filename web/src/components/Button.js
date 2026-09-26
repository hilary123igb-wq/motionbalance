import Link from "next/link";

export function ButtonPrimary({ href, children }) {
  return (
    <Link href={href} className="inline-flex items-center gap-2 bg-indigo-500 text-white rounded-full px-5 py-2.5 text-sm font-medium hover:bg-indigo-600 transition-colors">
      {children}
    </Link>
  );
}

export function ButtonSecondary({ href, children }) {
  return (
    <Link href={href} className="inline-flex items-center gap-2 border border-gray-200 text-gray-700 rounded-full px-5 py-2.5 text-sm font-medium hover:border-indigo-300 hover:text-indigo-600 transition-colors">
      {children}
    </Link>
  );
}