import React from 'react';
import { FaCheck } from 'react-icons/fa';

const PricingPage = () => {
  const features = [
    'Combine knowledge from various books and documents to create a comprehensive AI expert on any topic you choose.',
    'Combine knowledge from various books and documents to create a comprehensive AI expert on any topic you choose.',
    'Combine knowledge from various books and documents to create a comprehensive AI expert on any topic you choose.',
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-6">
      <h1 className="text-4xl font-bold mb-8">Pricing</h1>
      <div className="flex space-x-8">
        {[...Array(2)].map((_, index) => (
          <div key={index} className="bg-white rounded-lg shadow-lg overflow-hidden w-80">
            <div className="bg-blue-500 p-6 text-center text-white">
              <h2 className="text-2xl font-semibold">Free</h2>
            </div>
            <div className="p-6">
              {features.map((feature, i) => (
                <div key={i} className="flex items-start mb-4">
                  <FaCheck className="text-blue-500 mt-1 mr-2" />
                  <p className="text-gray-700">{feature}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PricingPage;
