import { useState } from "react";
import WorkflowPage from "./components/WorkflowView";
import FlowDiagram from "./components/FlowDiagram";
import KeyFeatures from "./components/KeyFeatures";
import "./index.css";

function App() {
  const [selectedFeature, setSelectedFeature] = useState(null);

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      <main className="max-w-6xl mx-auto px-6 py-10 flex-1 flex flex-col">
        {selectedFeature !== null ? (
          <WorkflowPage onBack={() => setSelectedFeature(null)} />
        ) : (
          <section className="flex-1 flex flex-col items-center justify-center">
            <div className="flex flex-col items-center">
              <h1
                className="text-7xl font-extrabold text-white mb-5 tracking-tight"
                style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
              >
                <span className="block text-sm font-medium text-gray-500 tracking-widest uppercase mb-1 text-left pl-1">
                  powered by
                </span>
                MCP{" "}
                <span className="text-3xl font-semibold text-gray-500 align-middle">
                  x
                </span>{" "}
                ZeroClaw
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
