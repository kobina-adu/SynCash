import { betterAuth } from "better-auth"
import { twoFactor } from "better-auth/plugins"
 
export const auth = betterAuth({
    emailAndPassword: {
    	enabled: true,
    	autoSignIn: false //defaults to true
  },
    plugins: [ 
        twoFactor() 
    ] 
})