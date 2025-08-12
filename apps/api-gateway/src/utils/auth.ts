import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { twoFactor } from "better-auth/plugins";
import { db } from "./db.js";
import { users } from "./schema.js";

export const auth = betterAuth({
  database: drizzleAdapter(db, {
    provider: "pg", 
  }), 
  emailAndPassword: {
    enabled: true,
    autoSignIn: false
  },
  plugins: [
    twoFactor()
  ]
});
