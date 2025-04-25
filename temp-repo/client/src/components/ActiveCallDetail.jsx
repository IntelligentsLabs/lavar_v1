import AssistantSpeechIndicator from "./call/AssistantSpeechIndicator";
import Button from "./base/Button";
import VolumeLevel from "./call/VolumeLevel";

const ActiveCallDetail = ({ assistantIsSpeaking, volumeLevel, onEndCallClick }) => {
  return (
    <div>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "1px",
          border: "1px solid #ddd",
          borderRadius: "2px",
          boxShadow: "0px 4px 8px rgba(0,0,0,0.1)",
          width: "10px",
          height: "10px",
        }}
      >
        <AssistantSpeechIndicator isSpeaking={assistantIsSpeaking} />
        <VolumeLevel volume={volumeLevel} />
      </div>
      <div style={{ marginTop: "2px", textAlign: "center" }}>
        <Button label="End Call" onClick={onEndCallClick} />
      </div>
    </div>
  );
};

export default ActiveCallDetail;
