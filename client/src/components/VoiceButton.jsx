import { useEffect, useState, useCallback } from "react";
import Button from "./base/Button";
import Vapi from "@vapi-ai/web";

const vapi = new Vapi("226815bb-8ad3-4c2e-bc81-a973f0fb163c");
const REACT_APP_BACKEND_URL = import.meta.env.VITE_API_BASE_URL || ""; // Use VITE_API_BASE_URL or default to empty string

console.log(import.meta.env.VITE_VAPI_API_KEY); // Use VITE_VAPI_API_KEY
const VoiceButton = ({ func }) => {
  const [user, setUser] = useState({});
  const [token, setToken] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const storedToken = sessionStorage.getItem("access_token");
    if (storedToken && storedToken.length > 10) {
      setToken(storedToken);
    }
  }, []);

  const getUser = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(
        `${REACT_APP_BACKEND_URL}/api/custom_llm/user`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        },
      );
      const data = await res.json();
      if (data.success) {
        setUser(data.user);
      }
    } catch (err) {
      console.error("Failed to fetch user:", err);
    }
  }, [token]);

  useEffect(() => {
    getUser();
  }, [getUser]);

  const onMessageUpdate = useCallback(
    async (message) => {
      console.log(message);
      if (message.type === "transcript" && message.transcriptType === "final") {
        const role = message.role === "user" ? true : false;
        func(message.transcript, role);
      }
      if (message.type !== "function-call") return;

      if (message.functionCall.name === "changeBackground") {
        const parameter = message.functionCall.parameters;
        fetch(
          `${REACT_APP_BACKEND_URL}/api/custom_llm/color`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ color: parameter.color }),
          },
        );
        vapi.send(`Background has been changed to ${parameter.color}`);
      }

      if (message.functionCall.name === "finalizeDetail") {
        const params = message.functionCall.parameters;
        fetch(
           `${REACT_APP_BACKEND_URL}/api/custom_llm/character`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ key: params.key, value: params.value }),
          },
        )
          .then((res) => res.json())
          .then((data) => {
            if (data.success) {
              vapi.send(
                `Your character's ${params.key} has been set to ${params.value}`,
              );
            }
          });
      }
    },
    [func, token],
  );

  const onCallStart = useCallback(() => {
    setConnecting(false);
    setConnected(true);
  }, []);

  const onCallEnd = useCallback(() => {
    setConnecting(false);
    setConnected(false);
  }, []);

  const onError = useCallback((error) => {
    console.error(error);
    setConnecting(false);
  }, []);

  useEffect(() => {
    vapi.on("call-start", onCallStart);
    vapi.on("call-end", onCallEnd);
    vapi.on("error", onError);
    vapi.on("message", onMessageUpdate);

    return () => {
      vapi.off("call-start", onCallStart);
      vapi.off("call-end", onCallEnd);
      vapi.off("error", onError);
      vapi.off("message", onMessageUpdate);
    };
  }, [onCallStart, onCallEnd, onError, onMessageUpdate]);

  const startCallInline = () => {
    setConnecting(true);
    vapi.start("524f1032-277d-4348-bbfd-71b8dc445713", addUserName(user));
  };

  const endCall = () => {
    vapi.stop();
  };

  return (
    <Button
      onClick={startCallInline}
      isLoading={connecting || connected}
      onEndCall={endCall}
    />
  );
};

function addUserName(user) {
  console.log("************THIS IS THE USER************", user);
  const token = sessionStorage.getItem("access_token");
  return {
    name: "Mary",
    firstMessage: `hi ${user.username || "friend"}`,
    metadata: {
      token,
      data: {
        user: {
          username: user.username || "",
          email: user.email || "",
          ...user,
        },
      },
    },
    model: {
      model: "gpt-4.1-nano-2025-04-14",
      provider: "custom-llm",
      url: `${REACT_APP_BACKEND_URL}/api/custom_llm/chat/completions`,
      messages: [
        {
          role: "system",
          content: `You are a highly skilled assistant, deeply knowledgeable about the principles and strategies outlined in "Atomic Habits" by                          James Clear. Your primary role is to guide individuals in effectively applying these principles to their daily lives, assisting                      them in establishing, maintaining, and excelling in their personal and professional habits to achieve their goals. Here's how                        you'll accomplish this:
                    Understand the User's Goals:
                    Begin by engaging users in a conversation to clearly understand their long-term goals and the habits they believe will lead to                       those goals. Ask specific questions to clarify these goals and habits, ensuring they are measurable and achievable.
                    Break Down Goals into Atomic Habits:
                    Help users break down their broad goals into smaller, actionable habits. Emphasize the importance of making these habits as                          small and manageable as possible to ensure consistency and reduce overwhelm.`,
        },
      ],
      functions: [
        {
          name: "finalizeDetail",
          description:
            "Each time a detail has been finalized, this function should be called so that the user can be informed.",
          parameters: {
            type: "object",
            properties: {
              key: {
                type: "string",
                description: "e.g. name, alias, super_skill, etc.",
              },
              value: {
                type: "string",
                description: "The finalized value for the detail.",
              },
            },
          },
        },
        {
          name: "changeBackground",
          description:
            "Each time the user wants to change the background color, this function should be called.",
          parameters: {
            type: "object",
            properties: {
              color: {
                type: "string",
                description:
                  "A valid CSS color or hex code, e.g., blue, #fff, etc.",
              },
            },
          },
        },
      ],
    },
  };
}

export default VoiceButton;