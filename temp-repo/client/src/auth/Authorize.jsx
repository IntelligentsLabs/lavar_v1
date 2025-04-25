import { useAuth0 } from '@auth0/auth0-react'
import { useEffect } from 'react'

const Authorize = () => {
    const {user, logout} = useAuth0();
    
    useEffect(() => {
      if (user) {
       const Auth = () => {
        fetch('https://ec2-100-29-60-61.compute-1.amazonaws.com:5001/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'

          },
          body: JSON.stringify({
            username: user?.given_name,
            picture: user?.picture,
            email: user?.email
          })
        })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            sessionStorage.setItem('access_token', data.access_token)
            window.location.href = '/dashboard'
          } 
          // else {
          //   // logout({logoutParams: {returnTo: window.location.origin}})   
          // }

        })
       }
       
         Auth()
      }
       
    },[user])
    return <div>Loading....</div>

}

export default Authorize
