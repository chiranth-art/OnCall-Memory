
import { useState } from "react";

import {
  BrainCircuit,
  Sparkles,
  Search,
  CheckCircle2,
  XCircle,
  Database,
  RefreshCw
} from "lucide-react";

import {
  getLearnedPatterns
} from "../services/api";

export default function MemoryInsights() {
  const [question, setQuestion] = useState(
    "What successful solutions have worked for database connection timeout incidents?"
  );

  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [error, setError] = useState("");

  const handleReflect = async () => {
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    setLoading(true);
    setAnswer("");
    setError("");
    setDemoMode(false);

    try {
      const data = await getLearnedPatterns(question);

      setAnswer(
        typeof data === "string"
          ? data
          : data.answer || data.patterns || data.text || JSON.stringify(data, null, 2)
      );

    } catch {
      setError(
        "Backend unavailable. You can load the sample insights below."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadDemo = () => {
    setAnswer(
      "Based on the illustrative historical incident records:\n\n" +
      "1. Database connection pool exhaustion was associated with sudden traffic spikes.\n\n" +
      "2. Increasing the pool size helped in the recorded payment-service incident, after checking database capacity.\n\n" +
      "3. Restarting the payment service alone did not provide a lasting solution.\n\n" +
      "4. Redis memory exhaustion was addressed through increased memory allocation and cache expiration.\n\n" +
      "5. Troubleshooting should identify the actual bottleneck before restarting services."
    );

    setDemoMode(true);
    setError("");
  };

  const quickQuestions = [
    "What fixed database connection timeouts before?",
    "Which troubleshooting attempts failed?",
    "Compare payment and authentication incidents.",
    "What are the most common historical root causes?"
  ];

  return (
    <div className="memory-page">

      <div className="page-intro">
        <div>
          <span className="section-eyebrow">
            <BrainCircuit size={15} />
            HINDSIGHT MEMORY ENGINE
          </span>

          <h2>Memory & Learning Insights</h2>

          <p>
            Explore historical knowledge and discover
            patterns from previous production incidents.
          </p>
        </div>
      </div>

      <div className="memory-hero">

        <div className="memory-hero-icon">
          <BrainCircuit size={35} />
        </div>

        <div>
          <span>INCIDENT INTELLIGENCE</span>

          <h3>Every incident becomes organizational knowledge.</h3>

          <p>
            IncidentIQ uses persistent memory to recall
            previous failures, successful fixes and
            troubleshooting patterns.
          </p>
        </div>

      </div>

      <div className="memory-info-grid">

        <div className="memory-info-card">
          <Database size={22} />
          <span>Memory technology</span>
          <strong>Hindsight</strong>
        </div>

        <div className="memory-info-card">
          <CheckCircle2 size={22} />
          <span>Learning from</span>
          <strong>Successful fixes</strong>
        </div>

        <div className="memory-info-card">
          <XCircle size={22} />
          <span>Also remembers</span>
          <strong>Failed fixes</strong>
        </div>

      </div>

      <div className="reflection-card">

        <div className="reflection-heading">
          <div>
            <h3>
              <Sparkles size={19} />
              Ask IncidentIQ
            </h3>

            <p>
              Ask questions about previous incidents
              and their outcomes.
            </p>
          </div>
        </div>

        <div className="form-group">
          <label>Your question</label>

          <textarea
            rows="3"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
        </div>

        <div className="reflection-actions">

          <button
            className="primary-btn"
            onClick={handleReflect}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                Reflecting...
              </>
            ) : (
              <>
                <Search size={17} />
                Discover Patterns
              </>
            )}
          </button>

          <button
            className="secondary-btn"
            onClick={loadDemo}
          >
            Load Sample Insight
          </button>

        </div>

        {error && (
          <div className="api-message">
            {error}
          </div>
        )}

        {answer && (
          <div className="reflection-result">

            <div className="reflection-result-heading">
              <BrainCircuit size={20} />

              <strong>
                {demoMode ? "Sample Memory Insights" : "Hindsight Reflection"}
              </strong>

              <span className="result-mode">
                {demoMode ? "DEMO" : "LIVE"}
              </span>
            </div>

            <div className="reflection-answer">
              {answer}
            </div>

          </div>
        )}

      </div>

      <div className="quick-questions">

        <h3>Suggested questions</h3>

        <div className="question-list">
          {quickQuestions.map((item, index) => (
            <button
              key={index}
              onClick={() => {
                setQuestion(item);
                setAnswer("");
                setError("");
                setDemoMode(false);
              }}
            >
              <Sparkles size={15} />
              {item}
            </button>
          ))}
        </div>

      </div>

    </div>
  );
}
