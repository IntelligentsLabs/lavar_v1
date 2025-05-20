// debugEnv.ts

// Safely check if VITE_GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set
const clientId = process.env.VITE_GOOGLE_CLIENT_ID;
const clientSecret = process.env.GOOGLE_CLIENT_SECRET;

console.log("VITE_GOOGLE_CLIENT_ID:", clientId);
console.log("GOOGLE_CLIENT_SECRET:", clientSecret);
