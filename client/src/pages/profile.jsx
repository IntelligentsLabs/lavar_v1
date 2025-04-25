import React, { useState } from "react";
import Avatar from "react-avatar";
import { Button } from "@nextui-org/react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

const ProfilePage = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState({
    name: "Oluwatobi",
    title: "Student",
    email: "olola73@morgan.edu",
    phone: "(123) 456-7890",
    address: "Morgan State University, Baltimore, MD",
    bio: "Tobi is a student at Morgan State University studying Computer Science.",
    interests: "Fiction, Science, Technology, History",
    books: [
      { title: "The Alchemist", author: "Paulo Coelho" },
      { title: "The Lean Startup", author: "Eric Ries" },
      { title: "The Da Vinci Code", author: "Dan Brown" },
      { title: "1984", author: "George Orwell" },
      { title: "Brave New World", author: "Aldous Huxley" },
    ],
    password: "********",
    subscription: "Premium",
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setProfile((prevProfile) => ({
      ...prevProfile,
      [name]: value,
    }));
  };

  const handleSave = () => {
    setIsEditing(false);
  };

  const handleDeleteAccount = () => {
    alert("Deleting account...");
  };

  return (
    <div className="min-h-screen flex flex-col items-center bg-gradient-to-br from-gray-100 to-gray-200 p-4">
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-white rounded-xl shadow-lg p-6 w-full max-w-3xl"
      >
        <div className="flex items-center space-x-6">
          <motion.div whileHover={{ scale: 1.1 }} transition={{ duration: 0.3 }}>
            <Avatar name={profile.name} size="100" round={true} color="hsl(212.01999999999998 100% 46.67% / 1)" />
          </motion.div>
          <div>
            {isEditing ? (
              <input
                type="text"
                name="name"
                value={profile.name}
                onChange={handleInputChange}
                className="text-3xl font-semibold border-b border-gray-300 focus:outline-none"
              />
            ) : (
              <h1 className="text-3xl font-semibold">{profile.name}</h1>
            )}
            {isEditing ? (
              <input
                type="text"
                name="title"
                value={profile.title}
                onChange={handleInputChange}
                className="text-gray-600 border-b border-gray-300 focus:outline-none"
              />
            ) : (
              <p className="text-gray-600">{profile.title}</p>
            )}
          </div>
        </div>
        <div className="mt-6">
          <h2 className="text-2xl font-semibold mb-4">Profile Information</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-xl font-medium">Contact Information</h3>
              {isEditing ? (
                <>
                  <input
                    type="email"
                    name="email"
                    value={profile.email}
                    className="w-full border-b border-gray-300 focus:outline-none"
                    disabled
                  />
                  <input
                    type="text"
                    name="phone"
                    value={profile.phone}
                    onChange={handleInputChange}
                    className="w-full border-b border-gray-300 focus:outline-none"
                  />
                </>
              ) : (
                <>
                  <p>Email: {profile.email}</p>
                  <p>Phone: {profile.phone}</p>
                </>
              )}
            </div>
            <div>
              <h3 className="text-xl font-medium">Address</h3>
              {isEditing ? (
                <textarea
                  name="address"
                  value={profile.address}
                  onChange={handleInputChange}
                  className="w-full border-b border-gray-300 focus:outline-none"
                />
              ) : (
                <p>{profile.address}</p>
              )}
            </div>
            <div>
              <h3 className="text-xl font-medium">Bio</h3>
              {isEditing ? (
                <textarea
                  name="bio"
                  value={profile.bio}
                  onChange={handleInputChange}
                  className="w-full border-b border-gray-300 focus:outline-none"
                />
              ) : (
                <p>{profile.bio}</p>
              )}
            </div>
            <div>
              <h3 className="text-xl font-medium">Interests</h3>
              {isEditing ? (
                <input
                  type="text"
                  name="interests"
                  value={profile.interests}
                  onChange={handleInputChange}
                  className="w-full border-b border-gray-300 focus:outline-none"
                />
              ) : (
                <p>{profile.interests}</p>
              )}
            </div>
            <div>
              <h3 className="text-xl font-medium">Books</h3>
              <div className="max-h-40 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
                <ul className="space-y-2 pr-2">
                  {profile.books.map((book, index) => (
                    <li
                      key={index}
                      className="bg-gray-100 p-2 rounded-lg shadow-sm"
                    >
                      <p className="font-semibold">{book.title}</p>
                      <p className="text-gray-600">{book.author}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

          </div>
        </div>
        <div className="mt-6">
          <h2 className="text-2xl font-semibold mb-4">Password and Security</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-xl font-medium">Password</h3>
              {isEditing ? (
                <input
                  type="password"
                  name="password"
                  value={profile.password}
                  onChange={handleInputChange}
                  className="w-full border-b border-gray-300 focus:outline-none"
                />
              ) : (
                <p>Password: {profile.password}</p>
              )}
            </div>
          </div>
        </div>
        <div className="mt-6">
          <h2 className="text-2xl font-semibold mb-4">Subscription Details</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-xl font-medium">Subscription Plan</h3>
              {isEditing ? (
                <input
                  type="text"
                  name="subscription"
                  value={profile.subscription}
                  onChange={handleInputChange}
                  className="w-full border-b border-gray-300 focus:outline-none"
                />
              ) : (
                <p>Plan: {profile.subscription}</p>
              )}
            </div>
          </div>
        </div>
        <div className="mt-6 flex justify-end space-x-4">
          {isEditing ? (
            <>
              <Button
                auto
                onClick={() => setIsEditing(false)}
                className="bg-red-500 text-white hover:bg-red-600 transition-all duration-300"
              >
                Cancel
              </Button>
              <Button
                auto
                onClick={handleSave}
                className="bg-green-500 text-white hover:bg-green-600 transition-all duration-300"
              >
                Save
              </Button>
            </>
          ) : (
            <Button
              auto
              onClick={() => setIsEditing(true)}
              className="bg-blue-500 text-white hover:bg-blue-600 transition-all duration-300"
            >
              Edit Profile
            </Button>
          )}
        </div>
        <div className="mt-6 flex flex-col space-y-4">
          <Link to="/privacy-policy" className="text-blue-500 hover:underline">
            Privacy Policy
          </Link>
          <Button
            auto
            onClick={handleDeleteAccount}
            className="bg-red-500 text-white hover:bg-red-600 transition-all duration-300"
          >
            Delete Account
          </Button>
        </div>
      </motion.div>
    </div>
  );
};

export default ProfilePage;
