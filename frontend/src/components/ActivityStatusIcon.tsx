import { CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { ActivityStatus } from '../types/activity';

interface ActivityStatusIconProps {
  status: ActivityStatus | null;
}

export function ActivityStatusIcon({ status }: ActivityStatusIconProps) {
  if (status === ActivityStatus.SIMILARITY_READY) {
    return (
      <span title="Ready">
        <CheckCircle className="text-green-500 inline" />
      </span>
    );
  }
  if (status === ActivityStatus.NOT_PROCESSABLE) {
    return (
      <span title="Not Processable">
        <AlertCircle className="text-red-500 inline" />
      </span>
    );
  }
  return (
    <span title="Processing">
      <Clock className="text-yellow-500 inline" />
    </span>
  );
}
