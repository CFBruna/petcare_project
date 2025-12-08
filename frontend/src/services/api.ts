import axios, { AxiosInstance } from 'axios';
import type { DashboardData } from '../types/dashboard';

class ApiService {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: '/api/v1',
            timeout: 10000,
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json',
            },
        });
    }

    async getDashboardMetrics(days: number = 7): Promise<DashboardData> {
        const response = await this.client.get<DashboardData>(
            '/analytics/dashboard/',
            {
                params: { days },
            }
        );
        return response.data;
    }
}

export const apiService = new ApiService();
