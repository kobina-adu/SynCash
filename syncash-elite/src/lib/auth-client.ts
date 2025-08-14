import dotenv from "dotenv";
import { createAuthClient } from "better-auth/react";

dotenv.config();

export const authClient = createAuthClient({
    baseURL: process.env.NEXT_PUBLIC_APP_URL!,
    fetchOptions: {
        credentials: "include"
    }
});

export const {
    signIn,
    signOut,
    signUp,
    useSession
} = authClient;

export const Session = authClient.$Infer.Session;



