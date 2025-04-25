import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

const StackBooksPage = () => {
  const { title } = useParams();
  const navigate = useNavigate();

  // Dummy books data, replace with actual data or fetch from an API
  const books = [
    {
      title: 'Book 1',
      image: 'https://images.unsplash.com/photo-1532012197267-da84d127e765?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwzNjUyOXwwfDF8c2VhcmNofDIwfHxib29rfGVufDB8fHx8MTY2MzA3MjU2OA&ixlib=rb-1.2.1&q=80&w=400',
    },
    {
      title: 'Book 2',
      image: 'https://images.unsplash.com/photo-1544717305-996b815c338c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwzNjUyOXwwfDF8c2VhcmNofDE3fHxib29rfGVufDB8fHx8MTY2MzA3MjU2OA&ixlib=rb-1.2.1&q=80&w=400',
    },
    {
      title: 'Book 3',
      image: 'https://i.imgur.com/sYdSJ3ob.jpg',
    },
  ];

  return (
    <main className="flex flex-col items-start h-full bg-gray-100">
      <header className="w-full p-6">
        <h1 className="text-3xl font-semibold text-left">Books in {title}</h1>
        <button
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
          onClick={() => navigate(-1)}
        >
          Go Back
        </button>
      </header>
      <div className="flex flex-wrap justify-start items-start gap-4 p-6">
        {books.map((book, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="w-60 h-80 bg-white cursor-pointer shadow-lg rounded-lg flex flex-col justify-end items-center overflow-hidden relative"
          >
            <img src={book.image} alt={book.title} className="absolute inset-0 w-full h-full object-cover" />
            <div className="relative z-10 p-4 bg-white w-full flex flex-col justify-center items-center">
              <h2 className="text-xl font-semibold">{book.title}</h2>
              <button
                className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                onClick={() => navigate(`/non-premium`)}
              >
                View
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </main>
  );
};

export default StackBooksPage;
