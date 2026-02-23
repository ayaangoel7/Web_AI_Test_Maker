import { TestData, TestResults } from '@/types/test';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8090';

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE;
  }

  async checkHealth(): Promise<{ status: string; models_loaded: boolean }> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) throw new Error('Server unreachable');
    return res.json();
  }

  async checkModels(): Promise<{ exists: boolean; loaded: boolean }> {
    const res = await fetch(`${this.baseUrl}/models/status`);
    if (!res.ok) throw new Error('Failed to check models');
    return res.json();
  }

  async downloadModels(onProgress?: (progress: number, status: string) => void): Promise<void> {
    const res = await fetch(`${this.baseUrl}/models/download`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to start download');

    const reader = res.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value);
      const lines = text.split('\n').filter(Boolean);
      for (const line of lines) {
        try {
          const data = JSON.parse(line);
          onProgress?.(data.progress, data.status);
        } catch { /* skip */ }
      }
    }
  }

  async uploadFile(file: File): Promise<{ file_id: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${this.baseUrl}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to upload file');
    return res.json();
  }

  async generateTest(
    fileId: string,
    marks: number,
    distribution: Record<string, number> | object
  ): Promise<TestData> {
    const res = await fetch(`${this.baseUrl}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: fileId, marks, distribution }),
    });
    if (!res.ok) throw new Error('Failed to generate test');
    return res.json();
  }

  async gradeTest(
    testData: TestData,
    answers: Record<number, string>
  ): Promise<TestResults> {
    const res = await fetch(`${this.baseUrl}/grade`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test_data: testData, answers }),
    });
    if (!res.ok) throw new Error('Failed to grade test');
    return res.json();
  }
}

export const apiService = new ApiService();
