import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { initiateAirtableAuth, initiateGoogleAuth } from '../lib/oauth';
import { Button } from '../components/ui/button';

export default function IntegrationDashboard() {
  const [airtableConnected, setAirtableConnected] = useState(false);
  const [googleConnected, setGoogleConnected] = useState(false);

  useEffect(() => {
    // Check if services are already connected, could use local state or check from server
    // populateOAuthState();
  }, []);

  const handleAirtableConnect = async () => {
    try {
      await initiateAirtableAuth();
      setAirtableConnected(true);
    } catch (error) {
      console.error('Error connecting to Airtable:', error);
    }
  };

  const handleGoogleConnect = async () => {
    try {
      await initiateGoogleAuth();
      setGoogleConnected(true);
    } catch (error) {
      console.error('Error connecting to Google Sheets:', error);
    }
  };

  // Example of an API call to fetch Airtable bases
  const fetchAirtableBases = async () => {
    try {
      const response = await fetch('/api/airtable/bases');
      const data = await response.json();
      console.log('Airtable Bases:', data);
    } catch (error) {
      console.error('Failed to fetch Airtable bases:', error);
    }
  };

  return (
    <div className="min-h-screen p-6">
      <Card>
        <CardContent>
          <h2 className="text-xl font-semibold mb-4">Integration Dashboard</h2>
          <div className="space-y-4">
            <Button onClick={handleAirtableConnect}>
              {airtableConnected ? 'Airtable Connected' : 'Connect Airtable'}
            </Button>
            <Button onClick={handleGoogleConnect}>
              {googleConnected ? 'Google Sheets Connected' : 'Connect Google Sheets'}
            </Button>
            {airtableConnected && (
              <Button onClick={fetchAirtableBases}>
                Fetch Airtable Bases
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}