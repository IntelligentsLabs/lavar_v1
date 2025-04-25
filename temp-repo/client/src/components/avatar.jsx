
import {DropdownItem, DropdownTrigger, Dropdown, DropdownMenu, Avatar} from "@nextui-org/react";
import { useAuth0 } from "@auth0/auth0-react";
import { Link } from "react-router-dom";


const AvatarLogo = ({user}) => {
  const {logout} = useAuth0()

  return (
    <div>
      <Dropdown placement="bottom-end">
          <DropdownTrigger>
            <Avatar
              isBordered
              as="button"
              className="transition-transform"
              color="primary"
              name={user?.username.slice(0,1)}
              size="sm"
              src=""
            />
          </DropdownTrigger>
          <DropdownMenu aria-label="Profile Actions" variant="flat">
            <DropdownItem key="profile" className="h-14 gap-2">
              <Link to='/profile'>
              <p className="font-semibold">Signed in as</p>
              <p className="font-semibold">{user?.email}</p>
              </Link>
            </DropdownItem>
            <DropdownItem key="assessment"><Link to='/assessment'>Assessment</Link></DropdownItem>
            <DropdownItem key="settings"><Link to='/settings'>Settings</Link></DropdownItem>
            <DropdownItem key="help_and_feedback"><Link to='/faq'>Help & Feedback</Link></DropdownItem>
            <DropdownItem key="logout" color="danger" onPress = {() => {
              sessionStorage.clear()
              logout({logoutParams: {returnTo: window.location.origin}})}
              }>
              Log Out
          </DropdownItem>
          </DropdownMenu>
        </Dropdown>
    </div>
  )
}

export default AvatarLogo;


