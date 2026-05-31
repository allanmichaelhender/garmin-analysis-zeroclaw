import {
  ArrowLeftRight,
  ArrowDown,
  Search,
  Heart,
  BarChart3,
  Layers,
} from "lucide-react";

const steps = [
  {
    icon: Search,
    title: "Discover Available Activities",
    description: "Call get_activity_summary() with no ID",
    detail:
      "Returns a lightweight list of the 10 most recent activities — just enough info (type, date, duration, avg HR) for the agent to present options or let you pick one to inspect.",
  },
  {
    icon: Heart,
    title: "Inspect a Specific Workout",
    description: "Call get_activity_summary(activity_id=...)",
    detail:
      "Pass an activity ID to get the full curated view: core stats (HR, power, cadence, training effect), user-classified metadata (intervals, structure), and any saved Anthropic HR profile analysis.",
  },
  {
    icon: BarChart3,
    title: "Review Real HR Trends",
    description: "30-second bucket averages, always included",
    detail:
      "Instead of dumping thousands of raw 1-second samples, the tool computes 30-second HR averages. The agent gets real data to describe warmup, steady-state, and cooldown phases — no hallucinated BPM values.",
  },
  {
    icon: Layers,
    title: "Browse Condensed Lap Splits",
    description: "Clean lap array from raw Garmin JSON",
    detail:
      "Raw lapDTOs are condensed into a simple array with relative start/end times, duration, avg/max HR, and distance. The agent can reference specific laps by index without wading through nested Garmin API structures.",
  },
];

export default function ActivitySummaryView({
  onBack,
}: {
  onBack: () => void;
}) {
  return (
    <div className="min-h-screen bg-gray-950 p-6">
      <div className="max-w-6xl mx-auto">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors mb-6"
        >
          <ArrowLeftRight className="w-4 h-4 rotate-180" />
          Back
        </button>

        <h1 className="text-2xl font-bold text-white mb-1">
          Find &amp; Analyse Activities
        </h1>
        <p className="text-gray-400 mb-6 text-sm">
          Browse, inspect, and review workout data with condensed summaries
        </p>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Flow Diagram */}
          <div className="flex-1 max-w-sm">
            <div className="relative">
              {steps.map((step, index) => {
                const Icon = step.icon;
                const isLast = index === steps.length - 1;
                return (
                  <div key={index} className="relative">
                    <div className="relative z-10 bg-gray-900 rounded-lg border border-gray-800 p-3 hover:border-blue-500/50 transition-colors duration-200">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
                          <Icon className="w-4 h-4 text-blue-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono text-blue-500 bg-blue-500/10 px-1.5 py-0.5 rounded">
                              Step {index + 1}
                            </span>
                            <h3 className="text-sm font-semibold text-white">
                              {step.title}
                            </h3>
                          </div>
                          {step.description && (
                            <p className="text-xs font-mono text-blue-300 mt-0.5">
                              {step.description}
                            </p>
                          )}
                          <p className="text-xs text-gray-400 mt-0.5">
                            {step.detail}
                          </p>
                        </div>
                      </div>
                    </div>
                    {!isLast && (
                      <div className="flex justify-center py-1">
                        <div className="flex flex-col items-center">
                          <div className="w-0.5 h-3 bg-gradient-to-b from-blue-500/60 to-blue-500/20" />
                          <ArrowDown className="w-3 h-3 text-blue-400/60" />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Video */}
          <div className="flex-[2]">
            <div className="sticky top-8">
              <video
                className="w-full aspect-square object-cover bg-black rounded-lg"
                autoPlay
                muted
                loop
                playsInline
              >
                <source src="/assets/activity_summary.mp4" type="video/mp4" />
              </video>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
