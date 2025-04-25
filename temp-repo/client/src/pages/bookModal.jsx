import React, { useState } from 'react';
import { FaEllipsisH } from 'react-icons/fa';

const BookModal = ({ isOpen, onClose, onSelectBook, books }) => {
  const [selectedBook, setSelectedBook] = useState(null);

  if (!isOpen) return null;

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-white p-6 rounded shadow-lg w-11/12 max-w-4xl">
        <header className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Available Books</h2>
          <button onClick={onClose} className="text-xl font-semibold">&times;</button>
        </header>
        <div className="flex justify-center mb-4">
          <input
            type="text"
            placeholder="Search by name, Author, or topic"
            className="w-2/3 p-2 border border-gray-300 rounded"
          />
        </div>
        
        {selectedBook && (
          <div className="flex items-center mb-4 border-t border-b border-gray-300 py-4">
            <div className="w-32 h-48 bg-gray-200 flex-shrink-0"></div>
            <div className="ml-6">
              <h3 className="text-xl font-semibold">{selectedBook.title}</h3>
              <p className="text-gray-700">{selectedBook.author}</p>
              <p className="text-sm text-gray-500 mt-2">{selectedBook.description}</p>
              <p className="text-sm text-gray-500 mt-1">{selectedBook.year}</p>
              <button
                className="mt-4 px-4 py-2 bg-teal-500 text-white rounded hover:bg-teal-600"
                onClick={() => onSelectBook(selectedBook)}
              >
                Add Book
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-4 gap-4 mb-4">
          {books.map((book) => (
            <div
              key={book.id}
              className={`border rounded h-48 p-4 flex flex-col justify-between cursor-pointer ${
                selectedBook?.id === book.id ? 'border-blue-600' : 'border-dashed border-gray-300'
              }`}
              onClick={() => setSelectedBook(book)}
            >
              <div className="h-32 bg-gray-200 mb-2"></div>
              <div>
                <h3 className="text-sm font-semibold">{book.title}</h3>
                <p className="text-xs text-gray-500">{book.author}</p>
              </div>
              <FaEllipsisH className="self-end text-gray-400" />
            </div>
          ))}
        </div>
        <div className="flex justify-center">
          <button
            type="button"
            className="px-4 py-2 border border-blue-500 rounded bg-blue-500 text-white hover:bg-blue-600"
          >
            Load More
          </button>
        </div>
      </div>
    </div>
  );
};

export default BookModal;
