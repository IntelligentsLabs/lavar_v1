import { useAuth0 } from "@auth0/auth0-react";
import { useEffect } from "react";

const Authorize = () => {
  const { user, logout } = useAuth0();

  useEffect(() => {
    const Auth = async () => {
      try {
        const response = await fetch(
          "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/custom_llm/token",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
            },
            credentials: "include",
            body: JSON.stringify({
              username: user?.given_name,
              picture: user?.picture,
              email: user?.email,
            }),
          },
        );
        const data = await response.json();
        if (data.success) {
          sessionStorage.setItem("access_token", data.access_token);
          window.location.href = "/dashboard";
        }
      } catch (error) {
        console.error("Auth error:", error);
        // Uncomment if you want to logout on error
        // logout({logoutParams: {returnTo: window.location.origin}});
      }
    };

    if (user) {
      Auth();
    }
  }, [user, logout]);

  return <div>Loading....</div>;
};

export default Authorize;
