// import { betterAuth } from "better-auth";
// import { drizzleAdapter } from "better-auth/adapters/drizzle";
// import { emailOTP } from "better-auth/plugins/email-otp";
// import nodemailer from "nodemailer";
// import dotenv from "dotenv";

// import { db } from "./db.js";
// import { users } from "./schema.js";

// dotenv.configDotenv()

// const transporter = nodemailer.createTransport({
//   service: "gmail",
//   auth: {
//     user: process.env.GMAIL_USER!, 
//     pass: process.env.GMAIL_APP_PASSWORD!, 
//   },
// });

// export const auth = betterAuth({
//   database: drizzleAdapter(db, {
//     provider: "pg", 
//   }), 
//   emailAndPassword: {
//     enabled: true,
//     autoSignIn: false
//   },
//     plugins: [
//     emailOTP({
//       async sendVerificationOTP({ email, otp, type }) {
//         let subject = '', text = '';

//         if (type === "sign-in") {
//           subject = "Your Sign-In OTP";
//           text = `Your sign-in OTP is: ${otp}`;
//         } else if (type === "email-verification") {
//           subject = "Verify Your Email";
//           text = `Your email verification OTP is: ${otp}`;
//         } else {
//           subject = "Reset Your Password";
//           text = `Your password reset OTP is: ${otp}`;
//         }

//         await transporter.sendMail({
//           from: `"Syncash" <${process.env.GMAIL_USER}>`,
//           to: email,
//           subject,
//           text,
//         });

//         console.log(`OTP sent to ${email}: ${otp} (${type})`);
//       },
//     }),
//   ],
// });

import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "../db/index.js";
import { schema } from "../db/schema.js"
import { sendVerificationEmail } from "better-auth/api";
import { sendEmail } from "./send-email.js"; 
 
export const auth = betterAuth({
    database: drizzleAdapter(db, {
        provider: "pg",
        schema: schema,
    }),
    emailAndPassword: {
        enabled: true,
        requireEmailVerification: true
    },
    trustedOrigins: ["http://localhost:3000", "http://localhost:8080", "*"], // once again for testing purposes would just decide to leave it as that for now
    emailVerification: {
        autoSignInAfterVerification: true,
        sendVerificationEmail: async ({ user, token, url}, request) => {
            await sendEmail({
                to: user.email,
                subject: "Verify your email address",
                text: `Click the link to verify the link: ${url}`,
            });
        },
    }
});