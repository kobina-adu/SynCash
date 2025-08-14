import { Session } from "./auth-client";
import { cookies } from "next/headers";

/**
 * This function retrieves the server session for the user.
 * It uses the cookies from the request headers to fetch the session.
 * 
 * @returns {Promise<Session | null>} The server session or null if not found.
 */


export const getServerSession = async () : Promise<typeof Session | null> => {
   try {
    const cookieHeader = (await cookies()).toString();
    const res = await fetch(`http://localhost:8080/api/auth/get-session`, {
        credentials: "include",
        headers: {
            Cookie: cookieHeader
        }
    });

    return res.json();

   } catch (error) {
    console.error(error);
    return null;
   }
}

export default getServerSession;