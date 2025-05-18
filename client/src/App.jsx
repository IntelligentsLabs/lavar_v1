import { Routes, Route, BrowserRouter } from "react-router-dom";
import Authorize from "./auth/Authorize";
import LandingPage from "./pages/landingpage";
import Layout from "./layout/layout";
import ProfilePage from "./pages/profile";
import InterviewPage from "./pages/interview";
import LibraryPage from "./pages/library";
import CreateStackPage from "./pages/createStack";
import BookDetails from "./pages/bookDetails";
import InsightPage from "./pages/insights";
import Dashboard from "./pages/dashboard";
import StackBooksPage from "./pages/stackDetails";
import PremiumPage from "./pages/non-premium";
import PremiumFeaturesPage from "./pages/premium";
import { useState } from "react";
import InterviewChat from "./pages/interviewChat";

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/authorize" element={<Authorize />} />
        <Route path="/*" element={<MainLayout />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;

const MainLayout = () => {
  const [isPremium, setIsPremium] = useState(false);

  return (
    <>
      <main className="h-full text-foreground bg-background flex flex-col">
        <Layout setIsPremium={setIsPremium} isPremium={isPremium}>
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
<Route path="/integrations" element={<IntegrationDashboard />} />
            <Route path="/stack/chat/:id" element={<InterviewPage />} />
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/interview" element={<InterviewChat />} />
            <Route path="/createstack" element={<CreateStackPage />} />
            <Route path="/stackDetails" element={<StackBooksPage />} />
            <Route path="/bookdetails/:id" element={<BookDetails />} />
            <Route path="/assessment" element={<>Assessment</>} />
            <Route path="/insight" element={<InsightPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<>settings</>} />
            <Route path="/faq" element={<>Help & Feedback</>} />
            <Route path="/premium" element={<PremiumPage setIsPremium={setIsPremium} />} />
            <Route path="/non-premium" element={<PremiumFeaturesPage setIsPremium={setIsPremium}/>} />
          </Routes>
        </Layout>
      </main>
    </>
  );
};
