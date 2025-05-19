
import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { getOAuthState, exchangeCodeForToken, clearOAuthState } from '@/lib/oauth';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export default function AuthCallback() {
  const [, setLocation] = useLocation();
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  useEffect(() => {
    const processAuthCallback = async () => {
      try {
        const queryParams = new URLSearchParams(window.location.search);
        const code = queryParams.get('code');
        const state = queryParams.get('state');
        const error = queryParams.get('error');

        if (error) {
          throw new Error(`Authorization error: ${error}`);
        }
        
        if (!code || !state) {
          throw new Error('Missing required parameters (code or state)');
        }
        
        const savedState = getOAuthState(state);
        if (!savedState) {
          throw new Error('Invalid state parameter');
        }
        
        const success = await exchangeCodeForToken(
          code,
          savedState.provider,
          savedState.codeVerifier,
          savedState.redirectUri
        );
        
        if (!success) {
          throw new Error('Failed to exchange code for token');
        }

        clearOAuthState(state);
        setIsProcessing(false);
        setSuccess(true);
        
        const provider = savedState.provider;
        setTimeout(() => {
          setLocation(`/?provider=${provider}&connected=true`);
        }, 2000);
      } catch (error) {
        console.error('Auth callback error:', error);
        setIsProcessing(false);
        setError(error instanceof Error ? error.message : 'An unknown error occurred');
      }
    };
    
    processAuthCallback();
  }, [setLocation]);
  
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          {isProcessing ? (
            <div className="flex flex-col items-center justify-center py-6">
              <Loader2 className="h-12 w-12 text-primary animate-spin mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Processing Authentication</h2>
              <p className="text-gray-600 text-center">Please wait while we complete the authentication process...</p>
            </div>
          ) : error ? (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Authentication Failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : success ? (
            <Alert className="mb-4 border-green-200 bg-green-50">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertTitle className="text-green-800">Authentication Successful</AlertTitle>
              <AlertDescription className="text-green-700">
                You've successfully connected your account. Redirecting you back...
              </AlertDescription>
            </Alert>
          ) : null}
          
          {(error || success) && (
            <div className="flex justify-center mt-4">
              <Button 
                onClick={() => setLocation('/')}
                variant={error ? "destructive" : "default"}
              >
                {error ? "Try Again" : "Return to Setup"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
