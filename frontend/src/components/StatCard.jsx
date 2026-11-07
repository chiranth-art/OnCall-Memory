
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Brain
} from "lucide-react";

const icons = {
  alert: AlertTriangle,
  success: CheckCircle2,
  clock: Clock,
  memory: Brain
};

export default function StatCard({
  title,
  value,
  description,
  type
}) {
  const Icon = icons[type] || Brain;

  return (
    <div className="stat-card">

      <div className="stat-card-top">
        <span>{title}</span>

        <div className={`stat-icon ${type}`}>
          <Icon size={21} />
        </div>
      </div>

      <h2>{value}</h2>

      <p>{description}</p>

    </div>
  );
}
