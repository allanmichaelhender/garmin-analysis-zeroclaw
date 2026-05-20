import {
  Server,
  Bot,
  Cloud,
  Brain,
  ArrowLeftRight,
  ArrowUpDown,
  MessageSquare,
  Database,
  Route,
  Search,
} from "lucide-react";
import ArchCard from "./ArchCard";

export default function FlowDiagram() {
  return (
    <div className="flex flex-col items-center w-full">
      {/* Top row: MCP ↔ ZeroClaw */}
      <div className="flex items-center gap-10">
        <ArchCard
          icon={Server}
          label="MCP + FastAPI"
          sub="Backend Server"
          color="green"
          large
        />
        <ArrowLeftRight className="w-6 h-6 text-gray-400/70" />
        <ArchCard
          icon={Bot}
          label="ZeroClaw"
          sub="AI Agent"
          color="cyan"
          large
        />
      </div>

      {/* Two-column branching below */}
      <div className="flex gap-16 mt-1">
        {/* Left branch */}
        <div className="flex flex-col items-center">
          <div className="flex flex-col items-center py-1">
            <div className="w-0.5 h-4 bg-gradient-to-b from-green-500/60 to-green-500/20" />
            <ArrowUpDown className="w-4 h-4 text-gray-400/70" />
            <div className="w-0.5 h-4 bg-gradient-to-b from-green-500/20 to-green-500/60" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <ArchCard
              small
              icon={Cloud}
              label="garminconnect"
              sub="Activity Data"
              color="orange"
            />
            <ArchCard
              small
              icon={Database}
              label="Database"
              sub="Local Storage"
              color="blue"
            />
            <ArchCard
              small
              icon={Brain}
              label="AI Visual"
              sub="Sonnet 4.6"
              color="purple"
            />
            <ArchCard
              small
              icon={Route}
              label="Strava API"
              sub="Third-party"
              color="orange"
            />
          </div>
        </div>

        {/* Right branch */}
        <div className="flex flex-col items-center">
          <div className="flex flex-col items-center py-1">
            <div className="w-0.5 h-4 bg-gradient-to-b from-cyan-500/60 to-cyan-500/20" />
            <ArrowUpDown className="w-4 h-4 text-gray-400/70" />
            <div className="w-0.5 h-4 bg-gradient-to-b from-cyan-500/20 to-cyan-500/60" />
          </div>
          <div className="flex gap-3">
            <ArchCard
              small
              icon={MessageSquare}
              label="Discord"
              sub="Chat Interface"
              color="indigo"
            />
            <ArchCard
              small
              icon={Search}
              label="Web Search"
              sub="Real-time Information"
              color="blue"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
