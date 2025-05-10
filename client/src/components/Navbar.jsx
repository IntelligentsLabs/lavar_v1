import { useAuth0 } from "@auth0/auth0-react";
import { Button } from "@nextui-org/react";
import { useEffect, useState } from "react";
import AvatarLogo from "./avatar";

const NavBar = () => {
  const token =
    sessionStorage.getItem("access_token") !== null
      ? sessionStorage.getItem("access_token")
      : "";
  const isAuthenticated = token.length > 10 ? true : false;
  console.log(token);
  useEffect(() => {
    const getUser = async () => {
      const res = await fetch(
        "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/custom_llm/user",
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        },
      );
      const data = await res.json();
      if (data.success) {
        setUser(data.user);
      }
    };
    if (isAuthenticated) getUser();
  }, [isAuthenticated,token]);

  const [user, setUser] = useState({ username: "", picture: "", email: "" });
  const { loginWithRedirect } = useAuth0();
  return (
    <nav className="py-4 px-6 flex justify-between items-center border-b border-gray-200 bg-white w-full">
      <div>
        <h1 className="text-3xl font-semibold">Colloquial</h1>
      </div>
      <div>
        {!isAuthenticated ? (
          <>
            <Button
              light
              auto
              className="text-gray-700 hover:text-gray-900 mr-4"
              onClick={loginWithRedirect}
            >
              Login
            </Button>
            <Button auto flat color="primary" onClick={loginWithRedirect}>
              Sign Up
            </Button>
          </>
        ) : (
          <AvatarLogo user={user} />
        )}
      </div>
    </nav>
  );
};

export default NavBar;
