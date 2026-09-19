
import { healthCheck } from './src/mcp-server/db.js';

async function test() {
  const isHealthy = await healthCheck();
  console.log('Is Healthy:', isHealthy);
}

test();
