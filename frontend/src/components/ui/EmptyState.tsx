import React from 'react';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({ icon: Icon, title, description, actionLabel, onAction }) => (
  <div className="flex flex-col items-center justify-center py-16 px-4">
    <div className="flex items-center justify-center h-16 w-16 rounded-full bg-indigo-50 mb-5">
      <Icon className="h-8 w-8 text-indigo-500" />
    </div>
    <h3 className="text-xl font-semibold text-gray-900 mb-2 text-center">{title}</h3>
    {description && (
      <p className="text-sm text-gray-500 mb-6 text-center max-w-md leading-relaxed">{description}</p>
    )}
    {actionLabel && onAction && (
      <button
        onClick={onAction}
        className="inline-flex items-center px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium"
      >
        {actionLabel}
      </button>
    )}
  </div>
);

export default EmptyState;
