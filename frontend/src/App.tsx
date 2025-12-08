import { useState, useEffect } from 'react';
import { MetricsCard } from './components/MetricsCard';
import { RevenueChart } from './components/RevenueChart';
import { TopProductsTable } from './components/TopProductsTable';
import { apiService } from './services/api';
import type { DashboardData } from './types/dashboard';

function App() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [days, setDays] = useState(7);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const result = await apiService.getDashboardMetrics(days);
                setData(result);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load data');
                console.error('Error fetching dashboard data:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [days]);

    const getTotalRevenue = (): number => {
        if (!data) return 0;
        return data.metrics_history.reduce((sum, item) => sum + item.total_revenue, 0);
    };

    const getTotalAppointments = (): number => {
        if (!data) return 0;
        return data.metrics_history.reduce((sum, item) => sum + item.total_appointments, 0);
    };

    const getTotalCustomers = (): number => {
        if (!data) return 0;
        return data.metrics_history.reduce((sum, item) => sum + item.new_customers, 0);
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
        }).format(value);
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <h1 className="text-3xl font-bold text-gray-900">
                        Dashboard de Análise PetCare
                    </h1>
                    <p className="mt-1 text-sm text-gray-600">
                        Métricas de desempenho e insights de negócio
                    </p>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="mb-6 flex justify-between items-center">
                    <div>
                        {data && (
                            <p className="text-sm text-gray-600">
                                Período: {new Date(data.period_start).toLocaleDateString('pt-BR')} -{' '}
                                {new Date(data.period_end).toLocaleDateString('pt-BR')}
                            </p>
                        )}
                    </div>
                    <div className="flex gap-2">
                        {[7, 30, 90].map((d) => (
                            <button
                                key={d}
                                onClick={() => setDays(d)}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${days === d
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                                    }`}
                            >
                                {d} dias
                            </button>
                        ))}
                    </div>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
                        <p className="font-semibold">Erro ao carregar dashboard</p>
                        <p className="text-sm">{error}</p>
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <MetricsCard
                        title="Receita Total"
                        value={formatCurrency(getTotalRevenue())}
                        subtitle={`Últimos ${days} dias`}
                        loading={loading}
                    />
                    <MetricsCard
                        title="Total de Agendamentos"
                        value={getTotalAppointments()}
                        subtitle={`Últimos ${days} dias`}
                        loading={loading}
                    />
                    <MetricsCard
                        title="Novos Clientes"
                        value={getTotalCustomers()}
                        subtitle={`Últimos ${days} dias`}
                        loading={loading}
                    />
                </div>

                <div className="mb-8">
                    <RevenueChart data={data?.metrics_history || []} loading={loading} />
                </div>

                <div>
                    <div>
                        <TopProductsTable products={data?.top_products || []} loading={loading} />
                    </div>        </div>
            </main>

            <footer className="bg-white mt-12 border-t border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <p className="text-center text-sm text-gray-500">
                        Dashboard de Análise PetCare - TypeScript + React + Django REST API
                    </p>
                </div>
            </footer>
        </div>
    );
}

export default App;
