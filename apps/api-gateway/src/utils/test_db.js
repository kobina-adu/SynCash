import { Client } from "pg";

const client = new Client({
  host: "localhost",
  port: 5432,
  user: "synccash",
  password: "synccash",
  database: "synccash"
});

async function checkDB() {
  try {
    await client.connect();
    console.log("✅ Database is up!");
  } catch (err) {
    console.error("❌ Database not reachable:", err.message);
  } finally {
    await client.end();
  }
}

checkDB();
