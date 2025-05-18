
import React from 'react';

export function Button({ children, onClick }) {
  return (
    <button onClick={onClick} className="btn bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
      {children}
    </button>
  );
}
