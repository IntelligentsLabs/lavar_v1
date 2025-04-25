import React, { useEffect, useRef, useState } from "react";
import { Button } from "@nextui-org/react";
import { motion } from "framer-motion";
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area";
import { twMerge } from "tailwind-merge";
import { useNavigate, useParams } from "react-router-dom";
import VoiceButton from "../components/VoiceButton";
import InsightsSection from "../components/insightsSection";

export const bookDetails = {
  title: "Atomic Habits",
  author: "James Clear",
  description: `"Atomic Habits" by James Clear is a bestselling self-help book that explores how small, consistent actions—known as "atomic habits"—can lead to significant life improvements. The book offers practical strategies for building good habits, breaking bad ones, and achieving long-term success through tiny, incremental changes. It's widely praised for its actionable advice on habit formation and personal growth.`,
  coverImage: `data:image/jpeg;base64,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`
};

const ScrollArea = React.forwardRef(
  ({ className, children, viewportRef, ...props }, ref) => (
    <ScrollAreaPrimitive.Root
      ref={ref}
      className={twMerge("relative overflow-hidden", className)}
      {...props}
    >
      <ScrollAreaPrimitive.Viewport
        ref={viewportRef}
        className="h-full w-full rounded-[inherit]"
      >
        {React.Children.only(children)}
      </ScrollAreaPrimitive.Viewport>
      <ScrollBar />
      <ScrollAreaPrimitive.Corner />
    </ScrollAreaPrimitive.Root>
  )
);

const ScrollBar = React.forwardRef(
  ({ className, orientation = "vertical", ...props }, ref) => (
    <ScrollAreaPrimitive.ScrollAreaScrollbar
      ref={ref}
      orientation={orientation}
      className={twMerge(
        "flex touch-none select-none transition-colors",
        orientation === "vertical" &&
          "h-full w-2.5 border-l border-l-transparent p-[1px]",
        orientation === "horizontal" &&
          "h-2.5 flex-col border-t border-t-transparent p-[1px]",
        className
      )}
      {...props}
    >
      <ScrollAreaPrimitive.ScrollAreaThumb className="relative flex-1 rounded-full bg-slate-200 dark:bg-slate-800" />
    </ScrollAreaPrimitive.ScrollAreaScrollbar>
  )
);

const Message = ({ message, isUser }) => (
  <div
    className={`w-auto max-w-96 p-2 ${
      isUser ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-950"
    } dark:${
      isUser ? "bg-blue-700" : "bg-gray-800 text-gray-200"
    } rounded-md shadow-md mb-2 ${isUser ? "self-end" : "self-start"}`}
  >
    <p>{message.text}</p>
  </div>
);

const MessageList = ({ messages }) => {
  const viewportRef = useRef(null);

  const scrollToBottom = () => {
    const viewport = viewportRef.current;
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <ScrollArea className="h-[50vh] md:h-[70vh] w-full" viewportRef={viewportRef}>
      <div className="flex flex-col min-h-[50vh] md:min-h-[70vh] justify-end p-4 space-y-2">
        {messages.map((message, index) => (
          <Message key={index} message={message} isUser={message.isUser} />
        ))}
      </div>
    </ScrollArea>
  );
};

const InterviewPage = () => {
  const navigate = useNavigate();
  const { bookId } = useParams(); // Getting the book ID from the URL params
  const [messages, setMessages] = useState([
    { text: "Welcome to Colloquial", isUser: false },
    { text: "Type in your message.", isUser: false },
  ]);
  const [inputValue, setInputValue] = useState("");
  const handleSendMessage = (message, isUser) => {
    if (message.trim()) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { text: message, isUser },
      ]);
      if (isUser) {
        setInputValue("")
      }
    }
  };

  const AIMessage = () => {
    setTimeout(async () => {
      const message = "You sent a message, this is my reply.";
      handleSendMessage(message, false);
    }, 3000);
  };

  return (
    <div className="flex flex-col items-center">
      <main className="flex flex-col md:flex-row h-auto w-full">
        <div className="w-full md:w-1/4 p-6 bg-white shadow-lg rounded-xl flex flex-col items-center">
          <img src={bookDetails.coverImage} alt={bookDetails.title} className="w-full h-auto rounded-lg mb-4" />
          <h2 className="text-xl md:text-2xl font-semibold mb-2">{bookDetails.title}</h2>
          <h3 className="text-lg md:text-xl mb-2">{bookDetails.author}</h3>
          <p className="text-sm md:text-base text-gray-700">{bookDetails.description}</p>
        </div>

        <div className="w-full md:w-2/4 h-auto flex flex-col justify-between bg-gradient-to-br from-gray-100 to-gray-200 p-4">
          <MessageList messages={messages} />
          <div className="flex items-center p-4 bg-white shadow-lg gap-1 rounded-xl">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="flex-1 px-4 py-2 border-2 border-gray-300 rounded-md outline-none focus:ring-2 focus:ring-blue-400"
            />
            <Button
              className="text-white bg-blue-500 p-3 rounded-md"
              onPress={ () => {
                 handleSendMessage(inputValue, true);
              }}
            >
              Send
            </Button>
            <VoiceButton func={handleSendMessage}/>
          </div>
        </div>

      </main>
    </div>
  );
};

export default InterviewPage;
