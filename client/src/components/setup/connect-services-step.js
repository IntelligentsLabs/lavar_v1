var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import React, { useEffect } from 'react';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table2, FileSpreadsheet, LockIcon } from 'lucide-react';
import { initiateAirtableAuth, initiateGoogleAuth } from '@/lib/oauth';
import { useLocation, useRoute } from 'wouter';
export default function ConnectServicesStep({ airtableConnected, googleConnected, onAirtableConnect, onGoogleConnect, onNext }) {
    const [match] = useRoute('/auth/callback');
    const [location] = useLocation();
    // Check URL for auth parameters after OAuth redirect
    useEffect(() => {
        if (match && location.includes('state=')) {
            const urlParams = new URLSearchParams(location.split('?')[1]);
            const provider = urlParams.get('provider');
            if (provider === 'airtable') {
                onAirtableConnect();
            }
            else if (provider === 'google') {
                onGoogleConnect();
            }
        }
    }, [match, location, onAirtableConnect, onGoogleConnect]);
    const handleAirtableConnect = () => __awaiter(this, void 0, void 0, function* () {
        try {
            yield initiateAirtableAuth();
        }
        catch (error) {
            console.error('Error initiating Airtable auth:', error);
        }
    });
    const handleGoogleConnect = () => __awaiter(this, void 0, void 0, function* () {
        try {
            yield initiateGoogleAuth();
        }
        catch (error) {
            console.error('Error initiating Google auth:', error);
        }
    });
    return (React.createElement(Card, { className: "mb-8" },
        React.createElement(CardContent, { className: "p-6" },
            React.createElement("h2", { className: "text-xl font-semibold mb-6" }, "Connect Your Services"),
            React.createElement("p", { className: "text-gray-600 mb-6" }, "To set up your integration, we need to connect to your Airtable and Google Sheets accounts. Click each button below to authorize access."),
            airtableConnected && (React.createElement("div", { className: "mb-6 p-4 bg-blue-50 border border-blue-200 rounded-md" },
                React.createElement("h3", { className: "text-md font-medium text-blue-800 mb-2" }, "Airtable Connected!"),
                React.createElement("p", { className: "text-sm text-blue-600 mb-3" }, "Your Airtable account is now connected. You'll be able to select bases and tables in the next step."),
                React.createElement(Button, { variant: "outline", size: "sm", className: "text-sm", onClick: () => __awaiter(this, void 0, void 0, function* () {
                        try {
                            const response = yield fetch('/api/test/airtable/bases');
                            const data = yield response.json();
                            if (data.success) {
                                alert(`Successfully connected to Airtable! Found ${data.bases.length} bases.`);
                            }
                            else {
                                alert(`Error testing Airtable connection: ${data.message}`);
                            }
                        }
                        catch (error) {
                            alert(`Error testing Airtable connection: ${error}`);
                        }
                    }) }, "Test Connection"))),
            React.createElement("div", { className: "space-y-6" },
                React.createElement("div", { className: "flex flex-col sm:flex-row items-start sm:items-center justify-between p-5 border rounded-lg" },
                    React.createElement("div", { className: "flex items-center" },
                        React.createElement("div", { className: "w-12 h-12 flex-shrink-0 bg-blue-100 rounded-lg flex items-center justify-center" },
                            React.createElement(Table2, { className: "text-blue-600 text-2xl" })),
                        React.createElement("div", { className: "ml-4" },
                            React.createElement("h3", { className: "font-medium text-gray-900" }, "Airtable"),
                            React.createElement("p", { className: "text-gray-500 text-sm" }, "Connect to access and modify your bases"))),
                    airtableConnected ? (React.createElement("div", { className: "mt-4 sm:mt-0 flex space-x-2" },
                        React.createElement("div", { className: "px-4 py-2 rounded-md bg-green-100 text-green-800 font-medium flex items-center" },
                            React.createElement(CheckIcon, { className: "mr-1 h-4 w-4" }),
                            " Connected"),
                        React.createElement(Button, { variant: "outline", size: "sm", onClick: () => __awaiter(this, void 0, void 0, function* () {
                                try {
                                    yield fetch('/api/oauth/logout?provider=airtable', {
                                        method: 'POST'
                                    });
                                    // Set Airtable as disconnected
                                    onAirtableConnect();
                                    window.location.reload(); // Force reload to clear state
                                }
                                catch (error) {
                                    console.error('Error disconnecting:', error);
                                }
                            }), className: "border-red-200 text-red-600 hover:text-red-700" }, "Disconnect"))) : (React.createElement(Button, { onClick: handleAirtableConnect, className: "mt-4 sm:mt-0 bg-blue-600 hover:bg-blue-700" }, "Connect Airtable"))),
                React.createElement("div", { className: "flex flex-col sm:flex-row items-start sm:items-center justify-between p-5 border rounded-lg" },
                    React.createElement("div", { className: "flex items-center" },
                        React.createElement("div", { className: "w-12 h-12 flex-shrink-0 bg-green-100 rounded-lg flex items-center justify-center" },
                            React.createElement(FileSpreadsheet, { className: "text-green-600 text-2xl" })),
                        React.createElement("div", { className: "ml-4" },
                            React.createElement("h3", { className: "font-medium text-gray-900" }, "Google Sheets"),
                            React.createElement("p", { className: "text-gray-500 text-sm" }, "Connect to access and modify your spreadsheets"))),
                    googleConnected ? (React.createElement("div", { className: "mt-4 sm:mt-0 flex space-x-2" },
                        React.createElement("div", { className: "px-4 py-2 rounded-md bg-green-100 text-green-800 font-medium flex items-center" },
                            React.createElement(CheckIcon, { className: "mr-1 h-4 w-4" }),
                            " Connected"),
                        React.createElement(Button, { variant: "outline", size: "sm", onClick: () => __awaiter(this, void 0, void 0, function* () {
                                try {
                                    yield fetch('/api/oauth/logout?provider=google', {
                                        method: 'POST'
                                    });
                                    // Set Google as disconnected
                                    onGoogleConnect();
                                    window.location.reload(); // Force reload to clear state
                                }
                                catch (error) {
                                    console.error('Error disconnecting:', error);
                                }
                            }), className: "border-red-200 text-red-600 hover:text-red-700" }, "Disconnect"))) : (React.createElement(Button, { onClick: handleGoogleConnect, className: "mt-4 sm:mt-0 bg-green-600 hover:bg-green-700" }, "Connect Google Sheets"))))),
        React.createElement(CardFooter, { className: "px-6 py-4 bg-gray-50 rounded-b-lg border-t flex justify-between items-center" },
            React.createElement("div", null,
                React.createElement("p", { className: "text-sm text-gray-500 flex items-center" },
                    React.createElement(LockIcon, { className: "h-4 w-4 mr-1" }),
                    "Your data and credentials are securely handled")),
            React.createElement(Button, { onClick: onNext, disabled: !airtableConnected, variant: !airtableConnected ? "secondary" : "default" }, "Continue"))));
}
function CheckIcon(props) {
    return (React.createElement("svg", Object.assign({}, props, { xmlns: "http://www.w3.org/2000/svg", width: "24", height: "24", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round" }),
        React.createElement("path", { d: "M20 6 9 17l-5-5" })));
}
