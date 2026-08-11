import { useState } from "react";

// Generiert eine einfache, zufällige ID -- reicht für unseren Zweck völlig
function generateThreadId() {
  return "thread-" + Math.random().toString(36).substring(2, 15);
}

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  // useState mit einer Funktion als Startwert: wird nur EINMAL beim ersten Rendern ausgeführt,
  // nicht bei jedem Neu-Rendern -- genau das, was wir wollen (eine ID pro Sitzung)
  const [threadId, setThreadId] = useState(() => generateThreadId());

  const handleAsk = async () => {
    setLoading(true);
    setAnswer("");

    try {
      const response = await fetch(
        "https://health-fitness-qa-bot-backend.onrender.com/ask",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, thread_id: threadId }),
        },
      );
      const data = await response.json();
      setAnswer(data.answer);
    } catch (error) {
      setAnswer("Fehler: Backend nicht erreichbar.");
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setThreadId(generateThreadId());
    setQuestion("");
    setAnswer("");
  };

  return (
    <div
      style={{
        maxWidth: "600px",
        margin: "40px auto",
        fontFamily: "sans-serif",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h1>Health/Fitness QA-Bot</h1>
        <button onClick={handleNewChat} style={{ height: "36px" }}>
          Neuer Chat
        </button>
      </div>

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Stell eine Frage zum Video..."
        rows={3}
        style={{ width: "100%", padding: "8px" }}
      />

      <button
        onClick={handleAsk}
        disabled={loading || !question}
        style={{ marginTop: "8px" }}
      >
        {loading ? "Frage wird beantwortet..." : "Senden"}
      </button>

      {answer && (
        <div
          style={{
            marginTop: "20px",
            padding: "12px",
            background: "#f0f0f0",
            borderRadius: "8px",
            whiteSpace: "pre-wrap",
          }}
        >
          {answer}
        </div>
      )}
    </div>
  );
}

export default App;
