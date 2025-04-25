import { Button } from '@nextui-org/react';
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaArrowRight, FaPlus, FaTimes } from 'react-icons/fa';

const books = [
  { id: 1, title: 'Book Title', author: 'Author Name', description: 'Description Ipsum ac placerat vestibulum lectus eros Description Ipsum ac placerat vestibulum lectus eros.', year: '2014' },
  { id: 2, title: 'Book Title', author: 'Author Name', description: 'Description Ipsum ac placerat vestibulum lectus eros Description Ipsum ac placerat vestibulum lectus eros.', year: '2014' },
  // Add more books as needed
];

const BookDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const book = books.find((book) => book.id === parseInt(id));

  if (!book) {
    return <p>Book not found</p>;
  }

  return (
    <div className="flex flex-col items-center p-4">
      <header className="flex justify-between items-center w-full mb-4">
        <Button auto light onClick={() => navigate(-1)}>
          <FaArrowLeft className="mr-2" />back
        </Button>
        <button onClick={() => navigate('/')}>
          <FaTimes className="text-2xl" />
        </button>
      </header>
      <div className="flex items-center justify-center w-full">
        <FaArrowLeft className="text-gray-500 cursor-pointer" />
        <div className="flex items-center p-4 border rounded-lg shadow-md w-3/4">
          <div className="w-1/3 h-64 bg-gray-300 mr-4"></div>
          <div className="w-2/3">
            <h1 className="text-2xl font-semibold mb-2">{book.title}</h1>
            <h2 className="text-lg font-medium text-gray-700">{book.author}</h2>
            <p className="text-gray-600 mb-4">{book.description}</p>
            <p className="text-gray-600">{book.year}</p>
            <hr className="my-4" />
            <Button auto light>
              <FaPlus className="mr-2" /> Add Book
            </Button>
            <Button auto light color="error" className="ml-4">
              Cancel
            </Button>
          </div>
        </div>
        <FaArrowRight className="text-gray-500 cursor-pointer" />
      </div>
    </div>
  );
};

export default BookDetails;
