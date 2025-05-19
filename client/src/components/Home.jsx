import React from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4">Welcome to Our Website</h1>
      <p className="mb-4">This is the home page.</p>

      <div className="mt-8">
        <Link to="/terms" className="text-blue-500">Terms and Conditions</Link> | 
        <Link to="/policy" className="text-blue-500 ml-2">Privacy Policy</Link>
      </div>
    </div>
  );
};

export default Home;