import ScaleLoader from "react-spinners/ScaleLoader";

const Button = ({onClick, isLoading, disabled, onEndCall }) => {
  const opacity = disabled ? 0.75 : 1;
  const cursor = disabled ? "not-allowed" : "pointer";

  const Contents = isLoading ? (
    <ScaleLoader
      color="#fff"
      height={8}
      width={2}
      margin={0.5}
      loading={true}
      size={10}
      css={{ display: "block", margin: "0 auto" }}
    />
  ) : (
    <p style={{ margin: 0, padding: 0 }}>
      <span className="material-icons-outlined text-white-500 cursor-pointer">
        mic
      </span>
    </p>
  );

  return (
    <button
      onClick={() => {
        Contents.type !== 'p' ? onEndCall() :
        onClick()
      }
      }
      // disabled={disabled}
      style={{ opacity, cursor }}
      className="bg-gradient-to-r from-blue-500 to-blue-700 text-white px-4 py-2 rounded-full shadow-lg flex items-center justify-center space-x-2 transition-all duration-300 transform hover:scale-105 disabled:opacity-75 disabled:cursor-not-allowed"
    >
      {Contents}
    </button>
  );
};

export default Button;
