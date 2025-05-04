import { useEffect, useState } from "react";
import Button from "./base/Button";
import Vapi from "@vapi-ai/web";

const vapi = new Vapi("a5f4525c-163d-4f03-b430-cde030a0e13d");

const VoiceButton = ({ func }) => {
  const [user, setUser] = useState({});
  const [bg, setBg] = useState("#000000");
  const [token, setToken] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [assistantIsSpeaking, setAssistantIsSpeaking] = useState(false);
  const [volumeLevel, setVolumeLevel] = useState(0);

  useEffect(() => {
    const storedToken = sessionStorage.getItem("access_token");
    if (storedToken && storedToken.length > 10) {
      setToken(storedToken);
    }
  }, []);

  useEffect(() => {
    const getUser = async () => {
      if (!token) return;

      try {
        const res = await fetch(
          "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/custom_llm/user",
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
          setBg(data.user.current_bg);
        }
      } catch (err) {
        console.error("Failed to fetch user:", err);
      }
    };

    getUser();
  }, [token]);

  useEffect(() => {
    const onMessageUpdate = async (message) => {
      console.log(message);
      if (message.type === "transcript" && message.transcriptType === "final") {
        const role = message.role === "user" ? true : false;
        func(message.transcript, role);
      }
      if (message.type !== "function-call") return;

      if (message.functionCall.name === "changeBackground") {
        const parameter = message.functionCall.parameters;
        const addColor = () => {
          fetch(
            "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/custom_llm/color",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({ color: parameter.color }),
            },
          );
        };
        addColor();
        setBg(parameter.color);
        vapi.send(`Background has been changed to ${parameter.color}`);
      }

      if (message.functionCall.name === "finalizeDetail") {
        const params = message.functionCall.parameters;

        fetch(
          "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/custom_llm/character",
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
    };

    vapi.on("call-start", () => {
      setConnecting(false);
      setConnected(true);
    });

    vapi.on("call-end", () => {
      setConnecting(false);
      setConnected(false);
    });

    vapi.on("speech-start", () => {
      setAssistantIsSpeaking(true);
    });

    vapi.on("speech-end", () => {
      setAssistantIsSpeaking(false);
    });

    vapi.on("volume-level", (level) => {
      setVolumeLevel(level);
    });

    vapi.on("error", (error) => {
      console.error(error);
      setConnecting(false);
    });

    vapi.on("message", onMessageUpdate);

    return () => {
      vapi.off("message", onMessageUpdate);
    };
  }, [func, token]);

  const startCallInline = () => {
    setConnecting(true);
    vapi.start(addUserName(user.username || "friend"));
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

function addUserName(name) {
  const token = sessionStorage.getItem("access_token");
  const assistantOptions = {
    name: "Mary",
    firstMessage: `hi ${name}`,
    transcriber: {
      provider: "deepgram",
      model: "nova-2",
      language: "en-US",
    },
    voice: {
      provider: "playht",
      voiceId: "jennifer",
    },
    metadata: {
      token: token,
      data: {
        user: {
          username: name,
          email: "",
        },
      },
    },
    model: {
      model: "gpt-4o",
      provider: "custom-llm",
      url: "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/custom_llm/chat/completions",
      messages: [
        {
          role: "system",
          content: `You are another person who's main purpose is to change background colors and create superhero characters.
          Talk like an intelligent person who knows about every topic, you can explain in detail and can teach and very motivational, you can create superhero characters and these are the types of keys that are accepted: 'name', 'alias', 'super_skill', 'weakness', 'powers', 'equipments', 'height', 'age', 'birthplace'.
          Any time a user finalizes one of these, you will call the finalizeDetail function and pass in the appropriate key with the value. You can also help users generate values and guide in filling them out. Keep responses simple, casual, and voice-friendly.`,
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

  return assistantOptions;
}

export default VoiceButton;
