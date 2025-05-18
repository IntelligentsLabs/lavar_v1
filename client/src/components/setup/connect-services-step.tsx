import React, { useEffect } from 'react';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table2, FileSpreadsheet, LockIcon } from 'lucide-react';
import { initiateAirtableAuth, initiateGoogleAuth } from '@/lib/oauth';
import { useLocation, useRoute } from 'wouter';

interface ConnectServicesStepProps {
  airtableConnected: boolean;
  googleConnected: boolean;
  onAirtableConnect: () => void;
  onGoogleConnect: () => void;
  onNext: () => void;
}

export default function ConnectServicesStep({
  airtableConnected,
  googleConnected,
  onAirtableConnect,
  onGoogleConnect,
  onNext
}: ConnectServicesStepProps) {
  const [match] = useRoute('/auth/callback');
  const [location] = useLocation();
  
  // Check URL for auth parameters after OAuth redirect
  useEffect(() => {
    if (match && location.includes('state=')) {
      const urlParams = new URLSearchParams(location.split('?')[1]);
      const provider = urlParams.get('provider');
      
      if (provider === 'airtable') {
        onAirtableConnect();
      } else if (provider === 'google') {
        onGoogleConnect();
      }
    }
  }, [match, location, onAirtableConnect, onGoogleConnect]);
  
  const handleAirtableConnect = async () => {
    try {
      await initiateAirtableAuth();
    } catch (error) {
      console.error('Error initiating Airtable auth:', error);
    }
  };
  
  const handleGoogleConnect = async () => {
    try {
      await initiateGoogleAuth();
    } catch (error) {
      console.error('Error initiating Google auth:', error);
    }
  };
  
  return (
    <Card className="mb-8">
      <CardContent className="p-6">
        <h2 className="text-xl font-semibold mb-6">Connect Your Services</h2>
        <p className="text-gray-600 mb-6">
          To set up your integration, we need to connect to your Airtable and Google Sheets accounts. Click each button below to authorize access.
        </p>
        
        {airtableConnected && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
            <h3 className="text-md font-medium text-blue-800 mb-2">Airtable Connected!</h3>
            <p className="text-sm text-blue-600 mb-3">
              Your Airtable account is now connected. You'll be able to select bases and tables in the next step.
            </p>
            <Button 
              variant="outline"
              size="sm"
              className="text-sm"
              onClick={async () => {
                try {
                  const response = await fetch('/api/test/airtable/bases');
                  const data = await response.json();
                  
                  if (data.success) {
                    alert(`Successfully connected to Airtable! Found ${data.bases.length} bases.`);
                  } else {
                    alert(`Error testing Airtable connection: ${data.message}`);
                  }
                } catch (error) {
                  alert(`Error testing Airtable connection: ${error}`);
                }
              }}
            >
              Test Connection
            </Button>
          </div>
        )}
        
        <div className="space-y-6">
          {/* Airtable Connection */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-5 border rounded-lg">
            <div className="flex items-center">
              <div className="w-12 h-12 flex-shrink-0 bg-blue-100 rounded-lg flex items-center justify-center">
                <Table2 className="text-blue-600 text-2xl" />
              </div>
              <div className="ml-4">
                <h3 className="font-medium text-gray-900">Airtable</h3>
                <p className="text-gray-500 text-sm">Connect to access and modify your bases</p>
              </div>
            </div>
            {airtableConnected ? (
              <div className="mt-4 sm:mt-0 flex space-x-2">
                <div className="px-4 py-2 rounded-md bg-green-100 text-green-800 font-medium flex items-center">
                  <CheckIcon className="mr-1 h-4 w-4" /> Connected
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={async () => {
                    try {
                      await fetch('/api/oauth/logout?provider=airtable', {
                        method: 'POST'
                      });
                      // Set Airtable as disconnected
                      onAirtableConnect();
                      window.location.reload(); // Force reload to clear state
                    } catch (error) {
                      console.error('Error disconnecting:', error);
                    }
                  }}
                  className="border-red-200 text-red-600 hover:text-red-700"
                >
                  Disconnect
                </Button>
              </div>
            ) : (
              <Button 
                onClick={handleAirtableConnect}
                className="mt-4 sm:mt-0 bg-blue-600 hover:bg-blue-700"
              >
                Connect Airtable
              </Button>
            )}
          </div>

          {/* Google Sheets Connection */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-5 border rounded-lg">
            <div className="flex items-center">
              <div className="w-12 h-12 flex-shrink-0 bg-green-100 rounded-lg flex items-center justify-center">
                <FileSpreadsheet className="text-green-600 text-2xl" />
              </div>
              <div className="ml-4">
                <h3 className="font-medium text-gray-900">Google Sheets</h3>
                <p className="text-gray-500 text-sm">Connect to access and modify your spreadsheets</p>
              </div>
            </div>
            {googleConnected ? (
              <div className="mt-4 sm:mt-0 flex space-x-2">
                <div className="px-4 py-2 rounded-md bg-green-100 text-green-800 font-medium flex items-center">
                  <CheckIcon className="mr-1 h-4 w-4" /> Connected
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={async () => {
                    try {
                      await fetch('/api/oauth/logout?provider=google', {
                        method: 'POST'
                      });
                      // Set Google as disconnected
                      onGoogleConnect();
                      window.location.reload(); // Force reload to clear state
                    } catch (error) {
                      console.error('Error disconnecting:', error);
                    }
                  }}
                  className="border-red-200 text-red-600 hover:text-red-700"
                >
                  Disconnect
                </Button>
              </div>
            ) : (
              <Button 
                onClick={handleGoogleConnect}
                className="mt-4 sm:mt-0 bg-green-600 hover:bg-green-700"
              >
                Connect Google Sheets
              </Button>
            )}
          </div>
        </div>
      </CardContent>
      
      <CardFooter className="px-6 py-4 bg-gray-50 rounded-b-lg border-t flex justify-between items-center">
        <div>
          <p className="text-sm text-gray-500 flex items-center">
            <LockIcon className="h-4 w-4 mr-1" />
            Your data and credentials are securely handled
          </p>
        </div>
        <Button
          onClick={onNext}
          disabled={!airtableConnected}
          variant={!airtableConnected ? "secondary" : "default"}
        >
          Continue
        </Button>
      </CardFooter>
    </Card>
  );
}

function CheckIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}
