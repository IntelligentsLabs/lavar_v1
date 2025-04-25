import React from "react";
import { useAuth0 } from "@auth0/auth0-react";
import {Link, Button} from "@nextui-org/react";

const LoginButton = () => {
  const { user, isAuthenticated, loginWithRedirect } = useAuth0();
  // const {given_name, email} = user;


  return <Button as={Link} color="primary" variant="flat" onPress={
    (e) => {
    loginWithRedirect()
    }
  }>Sign in</Button>;
};

export default LoginButton;