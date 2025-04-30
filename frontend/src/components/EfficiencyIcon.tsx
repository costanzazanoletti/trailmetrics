import {
  ArrowDown,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  ArrowUp,
  SquareArrowDown,
  SquareArrowDownRight,
  SquareArrowRight,
  SquareArrowUpRight,
  SquareArrowUp,
} from 'lucide-react';

interface EfficiencyIconProps {
  zone: string;
  type: 'efficiency' | 'grade';
}

const colorClass: Record<string, string> = {
  very_low: 'text-red-500',
  low: 'text-orange-500',
  medium: 'text-yellow-500',
  high: 'text-green-500',
  very_high: 'text-emerald-600',
};

export function EfficiencyIcon({ zone, type }: EfficiencyIconProps) {
  const Icon = (() => {
    switch (zone) {
      case 'very_low':
        return type === 'efficiency' ? SquareArrowDown : ArrowDown;
      case 'low':
        return type === 'efficiency' ? SquareArrowDownRight : ArrowDownRight;
      case 'medium':
        return type === 'efficiency' ? SquareArrowRight : ArrowRight;
      case 'high':
        return type === 'efficiency' ? SquareArrowUpRight : ArrowUpRight;
      case 'very_high':
        return type === 'efficiency' ? SquareArrowUp : ArrowUp;
      default:
        return null;
    }
  })();

  if (!Icon) return null;

  return <Icon size={16} className={colorClass[zone]} />;
}
