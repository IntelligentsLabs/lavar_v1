var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
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
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);
    useEffect(() => {
        const processAuthCallback = () => __awaiter(this, void 0, void 0, function* () {
            try {
                // Get query parameters
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
                // Get the saved OAuth state
                const savedState = getOAuthState(state);
                if (!savedState) {
                    throw new Error('Invalid state parameter');
                }
                // Exchange the code for a token
                const success = yield exchangeCodeForToken(code, savedState.provider, savedState.codeVerifier, savedState.redirectUri);
                if (!success) {
                    throw new Error('Failed to exchange code for token');
                }
                // Clear the saved state
                clearOAuthState(state);
                // Show success message
                setIsProcessing(false);
                setSuccess(true);
                // Add provider info to url when redirecting back to home
                const provider = savedState.provider;
                setTimeout(() => {
                    setLocation(`/?provider=${provider}&connected=true`);
                }, 2000);
            }
            catch (error) {
                console.error('Auth callback error:', error);
                setIsProcessing(false);
                setError(error instanceof Error ? error.message : 'An unknown error occurred');
            }
        });
        processAuthCallback();
    }, [setLocation]);
    return (React.createElement("div", { className: "min-h-screen w-full flex items-center justify-center bg-gray-50 p-4" },
        React.createElement(Card, { className: "w-full max-w-md" },
            React.createElement(CardContent, { className: "pt-6" },
                isProcessing ? (React.createElement("div", { className: "flex flex-col items-center justify-center py-6" },
                    React.createElement(Loader2, { className: "h-12 w-12 text-primary animate-spin mb-4" }),
                    React.createElement("h2", { className: "text-xl font-semibold text-gray-900 mb-2" }, "Processing Authentication"),
                    React.createElement("p", { className: "text-gray-600 text-center" }, "Please wait while we complete the authentication process..."))) : error ? (React.createElement(Alert, { variant: "destructive", className: "mb-4" },
                    React.createElement(AlertCircle, { className: "h-4 w-4" }),
                    React.createElement(AlertTitle, null, "Authentication Failed"),
                    React.createElement(AlertDescription, null, error))) : success ? (React.createElement(Alert, { className: "mb-4 border-green-200 bg-green-50" },
                    React.createElement(CheckCircle2, { className: "h-4 w-4 text-green-600" }),
                    React.createElement(AlertTitle, { className: "text-green-800" }, "Authentication Successful"),
                    React.createElement(AlertDescription, { className: "text-green-700" }, "You've successfully connected your account. Redirecting you back..."))) : null,
                (error || success) && (React.createElement("div", { className: "flex justify-center mt-4" },
                    React.createElement(Button, { onClick: () => setLocation('/'), variant: error ? "destructive" : "default" }, error ? "Try Again" : "Return to Setup")))))));
}
