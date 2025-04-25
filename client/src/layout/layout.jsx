import React, { useState } from "react";
import Sidebar from "../components/sidebar";
import NavBar from "../components/Navbar";
import { motion } from "framer-motion";
import { Divider } from "@nextui-org/react";
import { HamburgerMenuIcon } from "../components/icons/icons";

const Layout = ({ children, isPremium, setIsPremium }) => {
  const [showSidebar, setShowSidebar] = useState(true);

  // Clone the children and pass setIsPremium to them
  const childrenWithProps = React.Children.map(children, (child) => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child, { setIsPremium, isPremium });
    }
    return child;
  });

  return (
    <div className="h-full flex flex-col bg-white text-gray-900">
      <NavBar />
      <div className="flex flex-1">

        <HamburgerMenuIcon className="w-6 h-6 absolute z-50" onPress={() => setShowSidebar((prev) => !prev)} />
        {showSidebar && <motion.div
          initial={{ x: '-100%' }}
          animate={{ x: showSidebar ? 0 : '-100%' }}
          transition={{ duration: 0.3 }}
          className={` inset-y-0 left-0 z-20 sm:w-1/2 lg:w-1/4 md:w-1/4 shadow-lg`}
          >
          <Sidebar isPremium={isPremium} />
        </motion.div>}


        {showSidebar && (
          <div
            className="fixed inset-0 z-10 bg-black opacity-50"
            onClick={() => setShowSidebar(false)}
            />
          )}


        <motion.main
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="bg-background text-foreground mr-auto ml-auto absolute w-full"
          onMouseEnter={() =>
            setTimeout(() => {
              setShowSidebar(false);
            }, 15000)
          }
        >
          {childrenWithProps}
        </motion.main>
      </div>
    </div>
  );
};

export default Layout;
