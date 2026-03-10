import express from 'express';

export * from './types/index.js'
export * from './billing/index.js'
export * from './memory/index.js'
export * from './orchestration/index.js'
export * from './models/index.js'
export * from './provisioning/index.js'
export * from './platform.js'

const app = express();
const PORT = process.env.PORT ?? 4000;

app.use(express.json());

app.get('/', (_req, res) => {
  res.json({ name: 'Agentopia', version: '2.0', status: 'ok' });
});

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Agentopia running on http://localhost:${PORT}`);
});
