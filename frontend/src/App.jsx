import { useState } from "react";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    setLoading(true);
    setAnswer("");

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await response.json();
      setAnswer(data.answer);
    } catch (error) {
      setAnswer("Fehler: Backend nicht erreichbar.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: "600px",
        margin: "40px auto",
        fontFamily: "sans-serif",
      }}
    >
      <h1>Health/Fitness QA-Bot</h1>

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
          }}
        >
          {answer}
        </div>
      )}
    </div>
  );
}

export default App;
