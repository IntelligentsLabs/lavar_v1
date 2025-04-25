import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const LibraryPage = () => {
  const [stacks, setStacks] = useState([
    { title: 'Stack 1', image: 'https://i.imgur.com/EZdSNjvb.jpg' },
    { title: 'Stack 2', image: 'https://i.imgur.com/BwtS9oDb.jpg' },
    { title: 'Stack 3', image: 'https://i.imgur.com/TtR3NOOb.jpg' },
  ]);

  const navigate = useNavigate();

  const addNewStack = () => {
    const newStackTitle = `Stack ${stacks.length + 1}`;
    setStacks([...stacks, { title: newStackTitle, image: 'https://i.imgur.com/FvZVblNb.jpg' }]);
  };

  const handleLaunchClick = (title) => {
    navigate(`/stackdetails`);
  };

  return (
    <main className="flex flex-col items-start h-full bg-gray-100">
      <header className="w-full p-6">
        <h1 className="text-3xl font-semibold text-left">My Book Stacks</h1>
      </header>
      <div className="flex flex-wrap mr-auto justify-start gap-5 p-6">
        {stacks.map((stack, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="w-60 h-80 bg-white cursor-pointer shadow-lg rounded-lg flex flex-col justify-end items-center overflow-hidden relative"
          >
            <img src={stack.image} alt={stack.title} className="absolute inset-0 w-full h-full object-cover" />
            <div className="relative z-10 p-4 bg-opacity-80 w-full flex flex-col justify-center items-center">
              <h2 className="text-xl font-semibold text-white">{stack.title}</h2>
              <button
                className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                onClick={() => handleLaunchClick(stack.title)}
              >
                Launch
              </button>
            </div>
          </motion.div>
        ))}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-60 h-80 bg-white shadow-lg rounded-lg flex flex-col justify-center items-center cursor-pointer"
          onClick={() => {
            addNewStack();
            navigate('/createstack');
          }}
        >
          <svg
            className="w-16 h-16 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 4v16m8-8H4"
            ></path>
          </svg>
          <h2 className="text-xl font-semibold mt-2">Create Stack</h2>
        </motion.div>
      </div>
    </main>
  );
};

export default LibraryPage;
