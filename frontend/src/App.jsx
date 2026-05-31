import { useState } from "react";
import WorkflowPage from "./components/WorkflowView";
import ActivitySummaryView from "./components/ActivitySummaryView";
import FlowDiagram from "./components/FlowDiagram";
import KeyFeatures from "./components/KeyFeatures";
import "./index.css";

function App() {
  const [selectedFeature, setSelectedFeature] = useState(null);

  const featurePages = [
    WorkflowPage, // 0: Sync Latest Workouts
    ActivitySummaryView, // 1: Find & Analyse
    WorkflowPage, // 2: Collaborate & Iterate
  ];

  const PageComponent =
    selectedFeature !== null ? featurePages[selectedFeature] : null;

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      <main className="max-w-6xl mx-auto px-6 py-10 flex-1 flex flex-col">
        {selectedFeature !== null ? (
          <PageComponent onBack={() => setSelectedFeature(null)} />
        ) : (
          <section className="flex-1 flex flex-col items-center justify-center">
            <div className="flex flex-col items-center">
              <h1
                className="text-7xl font-extrabold text-white mb-5 tracking-tight"
                style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
              >
                <span className="block text-8xl font-extrabold text-white mb-2 tracking-tight">
                  Analysing Allan
                </span>
              </h1>
            </div>
            <FlowDiagram />
          </section>
        )}

        <KeyFeatures selected={selectedFeature} onSelect={setSelectedFeature} />
      </main>
    </div>
  );
}

export default App;
