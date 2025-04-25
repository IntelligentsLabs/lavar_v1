import React from "react";

const AssistantSpeechIndicator = ({ isSpeaking }) => {
  return (
    <div style={{ display: "flex", alignItems: "center", marginBottom: "10px" }}>
      <div
        style={{
          width: "2px",
          height: "2px",
          backgroundColor: isSpeaking ? "#3ef07c" : "#f03e3e",
          marginRight: "1px",
          borderRadius: "4px",
        }}
      />
      <p style={{ color: "white", margin: 0 }}>
        {isSpeaking ? "Assistant speaking" : "Assistant not speaking"}
      </p>
    </div>
  );
};

export default AssistantSpeechIndicator;
