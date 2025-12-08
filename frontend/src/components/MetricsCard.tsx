import React from 'react';

interface MetricsCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    loading?: boolean;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({
    title,
    value,
    subtitle,
    loading = false,
}) => {
    if (loading) {
        return (
            <div className="bg-white p-6 rounded-lg shadow-sm animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </div>
        );
    }

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>
            <p className="text-3xl font-bold text-gray-900">{value}</p>
            {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
        </div>
    );
};
