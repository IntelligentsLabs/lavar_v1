
export const Bell = () => {
  return (
    <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-12 w-12 text-gray-700"
    viewBox="0 0 20 20"
    fill="currentColor"
  >
    <path
      fillRule="evenodd"
      d="M11.293 5.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 10-1.414-1.414L13 7.586V2a1 1 0 10-2 0v5.586L8.707 5.293a1 1 0 00-1.414 1.414l3 3z"
      clipRule="evenodd"
    />
    <path
      fillRule="evenodd"
      d="M17 14a1 1 0 011 1v1a1 1 0 01-1 1H4a1 1 0 01-1-1v-1a1 1 0 011-1h1V9a3 3 0 016 0v5h1zm-4 2a1 1 0 11-2 0 1 1 0 012 0z"
      clipRule="evenodd"
    />
  </svg>
  )
}


export const Dots = () => {
  return (
<svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-12 w-12 text-gray-700"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 12a2 2 0 100-4 2 2 0 000 4z"
                    clipRule="evenodd"
                  />
                  <path
                    fillRule="evenodd"
                    d="M10 20a2 2 0 100-4 2 2 0 000 4z"
                    clipRule="evenodd"
                  />
                  <path
                    fillRule="evenodd"
                    d="M5 16a2 2 0 100-4 2 2 0 000 4z"
                    clipRule="evenodd"
                  />
                  <path
                    fillRule="evenodd"
                    d="M15 16a2 2 0 100-4 2 2 0 000 4z"
                    clipRule="evenodd"
                  />
                  <path
                    fillRule="evenodd"
                    d="M5 6a2 2 0 100-4 2 2 0 000 4z"
                    clipRule="evenodd"
                  />
                  <path
                    fillRule="evenodd"
                    d="M15 6a2 2 0 100-4 2 2 0 000 4z"
                    clipRule="evenodd"
                  />
                </svg>
  )
}



export const HamburgerMenuIcon = ({ className, onPress}) => (
  <svg
    className= {className}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
    onClick={onPress}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      d="M4 6h16M4 12h16m-7 6h7"
    />
  </svg>
);

