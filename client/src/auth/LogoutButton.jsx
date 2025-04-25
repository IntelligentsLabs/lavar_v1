import React from "react";
import { useAuth0 } from "@auth0/auth0-react";
import {Link, Button, DropdownItem} from "@nextui-org/react";

const LogoutButton = () => {
  const { logout } = useAuth0();

  return (
        // <Button as={Link} color="primary" variant="flat" onPress={(e) => logout({ logoutParams: { returnTo: window.location.origin } })}>
        //     Log out
        // </Button>
          <DropdownItem key="logout" color="danger" onPress = {(e) => {
            localStorage.clear()
            sessionStorage.clear()
            logout({logoutParams: {returnTo: window.location.origin}})

            }}>
              Log Out
          </DropdownItem>
  );
};

export default LogoutButton;