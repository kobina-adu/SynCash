import dotenv from "dotenv"
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API!);

export const sendEmail = async ({
    to,
    subject,
    text
} : {
    to: string;
    subject: string;
    text: string;
}) => {
    
    const {data, error } = await resend.emails.send({
        from: "<users-no-reply@syncash.com>",
        to,
        subject,
        text,
    });

    if ( error ) {
        console.error(error);
        throw new Error("Failed to send email");
    }
}

