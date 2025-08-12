import { Pool } from 'pg';
import { drizzle } from 'drizzle-orm/node-postgres';

const pool = new Pool({
  connectionString: process.env.PG_DB_URL || 'postgres://synccash:synccash@localhost:5432/synccash',
});

export const db = drizzle(pool);
