const features = [
  {
    title: "Sync Latest Workouts",
    desc: "Fetch the latest activities from Garmin with full metrics and split data.",
  },
  {
    title: "Classify & Analyze",
    desc: "Identify interval sessions and analyze heart rate profiles using AI vision.",
  },
  {
    title: "Collaborate & Iterate",
    desc: "Review insights, discuss training implications, and refine analysis together.",
  },
];

export default function KeyFeatures({
  selected,
  onSelect,
}: {
  selected: number | null;
  onSelect: (i: number | null) => void;
}) {
  return (
    <section className="mt-auto pt-6">
      <h2 className="text-lg font-medium text-gray-400">Key Features</h2>
      <div className="flex divide-x divide-gray-800">
        {features.map((feat, i) => (
          <button
            key={i}
            onClick={() => onSelect(selected === i ? null : i)}
            className="flex-1 text-left group px-5 py-3 first:pl-0 last:pr-0"
          >
            <h3
              className={`text-base font-semibold transition-colors ${
                selected === i
                  ? "text-blue-400"
                  : "text-white group-hover:text-blue-400"
              }`}
            >
              {feat.title}
            </h3>
            <p className="text-base text-gray-500 mt-1">{feat.desc}</p>
          </button>
        ))}
      </div>
    </section>
  );
}
