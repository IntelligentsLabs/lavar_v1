import React from "react";
import { Link } from "react-router-dom";

const Sidebar = ({ isPremium }) => {
  return (
    <aside className="w-full bg-white text-gray-900 p-6 shadow-lg h-full">
      <nav className="flex flex-col space-y-4">
        <Link
          to="/dashboard"
          className="hover:bg-blue-100 p-2 rounded flex items-center space-x-2 transition-all duration-300"
        >
          <span className="material-icons-outlined text-blue-500">dashboard</span>
          <span>Dashboard</span>
        </Link>
        <Link
          to="/interview"
          className="hover:bg-blue-100 p-2 rounded flex items-center space-x-2 transition-all duration-300"
        >
          <span className="material-icons-outlined text-blue-500">mic</span>
          <span>Interview</span>
        </Link>

        <Link
          to="/library"
          className="hover:bg-blue-100 p-2 rounded flex items-center space-x-2 transition-all duration-300"
        >
          <span className="material-icons-outlined text-blue-500">book</span>
          <span>Library</span>
        </Link>
        {isPremium && (
          <>
            <Link
              to="/assessment"
              className="hover:bg-blue-100 p-2 rounded flex items-center space-x-2 transition-all duration-300"
            >
              <span className="material-icons-outlined text-blue-500">assessment</span>
              <span>Assessment</span>
            </Link>
            <Link
              to="/insight"
              className="hover:bg-blue-100 p-2 rounded flex items-center space-x-2 transition-all duration-300"
            >
              <span className="material-icons-outlined text-blue-500">insights</span>
              <span>Insight</span>
            </Link>
          </>
        )}
        <Link
          to="/profile"
          className="hover:bg-blue-100 p-2 rounded flex items-center space-x-2 transition-all duration-300"
        >
          <span className="material-icons-outlined text-blue-500">person</span>
          <span>Profile</span>
        </Link>
        <Link
          to="/settings"
          className="hover:bg-blue-100 p-2 rounded flex items-center space-x-2 transition-all duration-300"
        >
          <span className="material-icons-outlined text-blue-500">settings</span>
          <span>Settings</span>
        </Link>
      </nav>
    </aside>
  );
};

export default Sidebar;
