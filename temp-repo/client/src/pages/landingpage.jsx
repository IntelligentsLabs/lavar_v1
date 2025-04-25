import React from "react";
import { Button } from "@nextui-org/react";
import { Link } from "react-router-dom";
import { Bell, Dots } from "../components/icons/icons";
import { useAuth0 } from "@auth0/auth0-react";
import { motion } from "framer-motion";
import NavBar from "../components/Navbar";
import PricingPage from "../components/pricing";

const LandingPage = () => {
  const { loginWithRedirect } = useAuth0();

  const fadeInUp = {
    initial: { opacity: 0, y: 50 },
    animate: { opacity: 1, y: 0 },
  };

  return (
    <>
    <NavBar />
      <header className="flex flex-col items-center justify-center h-screen text-center px-6 bg-white">
        <div className="max-w-2xl">
          <motion.h1
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-6xl font-bold mb-6"
          >
            Merge, Learn and Converse
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-xl mb-8"
          >
            AI-Powered Conversations for In-Depth Learning
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <Button
              onClick={loginWithRedirect}
              auto
              shadow
              color="primary"
              className="py-4 px-8 text-xl font-semibold"
            >
              Get Started
            </Button>
          </motion.div>
        </div>
      </header>

      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-6">
          <motion.h2
            initial={fadeInUp.initial}
            animate={fadeInUp.animate}
            transition={{ duration: 0.8 }}
            className="text-4xl font-semibold text-center mb-12"
          >
            Features
          </motion.h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <motion.div
              initial={fadeInUp.initial}
              animate={fadeInUp.animate}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="text-center"
            >
              <div className="rounded-full bg-gray-200 h-24 w-24 flex items-center justify-center mx-auto mb-6">
                <Bell />
              </div>
              <h3 className="text-2xl font-semibold mb-4">
                Interactive Interviews
              </h3>
              <p className="text-lg">
                Let our AI interview you based on the books you read, making
                your reading experience more immersive.
              </p>
            </motion.div>
            <motion.div
              initial={fadeInUp.initial}
              animate={fadeInUp.animate}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="text-center"
            >
              <div className="rounded-full bg-gray-200 h-24 w-24 flex items-center justify-center mx-auto mb-6">
                <Dots />
              </div>
              <h3 className="text-2xl font-semibold mb-4">
                Personalized Planning
              </h3>
              <p className="text-lg">
                Use insights from your readings to plan and organize your life
                more effectively.
              </p>
            </motion.div>
            <motion.div
              initial={fadeInUp.initial}
              animate={fadeInUp.animate}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="text-center"
            >
              <div className="rounded-full bg-gray-200 h-24 w-24 flex items-center justify-center mx-auto mb-6">
                <Dots />
              </div>
              <h3 className="text-2xl font-semibold mb-4">
                AI-Powered Insights
              </h3>
              <p className="text-lg">
                Leverage advanced AI to gain deeper insights and enhance your
                learning experience.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      <section className="py-20 text-center">
        <div className="max-w-6xl mx-auto px-6">
          <motion.h2
            initial={fadeInUp.initial}
            animate={fadeInUp.animate}
            transition={{ duration: 0.8 }}
            className="text-4xl font-semibold mb-6"
          >
            Ready to Transform Your Reading Experience?
          </motion.h2>
          <motion.p
            initial={fadeInUp.initial}
            animate={fadeInUp.animate}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-xl mb-8"
          >
            Join us and start your journey towards a more organized and
            insightful life.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <Button
              onClick={loginWithRedirect}
              auto
              shadow
              color="primary"
              className="py-4 px-8 text-xl font-semibold"
            >
              Get Started
            </Button>
          </motion.div>
        </div>
      </section>
        <PricingPage />

      <footer className="bg-gray-100 text-gray-700 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between">
          <div className="mb-4 md:mb-0">
            <h1 className="text-2xl font-semibold">Colloquial</h1>
            <p className="mt-2">Enhancing your reading journey with AI.</p>
          </div>
          <nav className="flex space-x-4">
            <Link to="/" className="hover:text-gray-900">
              Home
            </Link>
            <Link to="/about" className="hover:text-gray-900">
              About
            </Link>
            <Link to="/contact" className="hover:text-gray-900">
              Contact
            </Link>
            <Link to="/privacy" className="hover:text-gray-900">
              Privacy Policy
            </Link>
          </nav>
        </div>
        <div className="mt-4 text-center">
          <p>&copy; 2024 Colloquial. All rights reserved.</p>
        </div>
      </footer>
    </>
  );
};

export default LandingPage;
