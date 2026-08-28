import { UserRound } from "lucide-react";

export default function UserMenu() {
    return <div className="operator" aria-label="Operator unavailable"><span className="operator-avatar"><UserRound size={13} /></span><span className="operator-copy"><strong>Operator unavailable</strong><small>Session identity not configured</small></span></div>;
}
