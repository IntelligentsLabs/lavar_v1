import { Button, Image } from '@nextui-org/react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const goals = {
  primary: [
    {
      title: 'Challenges',
      description: 'Ac placerat vestibulum lectus eros.',
      image: 'https://i.imgur.com/LpS6tOdb.jpg',
    },
    {
      title: 'Motivations',
      description: 'Ac placerat vestibulum lectus eros.',
      image: 'https://i.imgur.com/3ODXP7Bb.jpg',
    },
  ],
  secondary: [
    {
      title: 'Wake Up',
      description: 'Ac placerat vestibulum lectus mauris ultricies eros. Ut lectus arcu bibendum at.',
      image: 'https://i.imgur.com/NwFmtuCb.jpg',
    },
    {
      title: 'Mid Day Check In',
      description: 'Ac placerat vestibulum lectus eros. Ut lectus arcu bibendum at.',
      image: 'https://i.imgur.com/hMPNlGjb.jpg',
    },
    {
      title: 'Mid Day Check In',
      description: 'Ac placerat vestibulum lectus eros. Ut lectus arcu bibendum at.',
      image: 'https://i.imgur.com/whhXv6Hb.jpg',
    },
  ],
};

const GoalCard = ({ title, description, image }) => (
<div className="mb-4 p-4 flex items-center space-x-4 rounded-lg bg-gray-50 shadow-sm">
  <Image
    src={image}
    alt={title}
    className="rounded-full w-1/2 h-1/2 object-cover"
  />

  <div>
    <h4 className="font-semibold text-base sm:text-lg lg:text-xl">{title}</h4>
    <p className="text-gray-500 text-sm sm:text-base lg:text-lg">{description}</p>
  </div>
</div>

);

const Dashboard = () => {
  const navigate = useNavigate();
  const [isPremium, setIsPremium] = useState(false);

  return (
    <div className="h-full bg-gray-100 flex items-center justify-center p-6">
      <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-3xl">
        <h2 className="text-2xl font-bold mb-6 text-center">Your Insights</h2>

        <div className="mb-8">
          <h3 className="text-xl font-semibold mb-4">Primary Goals</h3>
          {goals.primary.map((goal, index) => (
            <GoalCard
              key={index}
              title={goal.title}
              description={goal.description}
              image={goal.image}
            />
          ))}
        </div>

        <div className="mb-8">
          <h3 className="text-xl font-semibold mb-4">Secondary Goals</h3>
          {goals.secondary.map((goal, index) => (
            <GoalCard
              key={index}
              title={goal.title}
              description={goal.description}
              image={goal.image}
            />
          ))}
        </div>

        <div className="flex flex-col gap-2 w-44 mx-auto">
          <Button auto flat color="primary" className='rounded-3xl'>
            Chat With The Coach
          </Button>
          {!isPremium && (
            <Button
              auto
              onClick={() => navigate('/non-premium')}
              color="foreground"
              className="text-primary-500 border-primary-500 rounded-3xl border-2"
            >
              Go Premium
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
