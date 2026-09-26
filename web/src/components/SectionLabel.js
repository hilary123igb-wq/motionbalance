export default function SectionLabel({ children }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="w-6 h-px bg-indigo-300" />
      <span className="text-xs font-medium tracking-widest text-gray-400 uppercase">
        {children}
      </span>
    </div>
  );
}