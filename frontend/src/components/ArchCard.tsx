const borderMap: Record<string, string> = {
  indigo: "border-indigo-500/30 bg-indigo-500/5 text-indigo-400",
  cyan: "border-cyan-500/30 bg-cyan-500/5 text-cyan-400",
  green: "border-green-500/30 bg-green-500/5 text-green-400",
  orange: "border-orange-500/30 bg-orange-500/5 text-orange-400",
  purple: "border-purple-500/30 bg-purple-500/5 text-purple-400",
  blue: "border-blue-500/30 bg-blue-500/5 text-blue-400",
};

const bgMap: Record<string, string> = {
  indigo: "bg-indigo-500/10",
  cyan: "bg-cyan-500/10",
  green: "bg-green-500/10",
  orange: "bg-orange-500/10",
  purple: "bg-purple-500/10",
  blue: "bg-blue-500/10",
};

export default function ArchCard({
  icon: Icon,
  label,
  sub,
  color,
  large,
  small,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  sub: string;
  color: string;
  large?: boolean;
  small?: boolean;
}) {
  return (
    <div
      className={`flex items-center border ${borderMap[color]} ${
        large
          ? "gap-4 px-7 py-4 rounded-xl scale-110"
          : small
            ? "gap-1.5 px-2 py-1.5 rounded-md"
            : "gap-3 px-4 py-3 rounded-lg"
      }`}
    >
      <div
        className={`${
          large ? "w-[52px] h-[52px]" : small ? "w-6 h-6" : "w-10 h-10"
        } rounded-lg ${bgMap[color]} flex items-center justify-center`}
      >
        <Icon
          className={`${large ? "w-6 h-6" : small ? "w-3 h-3" : "w-5 h-5"}`}
        />
      </div>
      <div>
        <p
          className={`${large ? "text-base" : small ? "text-[10px]" : "text-sm"} font-semibold text-white`}
        >
          {label}
        </p>
        <p
          className={`${large ? "text-sm" : small ? "text-[8px]" : "text-xs"} text-gray-400`}
        >
          {sub}
        </p>
      </div>
    </div>
  );
}
