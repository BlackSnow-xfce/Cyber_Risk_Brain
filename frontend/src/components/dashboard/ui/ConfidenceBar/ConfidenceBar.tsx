import "./ConfidenceBar.css";

interface ConfidenceBarProps {
    value: number;
}

export default function ConfidenceBar({
    value,
}: ConfidenceBarProps) {
    const percentage = Math.max(0, Math.min(100, value));

    return (
        <div className="confidence-bar">
            <div className="confidence-bar__header">
                <span>Confidence</span>

                <strong>{percentage}%</strong>
            </div>

            <div className="confidence-bar__track">
                <div
                    className="confidence-bar__fill"
                    style={{
                        width: `${percentage}%`,
                    }}
                />
            </div>
        </div>
    );
}