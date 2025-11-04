// K6 Load Testing Script for CPG2PVG-AI
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter, Trend } from 'k6/metrics';

// Custom metrics
export let errorRate = new Rate('errors');
export let requestCounter = new Counter('requests');
export let responseTime = new Trend('response_time');

// Test configuration
export let options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests should be below 2s
    http_req_failed: ['rate<0.1'],      // Error rate should be below 10%
    errors: ['rate<0.1'],
  },
};

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';

// Test data
const testFile = open('test-data/sample.cpg', 'b');

export default function() {
  // Health check
  let healthResponse = http.get(`${BASE_URL}/health`, {
    tags: { endpoint: 'health' }
  });

  let healthSuccess = check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!healthSuccess);
  requestCounter.add(1);
  responseTime.add(healthResponse.timings.duration);

  sleep(1);

  // API authentication
  let loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    username: 'testuser',
    password: 'testpass'
  }), {
    headers: { 'Content-Type': 'application/json' },
    tags: { endpoint: 'login' }
  });

  let loginSuccess = check(loginResponse, {
    'login status is 200': (r) => r.status === 200,
    'login returns token': (r) => JSON.parse(r.body).access_token !== undefined,
  });

  if (loginSuccess) {
    let token = JSON.parse(loginResponse.body).access_token;
    let authHeaders = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    // Test file upload
    let uploadResponse = http.post(`${BASE_URL}/api/v1/files/upload`, testFile, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/octet-stream'
      },
      tags: { endpoint: 'upload' }
    });

    let uploadSuccess = check(uploadResponse, {
      'upload status is 200': (r) => r.status === 200,
      'upload returns file ID': (r) => JSON.parse(r.body).file_id !== undefined,
    });

    errorRate.add(!uploadSuccess);
    requestCounter.add(1);
    responseTime.add(uploadResponse.timings.duration);

    if (uploadSuccess) {
      let fileId = JSON.parse(uploadResponse.body).file_id;

      sleep(2);

      // Test file processing
      let processResponse = http.post(`${BASE_URL}/api/v1/cpv/process`, JSON.stringify({
        file_id: fileId,
        options: {
          output_format: 'pvg',
          quality: 'high'
        }
      }), {
        headers: authHeaders,
        tags: { endpoint: 'process' }
      });

      let processSuccess = check(processResponse, {
        'process status is 200': (r) => r.status === 200,
        'process returns task ID': (r) => JSON.parse(r.body).task_id !== undefined,
      });

      errorRate.add(!processSuccess);
      requestCounter.add(1);
      responseTime.add(processResponse.timings.duration);

      sleep(1);

      // Test task status check
      if (processSuccess) {
        let taskId = JSON.parse(processResponse.body).task_id;
        let statusResponse = http.get(`${BASE_URL}/api/v1/tasks/${taskId}/status`, {
          headers: authHeaders,
          tags: { endpoint: 'status' }
        });

        let statusSuccess = check(statusResponse, {
          'status check successful': (r) => r.status === 200,
          'status returns valid data': (r) => JSON.parse(r.body).status !== undefined,
        });

        errorRate.add(!statusSuccess);
        requestCounter.add(1);
        responseTime.add(statusResponse.timings.duration);

        sleep(1);
      }
    }

    // Test user profile
    let profileResponse = http.get(`${BASE_URL}/api/v1/users/profile`, {
      headers: authHeaders,
      tags: { endpoint: 'profile' }
    });

    let profileSuccess = check(profileResponse, {
      'profile status is 200': (r) => r.status === 200,
      'profile returns user data': (r) => JSON.parse(r.body).username !== undefined,
    });

    errorRate.add(!profileSuccess);
    requestCounter.add(1);
    responseTime.add(profileResponse.timings.duration);

    sleep(1);

    // Test file list
    let filesResponse = http.get(`${BASE_URL}/api/v1/files/`, {
      headers: authHeaders,
      tags: { endpoint: 'files' }
    });

    let filesSuccess = check(filesResponse, {
      'files list status is 200': (r) => r.status === 200,
      'files list is array': (r) => Array.isArray(JSON.parse(r.body)),
    });

    errorRate.add(!filesSuccess);
    requestCounter.add(1);
    responseTime.add(filesResponse.timings.duration);
  }

  sleep(1);
}

export function handleSummary(data) {
  return {
    'summary.json': JSON.stringify(data, null, 2),
    'load-test-results.html': htmlReport(data),
  };
}

function htmlReport(data) {
  return `
<!DOCTYPE html>
<html>
<head>
    <title>CPG2PVG-AI Load Test Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
        .pass { background-color: #d4edda; }
        .fail { background-color: #f8d7da; }
        .warn { background-color: #fff3cd; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>CPG2PVG-AI Load Test Results</h1>
    <p><strong>Test Date:</strong> ${new Date().toISOString()}</p>

    <h2>Summary Metrics</h2>
    <div class="metric ${data.metrics.http_req_duration.values.avg < 1000 ? 'pass' : 'warn'}">
        <strong>Average Response Time:</strong> ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms
    </div>

    <div class="metric ${data.metrics.http_req_duration.values.p95 < 2000 ? 'pass' : 'fail'}">
        <strong>95th Percentile Response Time:</strong> ${data.metrics.http_req_duration.values.p95.toFixed(2)}ms
    </div>

    <div class="metric ${data.metrics.http_req_failed.rate < 0.1 ? 'pass' : 'fail'}">
        <strong>Error Rate:</strong> ${(data.metrics.http_req_failed.rate * 100).toFixed(2)}%
    </div>

    <div class="metric">
        <strong>Total Requests:</strong> ${data.metrics.http_reqs.count}
    </div>

    <div class="metric">
        <strong>Request Rate:</strong> ${data.metrics.http_reqs.rate.toFixed(2)} req/s
    </div>

    <h2>Endpoint Performance</h2>
    <table>
        <tr>
            <th>Endpoint</th>
            <th>Count</th>
            <th>Avg Response Time</th>
            <th>95th Percentile</th>
            <th>Error Rate</th>
        </tr>
        ${Object.entries(data.metrics.http_req_duration.values.counts).map(([tag, count]) => `
            <tr>
                <td>${tag || 'all'}</td>
                <td>${count}</td>
                <td>${data.metrics.http_req_duration.values.avg.toFixed(2)}ms</td>
                <td>${data.metrics.http_req_duration.values.p95.toFixed(2)}ms</td>
                <td>${(data.metrics.http_req_failed.rate * 100).toFixed(2)}%</td>
            </tr>
        `).join('')}
    </table>

    <h2>Thresholds Status</h2>
    ${Object.entries(data.thresholds).map(([name, threshold]) => `
        <div class="metric ${threshold.ok ? 'pass' : 'fail'}">
            <strong>${name}:</strong> ${threshold.ok ? 'PASS' : 'FAIL'}
            ${threshold.ok ? '' : ` - ${threshold.reason}`}
        </div>
    `).join('')}
</body>
</html>
  `;
}