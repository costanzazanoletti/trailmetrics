import {
  SquareArrowDown,
  SquareArrowDownRight,
  SquareArrowRight,
  SquareArrowUpRight,
  SquareArrowUp,
  ArrowDown,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  ArrowUp,
} from 'lucide-react';

export function EfficiencyLegend() {
  return (
    <div className="bg-gray-50 p-4 rounded-md border text-xs mb-4">
      <div className="flex flex-wrap gap-6">
        {/* Efficiency Zones */}
        <div className="flex-1 min-w-[250px]">
          <h3 className="text-sm font-semibold mb-2">Efficiency Zones</h3>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-1">
              <SquareArrowDown className="w-4 h-4 text-red-500" />
              <span>Very Low</span>
            </div>
            <div className="flex items-center gap-1">
              <SquareArrowDownRight className="w-4 h-4 text-orange-500" />
              <span>Low</span>
            </div>
            <div className="flex items-center gap-1">
              <SquareArrowRight className="w-4 h-4 text-yellow-500" />
              <span>Medium</span>
            </div>
            <div className="flex items-center gap-1">
              <SquareArrowUpRight className="w-4 h-4 text-green-500" />
              <span>High</span>
            </div>
            <div className="flex items-center gap-1">
              <SquareArrowUp className="w-4 h-4 text-emerald-600" />
              <span>Very High</span>
            </div>
          </div>
        </div>

        {/* Grade Efficiency Zones */}
        <div className="flex-1 min-w-[250px]">
          <h3 className="text-sm font-semibold mb-2">Grade Efficiency Zones</h3>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-1">
              <ArrowDown className="w-4 h-4 text-red-500" />
              <span>Very Low</span>
            </div>
            <div className="flex items-center gap-1">
              <ArrowDownRight className="w-4 h-4 text-orange-500" />
              <span>Low</span>
            </div>
            <div className="flex items-center gap-1">
              <ArrowRight className="w-4 h-4 text-yellow-500" />
              <span>Medium</span>
            </div>
            <div className="flex items-center gap-1">
              <ArrowUpRight className="w-4 h-4 text-green-500" />
              <span>High</span>
            </div>
            <div className="flex items-center gap-1">
              <ArrowUp className="w-4 h-4 text-emerald-500" />
              <span>Very High</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
