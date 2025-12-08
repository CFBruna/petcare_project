export interface DailyMetric {
    date: string;
    total_revenue: number;
    total_appointments: number;
    new_customers: number;
}

export interface AppointmentStatusDistribution {
    status: string;
    count: number;
}

export interface TopProduct {
    product_id: number;
    product_name: string;
    category_name: string | null;
    units_sold: number;
    revenue_generated: number;
}

export interface DashboardData {
    period_start: string;
    period_end: string;
    metrics_history: DailyMetric[];
    status_distribution: AppointmentStatusDistribution[];
    top_products: TopProduct[];
}

export interface ApiError {
    error: string;
    detail?: string;
}
