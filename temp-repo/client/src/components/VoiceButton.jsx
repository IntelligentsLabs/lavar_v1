import { useEffect, useState } from "react";

import Button from "./base/Button";
import Vapi from "@vapi-ai/web";

// Put your Vapi Public Key below.
const vapi = new Vapi("a5f4525c-163d-4f03-b430-cde030a0e13d");

const VoiceButton = ({ func }) => {
  const token =
    sessionStorage.getItem("access_token") !== null
      ? sessionStorage.getItem("access_token")
      : "";
  const isAuthenticated = token.length > 10 ? true : false;
  const getUser = async () => {
    const res = await fetch("https://ec2-100-29-60-61.compute-1.amazonaws.com:5001/user", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    const data = await res.json();
    if (data.success) {
      setUser(data.user);
      setBg(data.user.current_bg);
    }
  };
  useEffect(() => {
    getUser();
  }, []);
  const [user, setUser] = useState({});
  const [bg, setBg] = useState("#00000");
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);

  const [assistantIsSpeaking, setAssistantIsSpeaking] = useState(false);
  const [volumeLevel, setVolumeLevel] = useState(0);

  useEffect(() => {
    const onMessageUpdate = async (message) => {
      console.log(message)
      if (message.type === "transcript" && message.transcriptType === 'final') {
        const role = message.role === 'user' ? true : false
        func(message.transcript, role)
      }
      if (message.type !== "function-call") return
      if (message.functionCall.name === "changeBackground") {
        const parameter = message.functionCall.parameters;
        const addColor = () => {
          fetch("https://ec2-100-29-60-61.compute-1.amazonaws.com:5001/color", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              color: parameter.color,
            }),
          });
        };
        addColor();
        setBg(parameter.color);
        vapi.send(`Background has been changed to ${parameter.color}`);
      }
      if (message.functionCall.name === "finalizeDetail") {
        const params = message.functionCall.parameters;

        fetch("https://ec2-100-29-60-61.compute-1.amazonaws.com:5001/character", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            key: params.key,
            value: params.value,
          }),
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.success) {
              vapi.send(
                `Your character's ${params.key} has been set to ${params.value}`
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
    }
  }, []);

  const startCallInline = () => {
    setConnecting(true);
    vapi.start(addUserName(user.username));
  };
  const endCall = () => {
    vapi.stop();
  };

  return (
    <>

      <Button
        onClick={startCallInline}
        isLoading={connecting || connected}
        onEndCall={endCall}
      />
    </>
  );
};


function addUserName(name) {
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
    model: {
      provider: "openai",
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: `You are another person who's main purpose is to change background colors and create superhero characters.
          Talk like an intelligent person who knows about every topic, you can explain in detail and can teach and very motivational, you can create superhero characters and these are the types of keys that are accepted        'name': '', 
                'alias', 
                'super_skill', 
                'weakness' , 
                'powers', 
                'equipments', 
                'height', 
                'age':, 
                'birthplace',
                any time a user finalizes of these, you will call the finalize detail function and pass in the approprriate key with the value, you can also help user generate random values if they are not sure of what to put, and also guide in filling it out.
                 . You are also going to brain storm with me and keep track of what we set by using the finalizeDetail function call, let it be set often also, It should be called often also. You will also change the background color any time i tell you to, make sure the color is a valid css value.
  - Keep all your responses and simple. Use casual language, phrases like "Umm...", "Well...", and "I mean" are preferred, don't use them every time tho. and can also explain things too.
  - This is a voice conversation, so keep your responses short or mid, like in a real conversation. Don't ramble for too long.`,
        },
      ],
      functions: [
        {
          name: "finalizeDetail",
          description:
            "Each time a detail has been finalized, this function should be called so that the user can be informed about the same.",
          parameters: {
            type: "object",
            properties: {
              key: {
                type: "string",
                description:
                  "This is the key or detail for which the values have been set. For example, key can be name, short description, User interface, appearance, application, tech stack, what to learn etc.",
              },
              value: {
                type: "string",
                description:
                  "This is the value of the detail which the user is finalizing. For example, if the key is name, then the value can be John Doe if user has decided that.",
              },
            },
          },
        },
        {
          name: "changeBackground",
          description:
            "Each time the user wants to change the background color, this function should be called so that the background color can be changed. It should be a valid css color or hexcode, if not set it to the closest",
          parameters: {
            type: "object",
            properties: {
              color: {
                type: "string",
                description:
                  "This is the color that the user chooses, it could be in hex code or color name e.g blue, #fff etc.",
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
