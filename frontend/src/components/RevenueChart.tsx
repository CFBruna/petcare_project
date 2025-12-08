import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts';
import type { DailyMetric } from '../types/dashboard';

interface RevenueChartProps {
    data: DailyMetric[];
    loading?: boolean;
}

export const RevenueChart: React.FC<RevenueChartProps> = ({ data, loading = false }) => {
    if (loading) {
        return (
            <div className="bg-white p-6 rounded-lg shadow-sm h-96 flex items-center justify-center">
                <div className="animate-pulse text-gray-400">Carregando gráfico...</div>
            </div>
        );
    }

    const formattedData = data.map((item) => ({
        ...item,
        date: new Date(item.date).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
        }),
    }));

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Tendência de Receita e Agendamentos
            </h3>
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={formattedData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="total_revenue"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        name="Receita (R$)"
                    />
                    <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="total_appointments"
                        stroke="#10b981"
                        strokeWidth={2}
                        name="Agendamentos"
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
