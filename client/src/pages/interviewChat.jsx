import {Tabs, Tab} from "@nextui-org/react";
import React, { useEffect, useRef, useState } from "react";
import { Button } from "@nextui-org/react";
import { motion } from "framer-motion";
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area";
import { twMerge } from "tailwind-merge";
import { useNavigate, useParams } from "react-router-dom";
import VoiceButton from "../components/VoiceButton";
import InsightsSection from "../components/insightsSection";
import { bookDetails } from "./interview";


export default function InterviewChat() {
  const navigate = useNavigate();
  const { bookId } = useParams();
  const [messages, setMessages] = useState([
    { text: "Welcome to Lavar", isUser: false },
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
    <div className="flex w-full flex-col items-center">
      <Tabs aria-label="Options">
        <Tab key="Book" title="Book">
        <div className="w-auto h-auto p-6 bg-white shadow-lg rounded-xl flex flex-col justify-between">
          <img src={bookDetails.coverImage} alt={bookDetails.title} className="w-1/3 h-auto rounded-lg mb-4" />
          <h2 className="text-xl md:text-2xl font-semibold mb-2">{bookDetails.title}</h2>
          <h3 className="text-lg md:text-xl mb-2">{bookDetails.author}</h3>
          <p className="text-sm md:text-base text-gray-700">{bookDetails.description}</p>
        </div>
        </Tab>
        <Tab key="Chat" title="Chat">
          <div className="w-[97vw] h-[80vh]">
        <div className="w-full h-full flex flex-col bg-gradient-to-br from-gray-100 to-gray-200">        
          <MessageList messages={messages} />
          <div className="flex items-center justify-around bg-white shadow-lg rounded-xl gap-1 justify-self-end">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="border-2 border-gray-300 rounded-md outline-none focus:ring-2 focus:ring-blue-400 w-4/5"
              />
            <Button
              className="text-white bg-blue-500 rounded-md"
              onPress={ () => {
                 handleSendMessage(inputValue, true);
                }}
                >
              Send
            </Button>
            <VoiceButton func={handleSendMessage}/>
          </div>
        </div>
        </div>

        </Tab>
        <Tab key="Insights" title="Insights">
        <InsightsSection />
        </Tab>
      </Tabs>
    </div>  
  );
}


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
    <ScrollArea className="h-[80svh] fixed" viewportRef={viewportRef}>
      <div className="flex flex-col justify-end p-4 space-y-2 overflow-auto">
        {messages.map((message, index) => (
          <Message key={index} message={message} isUser={message.isUser} />
        ))}
      </div>
    </ScrollArea>
  );
};
