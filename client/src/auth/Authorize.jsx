// client/src/auth/Authorize.jsx

import { useAuth0 } from "@auth0/auth0-react";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom"; // Use useNavigate hook
const REACT_APP_BACKEND_URL = process.env.REACT_APP_API_BASE_URL

const Authorize = () => {
  // Destructure necessary functions and state from useAuth0
  const { user, logout, isLoading, error, getAccessTokenSilently } = useAuth0(); 
  const navigate = useNavigate(); // Initialize navigate hook

  useEffect(() => {
    const AuthAndFetchToken = async () => {
      // Log the full user object received from Auth0 for debugging
      console.log("Auth0 User Object Received:", user); 
      console.dir(user); 

      // Validate essential user information before proceeding
      // Use 'name' as a fallback if 'given_name' isn't present
      const effectiveUsername = user.given_name || user.name || user.nickname || user.email?.split('@')[0];
      if (!user?.email || !effectiveUsername) {
          console.error("Auth0 user object is missing critical info (email or name/nickname):", user);
          // Optionally display an error message to the user or log them out
          // Consider redirecting to an error page or showing a message
          // logout({logoutParams: {returnTo: window.location.origin}}); 
          return; // Stop execution if essential info is missing
      }

      try {
        console.log("Attempting to fetch backend token with extended user data...");

        // Optional: Get an Auth0 Access Token if your backend validates it
        // const auth0AccessToken = await getAccessTokenSilently(); 
        // You would then pass this in the Authorization header if needed by your backend

        const response = await fetch(
          // Ensure this URL points correctly to your backend's /token endpoint
          // Use environment variables for base URL in production
          `${REACT_APP_BACKEND_URL}/api/custom_llm/token`, // Example using env var
          // "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/custom_llm/token", // Or hardcoded URL
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
              // If your backend needs the Auth0 token for validation:
              // Authorization: `Bearer ${auth0AccessToken}`, 
            },
            // credentials: "include", // Usually NOT needed if backend allows origin via CORS without cookies
            body: JSON.stringify({
              // --- Updated Body with More Fields ---
              username: effectiveUsername, // Use the derived username
              picture: user.picture,       // Profile picture URL
              email: user.email,         // User's email address
              first_name: user.given_name, // User's first name
              last_name: user.family_name,// User's last name
              email_verified: user.email_verified, // Email verification status
              auth0_sub: user.sub          // Auth0 unique subject ID (useful for linking/debugging)
              // --- End Updated Body ---
            }),
          },
        );

        // Handle non-successful HTTP responses (e.g., 4xx, 5xx)
        if (!response.ok) {
             let errorBody = `Server responded with status ${response.status}`;
             try {
                 // Try to parse JSON error message from backend
                 const errorData = await response.json();
                 errorBody = errorData.message || errorData.error || JSON.stringify(errorData);
             } catch (_) {
                 // Fallback to text if JSON parsing fails
                 try { errorBody = await response.text(); } catch (_) {}
             }
             console.error(`Backend token request failed: ${response.status} ${response.statusText}`, errorBody);
             // Optionally logout or display a user-friendly error
             // logout({logoutParams: {returnTo: window.location.origin}});
             return; 
        }

        // Parse the successful JSON response from your backend
        const data = await response.json();
        console.log("Backend /token response:", data); 

        // Check for success flag AND the presence of the access token
        if (data.success && data.access_token) {
          sessionStorage.setItem("access_token", data.access_token); // Store YOUR backend's JWT
          console.log("Backend JWT token stored in session storage. Redirecting to dashboard...");
          navigate("/dashboard"); // Use navigate hook for redirection
        } else {
           console.error("Backend token request was ok, but response indicates failure or token missing:", data);
           // Handle cases where backend returns success: false or no token
           // Maybe show an error message?
        }
      } catch (error) {
        // Catch network errors (fetch failed, DNS issues, CORS blocks if not handled by server)
        // Also catches JSON parsing errors if response isn't valid JSON
        console.error("Error during fetch or processing backend token:", error);
        // Optionally logout or display a user-friendly error
        // logout({logoutParams: {returnTo: window.location.origin}});
      }
    };

    // --- Effect Logic ---
    // Run only when Auth0 is done loading, there's no Auth0 error, and user object is available
    if (!isLoading && !error && user) {
      AuthAndFetchToken();
    } else if (isLoading) {
      console.log("Auth0 is loading user data..."); // Log loading state
    } else if (error) {
      console.error("Error during Auth0 authentication:", error); // Log Auth0 specific errors
      // Consider logging the user out or showing a persistent error message
      // logout({logoutParams: {returnTo: window.location.origin}});
    }
     // eslint-disable-next-line react-hooks/exhaustive-deps 
  }, [user, isLoading, error, logout, navigate, getAccessTokenSilently]); // Add navigate and getAccessTokenSilently to dependency array

  // --- Render UI ---
  // Provide feedback to the user during the process
  if (isLoading) return <div>Logging in, please wait...</div>;
  if (error) return <div>Oops... Login Error: {error.message}. Please try again or contact support.</div>;
  // Generic message while waiting for the token exchange and redirect
  return <div>Authorizing and setting up session...</div>; 
};

export default Authorize;