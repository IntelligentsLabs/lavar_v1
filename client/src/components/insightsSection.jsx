import React from 'react';
import { FaQuestionCircle, FaDownload } from 'react-icons/fa';

const insightsData = [
  {
    category: 'Topic',
    items: [
      {
        title: 'Challenges',
        description: 'Ac placerat vestibulum lectus eros.',
        image: 'https://i.imgur.com/5b9dI9n.jpg',
      },
      {
        title: 'Motivations',
        description: 'Ac placerat vestibulum lectus eros.',
        image: 'https://i.imgur.com/AfFp7pu.jpg',
      },
    ],
  },
  {
    category: 'Ideas',
    items: [
      {
        title: 'Wake Up',
        description: 'Ac placerat vestibulum lectus mauris ultrices eros.',
        image: 'https://i.imgur.com/10JMbZ2.jpg',
      },
      {
        title: 'Mid Day Check In',
        description: 'Ac placerat vestibulum lectus mauris ultrices eros.',
        image: 'https://i.imgur.com/8Km9tLL.jpg',
      },
      {
        title: 'Evening Wrap Up',
        description: 'Ac placerat vestibulum lectus mauris ultrices eros.',
        image: 'https://i.imgur.com/jzkMm4B.jpg',
      },
    ],
  },
];

const InsightsSection = () => {
  return (
    <div className="w-full p-6 flex flex-col items-center">
      <div className="w-full max-w-3xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Your Insights</h2>
          <FaQuestionCircle className="text-xl text-gray-500" />
        </div>

        {insightsData.map((section, index) => (
          <div key={index} className="mb-8">
            <h3 className="font-semibold text-lg mb-4">{section.category}</h3>
            <div className="space-y-6">
              {section.items.map((item, itemIndex) => (
                <div key={itemIndex} className="flex items-start gap-4">
                  <img
                    src={item.image}
                    alt={item.title}
                    className="rounded-full w-16 h-16 object-cover"
                  />
                  <div>
                    <h4 className="font-semibold text-base">{item.title}</h4>
                    <p className="text-gray-500 text-sm">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        <div className="flex flex-col lg:flex-row gap-4 mt-8">
          <button className="px-6 py-3 bg-blue-500 text-white rounded flex justify-center items-center gap-2">
            <FaDownload /> Export My Report
          </button>
          <button className="px-6 py-3 bg-blue-500 text-white rounded">
            End Session
          </button>
        </div>
      </div>
    </div>
  );
};

export default InsightsSection;
