import React from 'react';

export function Button({
  children,
  onClick,
  variant = '',
  size = '',
  className = '',
  ...rest
}) {
  return (
    <button
      onClick={onClick}
      className={`
        btn ${variant} ${size} ${className}
        bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded
      `}
      {...rest}
    >
      {children}
    </button>
  );
}
