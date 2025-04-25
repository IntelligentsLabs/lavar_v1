import React from 'react';
import { Button } from '@nextui-org/react';
import { useNavigate } from 'react-router-dom';

const PremiumPage = ({setIsPremium, isPremium}) => {
  const navigate = useNavigate();

  const handleSubscribeClick = () => {
    // Handle subscription logic here
    setIsPremium(true)
    alert("Subscription functionality coming soon!");
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 p-6">
      <div className="max-w-2xl bg-white p-8 rounded-xl shadow-lg text-center">
        <h1 className="text-3xl font-bold mb-4">Upgrade to Premium</h1>
        <p className="text-gray-700 mb-8">
          As a premium user, you will get access to exclusive features and
          content that will enhance your experience. Enjoy ad-free browsing,
          premium support, and much more!
        </p>
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-2">Premium Features:</h2>
          <ul className="list-disc list-inside text-left">
            <li className="text-gray-700 mb-1">Ad-free browsing</li>
            <li className="text-gray-700 mb-1">Exclusive premium content</li>
            <li className="text-gray-700 mb-1">Priority customer support</li>
            <li className="text-gray-700 mb-1">Early access to new features</li>
            <li className="text-gray-700 mb-1">And much more!</li>
          </ul>
        </div>
        <Button
          auto
          onClick={handleSubscribeClick}
          className="px-6 py-3 bg-blue-500 text-white rounded-full text-lg hover:bg-blue-600 transition"
        >
          Subscribe Now
        </Button>
        <Button
          auto
          onClick={() => navigate('/library')}
          className="mt-4 text-primary-500 border-primary-500 rounded-3xl text-lg border-2 w-36 align-center"
        >
          Go Back
        </Button>
      </div>
    </div>
  );
};

export default PremiumPage;
